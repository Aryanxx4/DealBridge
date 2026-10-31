from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import ratelimit
from app.core.enums import AnswerType, TicketReason
from app.core.errors import INFRA_ERRORS, AppError, invalid_state, not_found
from app.core.identity import get_current_user
from app.db.session import get_db
from app.models.chat import Conversation, Message, Ticket
from app.models.identity import User
from app.schemas.chat import MessageCreate, MessageOut, SendResult, SessionCreate, SessionDetail, SessionOut
from app.services.rag.pipeline import PRIVACY_FOOTER, answer_question
from app.services.rag.suggested import SUGGESTED_QUESTIONS
from app.services.tickets.ticket_service import raise_ticket

router = APIRouter(prefix="/chat", tags=["chat"])


def _own_session(db: Session, user: User, session_id: uuid.UUID) -> Conversation:
    c = db.get(Conversation, session_id)
    if c is None or c.owner_user_id != user.id or c.kind != "PRODUCT_CHAT":
        raise not_found("Chat session")  # 404, never 403 (does not confirm existence)
    return c


def _check_assessment_link(db: Session, user: User, assessment_id, requirement_id) -> None:
    if assessment_id is None:
        if requirement_id is not None:
            raise AppError("VALIDATION_ERROR", "requirement_id requires assessment_id.", 422)
        return
    try:
        from app.models.assessment import Assessment, Requirement
    except ImportError:
        raise AppError("VALIDATION_ERROR", "Assessments are not available yet.", 422) from None
    a = db.get(Assessment, assessment_id)
    if a is None or a.owner_user_id != user.id:
        raise not_found("Assessment")
    if requirement_id is not None:
        r = db.get(Requirement, requirement_id)
        if r is None or r.assessment_id != a.id:
            raise not_found("Requirement")


def _ticket_of(db: Session, m: Message) -> Ticket | None:
    return db.get(Ticket, m.ticket_id) if m.ticket_id else None


@router.get("/suggested-questions")
def suggested(_: User = Depends(get_current_user)):
    return {"questions": SUGGESTED_QUESTIONS}


