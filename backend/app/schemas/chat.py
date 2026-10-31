from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.services.retrieval.evidence import strip_scores


class SessionCreate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    assessment_id: uuid.UUID | None = None
    requirement_id: uuid.UUID | None = None


class SessionOut(BaseModel):
    id: uuid.UUID
    title: str
    assessment_id: uuid.UUID | None
    requirement_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, c) -> SessionOut:
        return cls(
            id=c.id,
            title=c.title,
            assessment_id=c.assessment_id,
            requirement_id=c.requirement_id,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class TicketRef(BaseModel):
    id: uuid.UUID
    display_id: str
    status: str
    linked: bool = False


class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    answer_type: str | None
    citations: list[dict]
    general_explanation_markdown: str | None = None
    unverified_aspects: list[str] = []
    conflict_note: str | None = None
    action: dict | None = None
    ticket: TicketRef | None = None
    created_at: datetime

    @classmethod
    def of(cls, m, ticket=None, linked: bool = False, include_scores: bool = False) -> MessageOut:
        st = m.structured or {}
        return cls(
            id=m.id,
            role=m.role,
            content=m.content,
            answer_type=m.answer_type,
            citations=m.citations if include_scores else strip_scores(m.citations or []),
            general_explanation_markdown=st.get("general_explanation_markdown"),
            unverified_aspects=st.get("unverified_aspects") or [],
            conflict_note=st.get("conflict_note"),
            action=st.get("action"),
            ticket=TicketRef(
                id=ticket.id, display_id=ticket.display_id, status=ticket.status, linked=linked or bool(st.get("ticket_linked"))
            )
            if ticket
            else None,
            created_at=m.created_at,
        )


class SessionDetail(SessionOut):
    messages: list[MessageOut]
    privacy_notice: str


class SendResult(BaseModel):
    user_message: MessageOut
    assistant_message: MessageOut
