"""Demo identities: organisations and users (no passwords, sessions or tokens)."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import OrgKind, UserRole, values
from app.db.base import Base, TimestampMixin, enum_check


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"
    __table_args__ = (enum_check("kind", values(OrgKind)),)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (enum_check("role", values(UserRole)),)

    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )

    organization: Mapped[Organization] = relationship(lazy="joined")
