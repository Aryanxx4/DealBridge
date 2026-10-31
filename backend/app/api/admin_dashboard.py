"""Admin dashboard: real counts from PostgreSQL and Qdrant, plus recent audit events."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.identity import require_role
from app.db.session import get_db
from app.models.chat import Ticket
from app.models.identity import User
from app.models.knowledge import KnowledgeRecord, OkfFile
from app.models.system import AuditEvent
from app.services.vector.qdrant_store import get_store

router = APIRouter(prefix="/admin", tags=["admin"])
admin_only = require_role("ADMIN")


@router.get("/dashboard")
def dashboard(_: User = Depends(admin_only), db: Session = Depends(get_db)):
    by_status = dict(db.execute(select(Ticket.status, func.count()).group_by(Ticket.status)).all())
    store = get_store()
    try:
        official_points, resolved_points = store.count(store.official), store.count(store.resolved)
    except AppError:
        official_points = resolved_points = None
    return {
        "tickets": {
            "open": by_status.get("OPEN", 0),
            "in_review": by_status.get("IN_REVIEW", 0),
            "awaiting_approval": by_status.get("ANSWER_PROPOSED", 0),
            "approved_unpublished": by_status.get("APPROVED", 0),
            "published": by_status.get("PUBLISHED", 0),
            "rejected": by_status.get("REJECTED", 0),
            "closed": by_status.get("CLOSED", 0),
        },
        "published_knowledge_records": db.scalar(
            select(func.count(KnowledgeRecord.id)).where(KnowledgeRecord.validity == "ACTIVE", KnowledgeRecord.index_status == "INDEXED")
        ),
        "official_files_indexed": db.scalar(select(func.count(OkfFile.id)).where(OkfFile.status == "INDEXED")),
        "official_chunks": official_points,
        "resolved_points": resolved_points,
    }


@router.get("/audit")
def audit_feed(limit: int = 50, offset: int = 0, _: User = Depends(admin_only), db: Session = Depends(get_db)):
    rows = db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(max(1, min(limit, 200))).offset(offset)).all()
    names = {u.id: u.display_name for u in db.scalars(select(User))}
    return [
        {
            "id": str(e.id),
            "action": e.action,
            "entity_type": e.entity_type,
            "entity_id": e.entity_id,
            "actor": names.get(e.actor_user_id, e.actor_role),
            "actor_role": e.actor_role,
            "created_at": e.created_at,
        }
        for e in rows
    ]
