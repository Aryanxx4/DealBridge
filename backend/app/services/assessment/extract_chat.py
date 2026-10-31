"""Requirement intake chat and change proposals (§10.5). Every proposal needs an explicit Apply."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import RequirementSource
from app.core.errors import AppError, invalid_state, not_found
from app.models.assessment import Assessment, ChangeProposal, Requirement
from app.models.chat import Conversation, Message
from app.prompts import intake_chat as P
from app.services.assessment import requirement_service as RS
from app.services.llm.client import get_llm


def intake_conversation(db: Session, a: Assessment, user, create: bool = True) -> Conversation | None:
    c = db.scalar(select(Conversation).where(Conversation.assessment_id == a.id, Conversation.kind == "REQUIREMENT_INTAKE"))
    if c is None and create:
        c = Conversation(owner_user_id=user.id, kind="REQUIREMENT_INTAKE", assessment_id=a.id, title="Requirement intake")
        db.add(c)
        db.flush()
    return c


def _snapshot(r: Requirement) -> dict:
    return {
        "display_id": r.display_id,
        "normalized_text": r.normalized_text,
        "category": r.category,
        "priority": r.priority,
        "is_removed": r.is_removed,
    }


def send(db: Session, a: Assessment, user, content: str) -> tuple[Message, Message, ChangeProposal | None]:
    c = intake_conversation(db, a, user)
    reqs = db.scalars(
        select(Requirement).where(Requirement.assessment_id == a.id, Requirement.is_removed.is_(False)).order_by(Requirement.seq)
    ).all()
    history = [
        {"role": m.role, "content": m.content}
        for m in db.scalars(select(Message).where(Message.conversation_id == c.id).order_by(Message.created_at.desc()).limit(10)).all()[
            ::-1
        ]
    ]
    um = Message(conversation_id=c.id, role="USER", content=content, citations=[])
    db.add(um)
    db.commit()
    turn = get_llm().complete_structured(
        "main",
        P.SYSTEM,
        P.build_messages(
            [
                {
                    "display_id": r.display_id,
                    "normalized_text": r.normalized_text,
                    "category": r.category,
                    "priority": r.priority,
                    "buyer_confirmed": r.buyer_confirmed,
                }
                for r in reqs
            ],
            history,
            content,
        ),
        P.IntakeTurn,
        P.TOOL,
        1500,
        0.0,
    )
    by_id = {r.display_id: r for r in reqs}
    ops = []
    for op in turn.proposed_ops:
        d = op.model_dump()
        if op.op in ("UPDATE", "REMOVE"):
            target = by_id.get((op.target_display_id or "").upper())
            if target is None:
                continue  # never touch an unidentified requirement
            d["target_display_id"] = target.display_id
            d["target_snapshot"] = _snapshot(target)
        elif not (op.normalized_text and 5 <= len(op.normalized_text.strip()) <= 1000):
            continue
        ops.append(d)
    am = Message(
        conversation_id=c.id,
        role="ASSISTANT",
        content=turn.assistant_message,
        citations=[],
        structured={
            "clarifying_questions": turn.clarifying_questions[:3],
            "assumptions_noted": turn.assumptions_noted,
            "is_ambiguous": turn.is_ambiguous,
        },
        model=None,
        prompt_versions={"intake_chat": P.PROMPT_VERSION},
    )
    db.add(am)
    db.flush()
    proposal = None
    if ops:
        proposal = ChangeProposal(assessment_id=a.id, message_id=am.id, ops=ops, status="PENDING")
        db.add(proposal)
    db.commit()
    return um, am, proposal


def apply(db: Session, a: Assessment, proposal_id, user, selected: list[int] | None) -> dict:
    p = db.get(ChangeProposal, proposal_id)
    if p is None or p.assessment_id != a.id:
        raise not_found("Change proposal")
    if p.status != "PENDING":
        raise invalid_state(f"This proposal is already {p.status.lower()}.")
    idx = list(range(len(p.ops))) if selected is None else sorted(set(selected))
    if any(i < 0 or i >= len(p.ops) for i in idx) or not idx:
        raise AppError("VALIDATION_ERROR", "Select at least one valid operation.", 422)
    reqs = {r.display_id: r for r in db.scalars(select(Requirement).where(Requirement.assessment_id == a.id))}
    # Staleness check before any change: targets must still exist and be unchanged since the proposal.
    for i in idx:
        op = p.ops[i]
        if op["op"] in ("UPDATE", "REMOVE"):
            r = reqs.get(op["target_display_id"])
            snap = op.get("target_snapshot") or {}
            if r is None or r.is_removed or r.normalized_text != snap.get("normalized_text"):
                raise AppError(
                    "STALE_PROPOSAL", f"{op['target_display_id']} changed after this proposal was made. Ask again in the chat.", 409
                )
    actor = RS.Actor(user, "CHAT")
    changed = []
    for i in idx:
        op = p.ops[i]
        if op["op"] == "ADD":
            r = RS.create(
                db,
                a,
                actor,
                original_text=op.get("source_quote") or op["normalized_text"],
                normalized_text=op["normalized_text"],
                category=op.get("category") or "OTHER",
                priority=op.get("priority") or "NOT_SPECIFIED",
                priority_basis=op.get("priority_basis"),
                source_type=RequirementSource.CHAT.value,
                source_reference={
                    "conversation_id": str(intake_conversation(db, a, user).id),
                    "message_id": str(p.message_id),
                    "quote": op.get("source_quote"),
                },
                buyer_confirmed=True,
            )
            changed.append({"op": "ADD", "display_id": r.display_id, "text": r.normalized_text})
        elif op["op"] == "UPDATE":
            r = reqs[op["target_display_id"]]
            RS.edit(db, a, r.id, actor, normalized_text=op.get("normalized_text"), category=op.get("category"), priority=op.get("priority"))
            changed.append({"op": "UPDATE", "display_id": r.display_id, "text": r.normalized_text})
        else:
            r = reqs[op["target_display_id"]]
            RS.remove(db, a, r.id, actor, reason="removed via requirement chat")
            changed.append({"op": "REMOVE", "display_id": r.display_id, "text": r.normalized_text})
    p.status, p.resolved_at, p.applied_op_indexes = "APPLIED", datetime.now(UTC), idx
    p.result = {"changed": changed, "assessment_status": a.status}
    db.commit()
    return p.result


def dismiss(db: Session, a: Assessment, proposal_id) -> ChangeProposal:
    p = db.get(ChangeProposal, proposal_id)
    if p is None or p.assessment_id != a.id:
        raise not_found("Change proposal")
    if p.status != "PENDING":
        raise invalid_state(f"This proposal is already {p.status.lower()}.")
    p.status, p.resolved_at = "DISMISSED", datetime.now(UTC)
    db.commit()
    return p
