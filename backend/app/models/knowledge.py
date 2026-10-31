"""Official knowledge bookkeeping (OKF files and ingestion runs)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, enum_check

OKF_FILE_STATUSES = ["INDEXED", "SKIPPED_NOT_APPROVED", "REMOVED", "ERROR"]


class OkfFile(TimestampMixin, Base):
    __tablename__ = "okf_files"
    __table_args__ = (enum_check("status", OKF_FILE_STATUSES),)

    path: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    knowledge_id: Mapped[str | None] = mapped_column(String(200), index=True)
    title: Mapped[str | None] = mapped_column(String(300))
    category: Mapped[str | None] = mapped_column(String(50))
    source_url: Mapped[str | None] = mapped_column(Text)
    last_verified_at: Mapped[str | None] = mapped_column(String(40))
    content_hash: Mapped[str | None] = mapped_column(String(64))
    version: Mapped[int | None] = mapped_column(Integer)
    approval_status: Mapped[str | None] = mapped_column(String(20))
    chunk_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    last_ingested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)


class IngestionRun(TimestampMixin, Base):
    __tablename__ = "ingestion_runs"

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    triggered_by: Mapped[str] = mapped_column(String(100), nullable=False)
    mode: Mapped[str] = mapped_column(String(50), nullable=False)
    spec_conformance: Mapped[str] = mapped_column(String(10), nullable=False, default="OKF")
    embedding_model: Mapped[str] = mapped_column(String(200), nullable=False)
    files_scanned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    added: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unchanged: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    removed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunks_upserted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunks_deleted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    errors: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="running")


class KnowledgeRecord(TimestampMixin, Base):
    """An approved expert resolution (versioned). The Qdrant point id equals this row's id."""

    __tablename__ = "knowledge_records"
    __table_args__ = (
        enum_check("validity", ["ACTIVE", "SUPERSEDED", "REVOKED"]),
        enum_check("index_status", ["PENDING", "INDEXED", "FAILED"]),
        UniqueConstraint("knowledge_group_id", "version", name="uq_knowledge_records_group_version"),
        Index("uq_knowledge_records_one_active", "knowledge_group_id", unique=True, postgresql_where=text("validity = 'ACTIVE'")),
    )

    knowledge_group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    question_original: Mapped[str] = mapped_column(Text, nullable=False)
    question_normalised: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    author_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    approver_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ticket_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id"), index=True)
    supporting_references: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    validity: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    status_reason: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(200), nullable=False)
    index_status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
