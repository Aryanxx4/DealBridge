"""Official knowledge bookkeeping (OKF files and ingestion runs)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
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
