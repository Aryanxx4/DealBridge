"""Assessments, uploaded documents, requirements, revisions and chat change proposals."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import AssessmentStatus, Priority, RequirementCategory, RequirementSource, values
from app.db.base import Base, CreatedOnlyMixin, TimestampMixin, enum_check


class Assessment(TimestampMixin, Base):
    __tablename__ = "assessments"
    __table_args__ = (enum_check("status", values(AssessmentStatus)),)

    owner_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=AssessmentStatus.DRAFT.value)
    context: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    intake_form: Mapped[dict | None] = mapped_column(JSONB)
    requirement_set_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_req_seq: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    latest_version_no: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class UploadedDocument(TimestampMixin, Base):
    __tablename__ = "uploaded_documents"
    __table_args__ = (
        enum_check("kind", ["BUYER_PDF", "SELLER_DOC"]),
        enum_check("extraction_status", ["OK", "SCANNED", "EMPTY", "MALFORMED"]),
    )

    assessment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("assessments.id"), index=True)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pages: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    extraction_status: Mapped[str] = mapped_column(String(20), nullable=False)
    extraction_message: Mapped[str | None] = mapped_column(Text)


class Requirement(TimestampMixin, Base):
    __tablename__ = "requirements"
    __table_args__ = (
        UniqueConstraint("assessment_id", "seq", name="uq_requirements_assessment_seq"),
        enum_check("category", values(RequirementCategory)),
        enum_check("priority", values(Priority)),
        enum_check("source_type", values(RequirementSource)),
    )

    assessment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False, index=True)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    display_id: Mapped[str] = mapped_column(String(20), nullable=False)
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default=Priority.NOT_SPECIFIED.value)
    priority_basis: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(10), nullable=False)
    source_reference: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    buyer_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    needs_clarification: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    clarifying_question: Mapped[str | None] = mapped_column(Text)
    clarification_waived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_removed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RequirementRevision(CreatedOnlyMixin, Base):
    __tablename__ = "requirement_revisions"
    __table_args__ = (
        enum_check("change_type", ["CREATED", "EDITED", "CONFIRMED", "CLARIFICATION_WAIVED", "REMOVED", "RESTORED"]),
        enum_check("origin", ["UI", "CHAT", "FORM", "PDF", "SYSTEM"]),
    )

    requirement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("requirements.id"), nullable=False, index=True)
    revision_no: Mapped[int] = mapped_column(Integer, nullable=False)
    change_type: Mapped[str] = mapped_column(String(30), nullable=False)
    changes: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    actor_role: Mapped[str | None] = mapped_column(String(20))
    origin: Mapped[str] = mapped_column(String(10), nullable=False)
    assessment_revision: Mapped[int] = mapped_column(Integer, nullable=False)


class ChangeProposal(TimestampMixin, Base):
    __tablename__ = "change_proposals"
    __table_args__ = (enum_check("status", ["PENDING", "APPLIED", "DISMISSED"]),)

    assessment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False, index=True)
    message_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("messages.id"), index=True)
    ops: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    applied_op_indexes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    result: Mapped[dict | None] = mapped_column(JSONB)
