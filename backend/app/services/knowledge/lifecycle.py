"""Resolved-knowledge lifecycle: supersede with a new version, or revoke (§9.7). Never rebuilds Qdrant wholesale."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.enums import AuditAction
from app.core.errors import invalid_state, not_found
from app.models.identity import User
from app.models.knowledge import KnowledgeRecord
from app.services.audit import audit
from app.services.knowledge.publish import create_record, index_record
from app.services.knowledge.state import bump_epoch
from app.services.vector.qdrant_store import get_store


def supersede(
    db: Session,
    record_id,
    actor: User,
    answer: str,
    question_normalised: str | None,
    category: str | None,
    supporting_references: list[dict] | None,
) -> KnowledgeRecord:
    cur = db.get(KnowledgeRecord, record_id)
    if cur is None:
        raise not_found("Knowledge record")
    if cur.validity != "ACTIVE":
        raise invalid_state("Only the active version can be superseded.", ["ACTIVE"])
    new = create_record(
        db,
        question_original=cur.question_original,
        question_normalised=(question_normalised or cur.question_normalised).strip(),
        answer=answer.strip(),
        category=category or cur.category,
        author_id=actor.id,
        approver_id=actor.id,
        ticket_id=cur.ticket_id,
        supporting_references=supporting_references if supporting_references is not None else cur.supporting_references,
        group_id=cur.knowledge_group_id,
    )
    db.commit()
    index_record(db, new, actor)
    return new


def revoke(db: Session, record_id, actor: User, reason: str) -> KnowledgeRecord:
    rec = db.get(KnowledgeRecord, record_id)
    if rec is None:
        raise not_found("Knowledge record")
    if rec.validity != "ACTIVE":
        raise invalid_state("Only an active record can be revoked.", ["ACTIVE"])
    rec.validity, rec.status_reason = "REVOKED", reason.strip()
    db.flush()
    if rec.index_status == "INDEXED":
        store = get_store()
        store.set_payload(store.resolved, [str(rec.id)], {"validity_status": "REVOKED"})  # point kept for audit, excluded by filter
    bump_epoch(db)
    audit(db, AuditAction.KNOWLEDGE_REVOKED, "knowledge_record", rec.id, actor, {"reason": reason[:300]})
    db.commit()
    return rec
