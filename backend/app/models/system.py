"""Jobs, audit events, knowledge epoch and vector collection bookkeeping."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import JobStatus, JobType, values
from app.db.base import Base, CreatedOnlyMixin, TimestampMixin, enum_check


class Job(TimestampMixin, Base):
    __tablename__ = "jobs"
    __table_args__ = (enum_check("type", values(JobType)), enum_check("status", values(JobStatus)))

    type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=JobStatus.QUEUED.value)
    # FK to assessments is added in the G4 migration (table created there).
    assessment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    progress_done: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    progress_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    progress_message: Mapped[str | None] = mapped_column(Text)
    result: Mapped[dict | None] = mapped_column(JSONB)
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditEvent(CreatedOnlyMixin, Base):
    __tablename__ = "audit_events"

    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    actor_role: Mapped[str | None] = mapped_column(String(20))
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(64))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)


class KnowledgeState(Base):
    """Singleton row (id = 1) whose epoch increments whenever retrievable knowledge changes."""

    __tablename__ = "knowledge_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    epoch: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class VectorCollection(TimestampMixin, Base):
    __tablename__ = "vector_collections"

    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    embedding_model: Mapped[str] = mapped_column(String(200), nullable=False)
    dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    last_reindexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