@router.post("/sessions", response_model=SessionOut, status_code=201)
def create_session(body: SessionCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _check_assessment_link(db, user, body.assessment_id, body.requirement_id)
    c = Conversation(
        owner_user_id=user.id,
        kind="PRODUCT_CHAT",
        assessment_id=body.assessment_id,
        requirement_id=body.requirement_id,
        title=(body.title or "New chat")[:200],
    )
    db.add(c)
    db.commit()
    return SessionOut.of(c)


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(limit: int = 50, offset: int = 0, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    limit = max(1, min(limit, 200))
    rows = db.scalars(
        select(Conversation)
        .where(Conversation.owner_user_id == user.id, Conversation.kind == "PRODUCT_CHAT")
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return [SessionOut.of(c) for c in rows]


@router.get("/sessions/{session_id}", response_model=SessionDetail)
def get_session(session_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = _own_session(db, user, session_id)
    msgs = db.scalars(select(Message).where(Message.conversation_id == c.id).order_by(Message.created_at, Message.role.desc())).all()
    admin = user.role == "ADMIN"
    return SessionDetail(
        **SessionOut.of(c).model_dump(),
        messages=[MessageOut.of(m, _ticket_of(db, m), include_scores=admin) for m in msgs],
        privacy_notice=PRIVACY_FOOTER,
    )


@router.post("/sessions/{session_id}/messages", response_model=SendResult)
def send_message(session_id: uuid.UUID, body: MessageCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = _own_session(db, user, session_id)
    ratelimit.check("chat", str(user.id))
    question = body.content.strip()
    um = Message(conversation_id=c.id, role="USER", content=question, citations=[])
    db.add(um)
    if c.title == "New chat":
        c.title = question[:60] + ("…" if len(question) > 60 else "")
    db.commit()  # the user's message is kept even if a dependency fails below
    try:
        out = answer_question(db, user, c, question, um)
    except INFRA_ERRORS:
        db.rollback()
        raise
    from app.core.config import get_settings

    s = get_settings()
    out.structured["ticket_linked"] = out.ticket_linked
    am = Message(
        conversation_id=c.id,
        role="ASSISTANT",
        content=out.content,
        answer_type=str(out.answer_type),
        citations=out.citations,
        ticket_id=out.ticket.id if out.ticket else None,
        retrieval_trace=out.trace,
        structured=out.structured,
        model=s.LLM_MODEL,
        prompt_versions=out.structured.get("prompt_versions"),
    )
    db.add(am)
    db.flush()
    if out.ticket is not None and out.ticket.message_id is None:
        out.ticket.message_id = um.id
    db.commit()
    admin = user.role == "ADMIN"
    return SendResult(
        user_message=MessageOut.of(um), assistant_message=MessageOut.of(am, out.ticket, out.ticket_linked, include_scores=admin)
    )


@router.post("/messages/{message_id}/raise-ticket", response_model=MessageOut)
def raise_for_message(message_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Raise a ticket for the unverified part of a PARTIAL answer (only when the user clicks)."""
    am = db.get(Message, message_id)
    if am is None:
        raise not_found("Message")
    c = _own_session(db, user, am.conversation_id)
    if am.role != "ASSISTANT" or am.answer_type != AnswerType.PARTIAL.value:
        raise invalid_state("Only partly verified answers can be raised with the product team from here.")
    if am.ticket_id:
        return MessageOut.of(am, _ticket_of(db, am))
    um = db.scalar(
        select(Message)
        .where(Message.conversation_id == c.id, Message.role == "USER", Message.created_at <= am.created_at)
        .order_by(Message.created_at.desc())
        .limit(1)
    )
    st = am.structured or {}
    cls = st.get("classification") or {}
    unverified = st.get("unverified_aspects") or []
    standalone = (cls.get("standalone_question") or (um.content if um else "")) + (
        f" (unverified part: {'; '.join(unverified)})" if unverified else ""
    )
    out = raise_ticket(
        db,
        user,
        c,
        um,
        um.content if um else standalone,
        standalone,
        cls.get("category", "OTHER"),
        TicketReason.PARTIAL,
        am.retrieval_trace,
    )
    am.ticket_id = out.ticket.id
    am.structured = st | {"ticket_linked": out.linked}
    db.commit()
    return MessageOut.of(am, out.ticket, out.linked)


@router.get("/tickets")
def my_tickets(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Tickets the caller created or is linked to. Published tickets include the approved answer."""
    from app.models.chat import TicketOccurrence
    from app.models.knowledge import KnowledgeRecord

    linked = select(TicketOccurrence.ticket_id).where(TicketOccurrence.user_id == user.id)
    rows = db.scalars(
        select(Ticket).where((Ticket.created_by == user.id) | (Ticket.id.in_(linked))).order_by(Ticket.created_at.desc())
    ).all()
    out = []
    for t in rows:
        item = {
            "id": str(t.id),
            "display_id": t.display_id,
            "question": t.original_question if t.created_by == user.id else t.normalised_question,
            "status": t.status,
            "created_at": t.created_at,
            "occurrence_count": t.occurrence_count,
            "answer": None,
        }
        if t.status == "PUBLISHED" and t.published_knowledge_id:
            rec = db.get(KnowledgeRecord, t.published_knowledge_id)
            if rec is not None and rec.validity != "ACTIVE":
                rec = (
                    db.scalar(
                        select(KnowledgeRecord).where(
                            KnowledgeRecord.knowledge_group_id == rec.knowledge_group_id, KnowledgeRecord.validity == "ACTIVE"
                        )
                    )
                    or rec
                )
            if rec is not None and rec.validity != "REVOKED":
                item["answer"] = {
                    "text": rec.answer,
                    "label": "Expert-verified answer",
                    "approved_at": rec.approved_at,
                    "version": rec.version,
                }
        out.append(item)
    return out
