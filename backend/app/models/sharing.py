"""Explicit sharing, attributed seller responses and buyer-seller follow-up threads."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import FollowUpStatus, values
from app.db.base import Base, CreatedOnlyMixin, TimestampMixin, enum_check


class AssessmentShare(TimestampMixin, Base):
    """One row per share action. A seller org may view a version only while an unrevoked row exists for it."""

    __tablename__ = "assessment_shares"

    assessment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False, index=True)
    seller_org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assessment_versions.id"), nullable=False, index=True)
    shared_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    shared_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)


class SellerResponse(TimestampMixin, Base):
    __tablename__ = "seller_responses"
    __table_args__ = (enum_check("assertion", ["NONE", "CONFIRMS_SUPPORT", "CONFIRMS_LIMITATION", "NEEDS_INFO_FROM_BUYER"]),)

    assessment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False, index=True)
    requirement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("requirements.id"), nullable=False, index=True)
    version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assessment_versions.id"), nullable=False, index=True)
    seller_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    assertion: Mapped[str] = mapped_column(String(30), nullable=False, default="NONE")
    attachment_document_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)


class FollowUpRequest(TimestampMixin, Base):
    __tablename__ = "follow_up_requests"
    __table_args__ = (
        enum_check("status", values(FollowUpStatus)),
        enum_check("seller_decision", ["PENDING", "ACCEPTED", "REJECTED"]),
    )

    assessment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False, index=True)
    seller_org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    requested_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    related_requirement_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=FollowUpStatus.REQUESTED.value)
    seller_decision: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    decision_reason: Mapped[str | None] = mapped_column(Text)
    assigned_owner_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)


class FollowUpMessage(CreatedOnlyMixin, Base):
    """Append-only."""

    __tablename__ = "follow_up_messages"

    follow_up_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("follow_up_requests.id"), nullable=False, index=True)
    author_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    author_role: Mapped[str] = mapped_column(String(20), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    attachment_document_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
