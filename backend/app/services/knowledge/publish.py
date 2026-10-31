"""Publishing approved expert resolutions into resolved_query_knowledge (§9.6). Synchronous and idempotent.

Nothing is embedded or upserted before human approval (R4). The Qdrant point id equals the knowledge_records id,
so retrying a publish overwrites the same point instead of duplicating it.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import AuditAction, TicketStatus
from app.core.errors import AppError
from app.models.chat import Ticket
from app.models.identity import User
from app.models.knowledge import KnowledgeRecord
from app.services.audit import audit
from app.services.embeddings.embedder import get_embedder
from app.services.knowledge.state import bump_epoch
from app.services.tickets.sanitize import redact
from app.services.vector.qdrant_store import get_store

log = logging.getLogger("dealbridge.publish")


class PublishIndexFailed(AppError):
    status_code = 502
    code = "PUBLISH_INDEX_FAILED"


def _hash(question: str, answer: str) -> str:
    return hashlib.sha256(f"{question}\n{answer}".encode()).hexdigest()


def payload_for(rec: KnowledgeRecord, db: Session) -> dict:
    """Qdrant payload. Contains only the reviewed, customer-neutral question and answer and staff attribution:
    never assessment ids, requirement text, document names or buyer organisation names."""
    author = db.get(User, rec.author_user_id)
    approver = db.get(User, rec.approver_user_id)
    ticket = db.get(Ticket, rec.ticket_id) if rec.ticket_id else None
    refs = rec.supporting_references or []
    return {
        "knowledge_id": str(rec.id),
        "knowledge_group_id": str(rec.knowledge_group_id),
        "title": rec.question_normalised[:120],
        "question_normalised": rec.question_normalised,
        "question_original": rec.question_original,
        "answer": rec.answer,
        "text": f"Q: {rec.question_normalised}\nA: {rec.answer}",
        "category": rec.category,
        "tags": rec.tags or [],
        "source_type": "expert_resolution",
        "source_document": f"expert-resolution:{ticket.display_id}" if ticket else f"expert-resolution:{rec.knowledge_group_id}",
        "source_url": next((r.get("url") for r in refs if r.get("url")), None),
        "author": author.display_name if author else None,
        "approver": approver.display_name if approver else None,
        "approved_at": rec.approved_at.isoformat(),
        "version": rec.version,
        "approval_status": "approved",
        "validity_status": rec.validity,
        "related_ticket_id": ticket.display_id if ticket else None,
        "supporting_references": refs,
        "content_hash": rec.content_hash,
        "updated_at": datetime.now(UTC).isoformat(),
    }


def create_record(
    db: Session,
    *,
    question_original: str,
    question_normalised: str,
    answer: str,
    category: str,
    author_id: uuid.UUID,
    approver_id: uuid.UUID,
    ticket_id: uuid.UUID | None,
    supporting_references: list[dict],
    group_id: uuid.UUID | None = None,
) -> KnowledgeRecord:
    """Create the next version (PENDING) and supersede the previous ACTIVE version in PostgreSQL, in one transaction."""
    previous = None
    version = 1
    if group_id is not None:
        version = (db.scalar(select(func.max(KnowledgeRecord.version)).where(KnowledgeRecord.knowledge_group_id == group_id)) or 0) + 1
        previous = db.scalar(
            select(KnowledgeRecord).where(KnowledgeRecord.knowledge_group_id == group_id, KnowledgeRecord.validity == "ACTIVE")
        )
        if previous is not None:
            previous.validity = "SUPERSEDED"
            previous.status_reason = f"Superseded by version {version}"
            db.flush()
    rec = KnowledgeRecord(
        id=uuid.uuid4(),
        knowledge_group_id=group_id or uuid.uuid4(),
        version=version,
        question_original=question_original,
        question_normalised=question_normalised,
        answer=answer,
        category=category,
        tags=[category],
        author_user_id=author_id,
        approver_user_id=approver_id,
        approved_at=datetime.now(UTC),
        ticket_id=ticket_id,
        supporting_references=supporting_references,
        validity="ACTIVE",
        content_hash=_hash(question_normalised, answer),
        embedding_model=get_settings().EMBEDDING_MODEL,
        index_status="PENDING",
    )
    db.add(rec)
    db.flush()
    return rec


def index_record(db: Session, rec: KnowledgeRecord, actor: User) -> None:
    """Embed and upsert one record, then deactivate earlier versions of its group in Qdrant. Commits."""
    store = get_store()
    try:
        vector = get_embedder().embed_documents([f"{rec.question_normalised}\n{rec.answer}"])[0]
        store.upsert(store.resolved, [(str(rec.id), vector, payload_for(rec, db))])
        older = db.scalars(
            select(KnowledgeRecord).where(
                KnowledgeRecord.knowledge_group_id == rec.knowledge_group_id,
                KnowledgeRecord.id != rec.id,
                KnowledgeRecord.index_status == "INDEXED",
            )
        ).all()
        for o in older:
            store.set_payload(store.resolved, [str(o.id)], {"validity_status": o.validity})
    except AppError as exc:
        db.rollback()
        rec = db.get(KnowledgeRecord, rec.id)
        rec.index_status = "FAILED"
        if rec.ticket_id:
            t = db.get(Ticket, rec.ticket_id)
            t.publish_error = f"{exc.code}: {exc.message}"[:500]
        db.commit()
        log.warning("publish indexing failed", extra={"record": str(rec.id), "code": exc.code})
        raise PublishIndexFailed(
            message="The answer was approved but could not be indexed. Retry publishing.", details={"cause": exc.code}
        ) from exc
    now = datetime.now(UTC)
    rec.index_status, rec.indexed_at = "INDEXED", now
    if rec.ticket_id:
        t = db.get(Ticket, rec.ticket_id)
        if t.status in (TicketStatus.APPROVED.value, TicketStatus.PUBLISHED.value):
            t.status, t.published_knowledge_id, t.resolved_at, t.publish_error = TicketStatus.PUBLISHED.value, rec.id, now, None
    bump_epoch(db)
    audit(
        db,
        AuditAction.KNOWLEDGE_PUBLISHED,
        "knowledge_record",
        rec.id,
        actor,
        {"version": rec.version, "group": str(rec.knowledge_group_id)},
    )
    if rec.version > 1:
        audit(db, AuditAction.KNOWLEDGE_SUPERSEDED, "knowledge_record", rec.knowledge_group_id, actor, {"new_version": rec.version})
    db.commit()


def buyer_org_names(db: Session, ticket: Ticket) -> list[str]:
    from app.models.chat import TicketOccurrence
    from app.services.tickets.ticket_service import org_names_for_user

    names: list[str] = []
    users = {ticket.created_by} | {o.user_id for o in db.scalars(select(TicketOccurrence).where(TicketOccurrence.ticket_id == ticket.id))}
    for uid in users:
        u = db.get(User, uid)
        if u is not None:
            names += org_names_for_user(db, u, ticket.assessment_id)
    return names


def publish_ticket(db: Session, ticket: Ticket, approver: User) -> KnowledgeRecord:
    """Create (or reuse, on retry) the record for an APPROVED ticket and index it."""
    rec = db.scalar(select(KnowledgeRecord).where(KnowledgeRecord.ticket_id == ticket.id).order_by(KnowledgeRecord.version.desc()).limit(1))
    if rec is None:
        rec = create_record(
            db,
            # The raw question may name the buyer; only a redacted copy may enter global knowledge (R6).
            question_original=redact(ticket.original_question, buyer_org_names(db, ticket)),
            question_normalised=ticket.normalised_question,
            answer=ticket.proposed_answer or "",
            category=ticket.category,
            author_id=ticket.proposed_by,
            approver_id=approver.id,
            ticket_id=ticket.id,
            supporting_references=ticket.supporting_sources or [],
        )
        db.commit()
    elif rec.index_status == "INDEXED":
        return rec  # idempotent: already published
    index_record(db, rec, approver)
    return rec
