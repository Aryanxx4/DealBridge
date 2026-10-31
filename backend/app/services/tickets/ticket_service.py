"""Creating or linking unanswered-question tickets (§9.4)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.enums import AuditAction, TicketPriority, TicketStatus
from app.models.chat import Conversation, Message, Ticket, TicketOccurrence
from app.models.identity import Organization, User
from app.services.audit import audit
from app.services.embeddings.embedder import get_embedder
from app.services.tickets.dedupe import find_duplicate
from app.services.tickets.sanitize import redact

ESCALATE_AT = 3


@dataclass
class TicketOutcome:
    ticket: Ticket
    linked: bool
    trace: dict


def org_names_for_user(db: Session, user: User, assessment_id=None) -> list[str]:
    """Names to redact: the user's organisation and the assessment's stated organisation name."""
    names = []
    org = db.get(Organization, user.organization_id)
    if org:
        names.append(org.name)
    if assessment_id:
        try:
            from app.models.assessment import Assessment  # available from G4

            a = db.get(Assessment, assessment_id)
            if a and (a.context or {}).get("organisation_name"):
                names.append(a.context["organisation_name"])
        except ImportError:
            pass
    return names


def _org_names(db: Session, user: User, conversation: Conversation | None) -> list[str]:
    return org_names_for_user(db, user, conversation.assessment_id if conversation else None)


def context_excerpt(db: Session, conversation: Conversation, orgs: list[str], upto_message: Message | None = None) -> list[dict]:
    msgs = db.scalars(
        select(Message).where(Message.conversation_id == conversation.id).order_by(Message.created_at.desc(), Message.id)
    ).all()
    if upto_message is not None:
        msgs = [m for m in msgs if m.created_at <= upto_message.created_at]
    return [{"role": m.role, "content": redact(m.content, orgs)[:500]} for m in reversed(msgs[:4])]


def next_display_id(db: Session) -> str:
    n = db.execute(text("SELECT nextval('ticket_display_seq')")).scalar_one()
    return f"TCK-{n:04d}"


def raise_ticket(
    db: Session,
    user: User,
    conversation: Conversation | None,
    message: Message | None,
    original_question: str,
    standalone_question: str,
    category: str,
    reason: str,
    retrieval_trace: dict | None,
    related_knowledge_ids: list[str] | None = None,
) -> TicketOutcome:
    """Link to a same-intent open ticket, or create a new one. Caller commits."""
    orgs = _org_names(db, user, conversation)
    normalised = redact(standalone_question or original_question, orgs).strip()
    vector = get_embedder().embed_documents([normalised])[0]
    dup, trace = find_duplicate(db, normalised, vector)
    if dup is not None:
        dup.occurrence_count += 1
        if dup.occurrence_count >= ESCALATE_AT:
            dup.priority = TicketPriority.HIGH.value
        db.add(
            TicketOccurrence(
                ticket_id=dup.id,
                user_id=user.id,
                conversation_id=conversation.id if conversation else None,
                message_id=message.id if message else None,
                question_text=redact(original_question, orgs),
            )
        )
        audit(db, AuditAction.TICKET_LINKED, "ticket", dup.id, user, {"occurrence_count": dup.occurrence_count})
        db.flush()
        return TicketOutcome(ticket=dup, linked=True, trace=trace)

    t = Ticket(
        id=uuid.uuid4(),
        display_id=next_display_id(db),
        original_question=original_question,
        normalised_question=normalised,
        category=category or "OTHER",
        status=TicketStatus.OPEN.value,
        priority=TicketPriority.MEDIUM.value,
        reason=reason,
        created_by=user.id,
        conversation_id=conversation.id if conversation else None,
        message_id=message.id if message else None,
        assessment_id=conversation.assessment_id if conversation else None,
        requirement_id=conversation.requirement_id if conversation else None,
        context_excerpt=context_excerpt(db, conversation, orgs, message) if conversation else [],
        question_embedding=vector,
        retrieval_trace=(retrieval_trace or {}) | {"duplicate_check": trace},
        related_knowledge_ids=related_knowledge_ids or [],
    )
    db.add(t)
    db.flush()
    audit(db, AuditAction.TICKET_CREATED, "ticket", t.id, user, {"reason": reason, "display_id": t.display_id})
    return TicketOutcome(ticket=t, linked=False, trace=trace)
