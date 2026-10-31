"""Conversations, messages and unanswered-question tickets."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import REAL, DateTime, ForeignKey, Integer, Sequence, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import AnswerType, TicketPriority, TicketReason, TicketStatus, values
from app.db.base import Base, CreatedOnlyMixin, TimestampMixin, enum_check

ticket_seq = Sequence("ticket_display_seq")


class Conversation(TimestampMixin, Base):
    __tablename__ = "conversations"
    __table_args__ = (enum_check("kind", ["PRODUCT_CHAT", "REQUIREMENT_INTAKE"]),)

    owner_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    assessment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    requirement_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, default="New chat")


class Message(TimestampMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (enum_check("role", ["USER", "ASSISTANT"]), enum_check("answer_type", values(AnswerType)))

    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    answer_type: Mapped[str | None] = mapped_column(String(30))
    citations: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    ticket_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id"), index=True)
    retrieval_trace: Mapped[dict | None] = mapped_column(JSONB)
    structured: Mapped[dict | None] = mapped_column(JSONB)
    model: Mapped[str | None] = mapped_column(String(100))
    prompt_versions: Mapped[dict | None] = mapped_column(JSONB)


class Ticket(TimestampMixin, Base):
    __tablename__ = "tickets"
    __table_args__ = (
        enum_check("status", values(TicketStatus)),
        enum_check("priority", values(TicketPriority)),
        enum_check("reason", values(TicketReason)),
    )

    display_id: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    original_question: Mapped[str] = mapped_column(Text, nullable=False)
    normalised_question: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="OTHER")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default=TicketStatus.OPEN.value, index=True)
    priority: Mapped[str] = mapped_column(String(10), nullable=False, default=TicketPriority.MEDIUM.value)
    occurrence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    reason: Mapped[str] = mapped_column(String(30), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id"), index=True)
    message_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    assessment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    requirement_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    context_excerpt: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    question_embedding: Mapped[list[float] | None] = mapped_column(ARRAY(REAL))
    retrieval_trace: Mapped[dict | None] = mapped_column(JSONB)
    related_knowledge_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    proposed_answer: Mapped[str | None] = mapped_column(Text)
    proposed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    proposed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    supporting_sources: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    internal_notes: Mapped[str | None] = mapped_column(Text)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    reviewer_note: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_knowledge_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    publish_error: Mapped[str | None] = mapped_column(Text)
    close_reason: Mapped[str | None] = mapped_column(String(40))
    duplicate_of: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))


class TicketOccurrence(CreatedOnlyMixin, Base):
    __tablename__ = "ticket_occurrences"

    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id"), index=True)
    message_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
