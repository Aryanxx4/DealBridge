"""Admin ticket workflow (§9.5). All transitions are enforced here; invalid ones return 409 INVALID_STATE."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, HttpUrl, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import AuditAction, TicketStatus
from app.core.errors import AppError, invalid_state, not_found
from app.core.identity import require_role
from app.db.session import get_db
from app.models.chat import Ticket, TicketOccurrence
from app.models.identity import User
from app.models.knowledge import KnowledgeRecord
from app.services.audit import audit
from app.services.knowledge.publish import publish_ticket

router = APIRouter(prefix="/admin/tickets", tags=["admin-tickets"])
admin_only = require_role("ADMIN")

S = TicketStatus
TRANSITIONS: dict[str, dict[str, str]] = {
    S.OPEN: {"start-review": S.IN_REVIEW, "close": S.CLOSED},
    S.IN_REVIEW: {"answer": S.ANSWER_PROPOSED, "reject": S.REJECTED, "close": S.CLOSED},
    S.ANSWER_PROPOSED: {"approve": S.APPROVED, "request-revision": S.IN_REVIEW, "reject": S.REJECTED, "close": S.CLOSED},
    S.APPROVED: {"publish": S.PUBLISHED, "close": S.CLOSED},
    S.REJECTED: {"reopen": S.IN_REVIEW, "close": S.CLOSED},
    S.PUBLISHED: {},
    S.CLOSED: {},
}
CATEGORIES = ["deployment", "architecture", "security", "platform", "integrations", "concepts", "OTHER"]


def _guard(t: Ticket, action: str) -> None:
    allowed = TRANSITIONS[S(t.status)]
    if action not in allowed:
        raise invalid_state(f"Cannot {action.replace('-', ' ')} a ticket in status {t.status}.", list(allowed))


def _get(db: Session, ticket_id: uuid.UUID) -> Ticket:
    t = db.get(Ticket, ticket_id)
    if t is None:
        raise not_found("Ticket")
    return t


def _name(db: Session, uid) -> str | None:
    u = db.get(User, uid) if uid else None
    return u.display_name if u else None


def ticket_summary(db: Session, t: Ticket) -> dict:
    return {
        "id": str(t.id),
        "display_id": t.display_id,
        "normalised_question": t.normalised_question,
        "category": t.category,
        "status": t.status,
        "priority": t.priority,
        "reason": t.reason,
        "occurrence_count": t.occurrence_count,
        "created_at": t.created_at,
        "updated_at": t.updated_at,
        "assigned_to": _name(db, t.assigned_to),
    }


def ticket_detail(db: Session, t: Ticket) -> dict:
    occ = db.scalars(select(TicketOccurrence).where(TicketOccurrence.ticket_id == t.id).order_by(TicketOccurrence.created_at)).all()
    rec = db.get(KnowledgeRecord, t.published_knowledge_id) if t.published_knowledge_id else None
    return ticket_summary(db, t) | {
        "original_question": t.original_question,
        "context_excerpt": t.context_excerpt,
        "retrieval_trace": t.retrieval_trace,
        "related_knowledge_ids": t.related_knowledge_ids,
        "linked_to_assessment": t.assessment_id is not None,
        "occurrences": [{"user": _name(db, o.user_id), "question_text": o.question_text, "created_at": o.created_at} for o in occ],
        "created_by": _name(db, t.created_by),
        "proposed_answer": t.proposed_answer,
        "proposed_by": _name(db, t.proposed_by),
        "proposed_by_id": str(t.proposed_by) if t.proposed_by else None,
        "proposed_at": t.proposed_at,
        "supporting_sources": t.supporting_sources,
        "internal_notes": t.internal_notes,
        "reviewed_by": _name(db, t.reviewed_by),
        "reviewer_note": t.reviewer_note,
        "reviewed_at": t.reviewed_at,
        "resolved_at": t.resolved_at,
        "publish_error": t.publish_error,
        "published_knowledge_id": str(t.published_knowledge_id) if t.published_knowledge_id else None,
        "published_version": rec.version if rec else None,
        "close_reason": t.close_reason,
        "allowed_actions": list(TRANSITIONS[S(t.status)]),
        "allow_self_approval": get_settings().ALLOW_SELF_APPROVAL,
    }


@router.get("")
def list_tickets(
    status: str | None = None,
    category: str | None = None,
    limit: int = 50,
    offset: int = 0,
    _: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    q = select(Ticket)
    if status:
        q = q.where(Ticket.status.in_(status.split(",")))
    if category:
        q = q.where(Ticket.category == category)
    q = q.order_by(Ticket.occurrence_count.desc(), Ticket.created_at.asc()).limit(max(1, min(limit, 200))).offset(offset)
    return [ticket_summary(db, t) for t in db.scalars(q)]


@router.get("/{ticket_id}")
def get_ticket(ticket_id: uuid.UUID, _: User = Depends(admin_only), db: Session = Depends(get_db)):
    return ticket_detail(db, _get(db, ticket_id))


@router.post("/{ticket_id}/start-review")
def start_review(ticket_id: uuid.UUID, user: User = Depends(admin_only), db: Session = Depends(get_db)):
    t = _get(db, ticket_id)
    _guard(t, "start-review")
    t.status, t.assigned_to = S.IN_REVIEW.value, user.id
    db.commit()
    return ticket_detail(db, t)


class Source(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    url: HttpUrl | None = None
    note: str | None = Field(default=None, max_length=500)


class AnswerIn(BaseModel):
    normalised_question: str = Field(min_length=5, max_length=1000)
    category: str = "OTHER"
    answer: str = Field(min_length=40, max_length=8000)
    supporting_sources: list[Source] = Field(default_factory=list, max_length=10)
    internal_notes: str | None = Field(default=None, max_length=4000)
    privacy_confirmed: bool

    @field_validator("category")
    @classmethod
    def _cat(cls, v: str) -> str:
        if v not in CATEGORIES:
            raise ValueError(f"category must be one of {CATEGORIES}")
        return v


@router.post("/{ticket_id}/answer")
def submit_answer(ticket_id: uuid.UUID, body: AnswerIn, user: User = Depends(admin_only), db: Session = Depends(get_db)):
    t = _get(db, ticket_id)
    _guard(t, "answer")
    if not body.privacy_confirmed:
        raise AppError("VALIDATION_ERROR", "Confirm that the answer contains no buyer-private or customer-specific information.", 422)
    t.normalised_question = body.normalised_question.strip()
    t.category = body.category
    t.proposed_answer = body.answer.strip()
    t.supporting_sources = [{"title": s.title, "url": str(s.url) if s.url else None, "note": s.note} for s in body.supporting_sources]
    t.internal_notes = body.internal_notes
    t.proposed_by, t.proposed_at = user.id, datetime.now(UTC)
    t.status = S.ANSWER_PROPOSED.value
    audit(db, AuditAction.TICKET_PROPOSED, "ticket", t.id, user, {"display_id": t.display_id})
    db.commit()
    return ticket_detail(db, t)


@router.post("/{ticket_id}/approve")
def approve(ticket_id: uuid.UUID, user: User = Depends(admin_only), db: Session = Depends(get_db)):
    t = _get(db, ticket_id)
    _guard(t, "approve")
    if t.proposed_by == user.id and not get_settings().ALLOW_SELF_APPROVAL:
        raise AppError("SELF_APPROVAL_NOT_ALLOWED", "The approver must be a different person from the proposer.", 403)
    t.status, t.reviewed_by, t.reviewed_at = S.APPROVED.value, user.id, datetime.now(UTC)
    audit(db, AuditAction.TICKET_APPROVED, "ticket", t.id, user, {"display_id": t.display_id})
    db.commit()
    publish_ticket(db, t, user)  # raises 502 PUBLISH_INDEX_FAILED (ticket stays APPROVED) on index failure
    db.refresh(t)
    return ticket_detail(db, t)


@router.post("/{ticket_id}/publish")
def publish(ticket_id: uuid.UUID, user: User = Depends(admin_only), db: Session = Depends(get_db)):
    """Retry publishing an APPROVED ticket. Safe to call repeatedly."""
    t = _get(db, ticket_id)
    if t.status == S.PUBLISHED.value:
        return ticket_detail(db, t)
    _guard(t, "publish")
    publish_ticket(db, t, db.get(User, t.reviewed_by) or user)
    db.refresh(t)
    return ticket_detail(db, t)


class NoteIn(BaseModel):
    reviewer_note: str = Field(min_length=3, max_length=2000)


@router.post("/{ticket_id}/request-revision")
def request_revision(ticket_id: uuid.UUID, body: NoteIn, user: User = Depends(admin_only), db: Session = Depends(get_db)):
    t = _get(db, ticket_id)
    _guard(t, "request-revision")
    t.status, t.reviewer_note, t.reviewed_by, t.reviewed_at = S.IN_REVIEW.value, body.reviewer_note, user.id, datetime.now(UTC)
    db.commit()
    return ticket_detail(db, t)


@router.post("/{ticket_id}/reject")
def reject(ticket_id: uuid.UUID, body: NoteIn, user: User = Depends(admin_only), db: Session = Depends(get_db)):
    t = _get(db, ticket_id)
    _guard(t, "reject")
    t.status, t.reviewer_note, t.reviewed_by, t.reviewed_at = S.REJECTED.value, body.reviewer_note, user.id, datetime.now(UTC)
    audit(db, AuditAction.TICKET_REJECTED, "ticket", t.id, user, {"display_id": t.display_id})
    db.commit()
    return ticket_detail(db, t)


@router.post("/{ticket_id}/reopen")
def reopen(ticket_id: uuid.UUID, user: User = Depends(admin_only), db: Session = Depends(get_db)):
    t = _get(db, ticket_id)
    _guard(t, "reopen")
    t.status, t.assigned_to = S.IN_REVIEW.value, user.id
    db.commit()
    return ticket_detail(db, t)


class CloseIn(BaseModel):
    reason: Literal["DUPLICATE", "OUT_OF_SCOPE", "NOT_A_PRODUCT_QUESTION", "OTHER"]
    duplicate_of: uuid.UUID | None = None
    note: str | None = Field(default=None, max_length=2000)


@router.post("/{ticket_id}/close")
def close(ticket_id: uuid.UUID, body: CloseIn, user: User = Depends(admin_only), db: Session = Depends(get_db)):
    t = _get(db, ticket_id)
    _guard(t, "close")
    if body.duplicate_of is not None and db.get(Ticket, body.duplicate_of) is None:
        raise not_found("Duplicate-of ticket")
    t.status, t.close_reason, t.duplicate_of, t.resolved_at = S.CLOSED.value, body.reason, body.duplicate_of, datetime.now(UTC)
    if body.note:
        t.reviewer_note = body.note
    audit(db, AuditAction.TICKET_CLOSED, "ticket", t.id, user, {"reason": body.reason})
    db.commit()
    return ticket_detail(db, t)
