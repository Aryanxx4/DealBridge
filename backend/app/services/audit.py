"""Append-only audit trail."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.enums import AuditAction
from app.models.system import AuditEvent


def audit(
    db: Session,
    action: AuditAction | str,
    entity_type: str,
    entity_id: uuid.UUID | str | None,
    actor=None,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    """Add an audit event to the current transaction (caller commits)."""
    ev = AuditEvent(
        actor_user_id=getattr(actor, "id", None),
        actor_role=getattr(actor, "role", None) if actor is not None else "SYSTEM",
        action=str(action),
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        metadata_=metadata or {},
    )
    db.add(ev)
    return ev
