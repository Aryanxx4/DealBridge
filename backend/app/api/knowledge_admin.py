from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import JobType
from app.core.errors import AppError
from app.core.identity import require_role
from app.core.runtime import STATE, check_vectors
from app.db.session import get_db
from app.models.identity import User
from app.models.knowledge import IngestionRun, OkfFile
from app.schemas.common import JobAccepted
from app.services.ingestion.okf_ingest import IngestOptions, ingest_bundle
from app.services.jobs import active_job, create_job, run_job
from app.services.knowledge.state import current_epoch
from app.services.vector.qdrant_store import get_store

router = APIRouter(prefix="/admin/knowledge", tags=["admin-knowledge"])
admin_only = require_role("ADMIN")


def _run_dict(r: IngestionRun | None) -> dict | None:
    if r is None:
        return None
    keys = (
        "id",
        "started_at",
        "finished_at",
        "triggered_by",
        "mode",
        "spec_conformance",
        "embedding_model",
        "files_scanned",
        "added",
        "updated",
        "unchanged",
        "removed",
        "skipped",
        "chunks_upserted",
        "chunks_deleted",
        "errors",
        "status",
    )
    return {k: getattr(r, k) for k in keys}


@router.get("/status")
def knowledge_status(_: User = Depends(admin_only), db: Session = Depends(get_db)):
    store = get_store()
    points = {"official": None, "resolved": None}
    qdrant_ok = True
    try:
        points = {"official": store.count(store.official), "resolved": store.count(store.resolved)}
    except AppError:
        qdrant_ok = False
    files = db.scalars(select(OkfFile).order_by(OkfFile.path)).all()
    last = db.scalar(select(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(1))
    running = active_job(db, JobType.REINDEX.value, None)
    return {
        "spec": {"format": "OKF", "version": "0.2", "source": "https://github.com/GoogleCloudPlatform/open-knowledge-format"},
        "qdrant_ok": qdrant_ok,
        "points": points,
        "epoch": current_epoch(db),
        "reindex_required": STATE.reindex_required,
        "reindex_problems": STATE.reindex_problems,
        "last_run": _run_dict(last),
        "running_job_id": str(running.id) if running else None,
        "files": [
            {
                "path": f.path,
                "knowledge_id": f.knowledge_id,
                "title": f.title,
                "category": f.category,
                "source_url": f.source_url,
                "content_hash": (f.content_hash or "")[:12],
                "status": f.status,
                "chunk_count": f.chunk_count,
                "last_verified_at": f.last_verified_at,
                "version": f.version,
                "error": f.error,
                "last_ingested_at": f.last_ingested_at,
            }
            for f in files
        ],
    }


def _reindex_job(recreate: bool):
    def fn(db: Session, ctx) -> dict:
        res = ingest_bundle(db, IngestOptions(recreate=recreate, triggered_by="admin-ui"), progress=ctx.progress)
        check_vectors(db)
        return {k: v for k, v in res.as_dict().items() if k != "plan"}

    return fn


@router.post("/reindex", status_code=202, response_model=JobAccepted)
def reindex(background: BackgroundTasks, recreate: bool = False, user: User = Depends(admin_only), db: Session = Depends(get_db)):
    if active_job(db, JobType.REINDEX.value, None):
        raise AppError("JOB_IN_PROGRESS", "A re-ingestion is already running.", 409)
    job = create_job(db, JobType.REINDEX.value, user)
    db.commit()
    background.add_task(run_job, job.id, _reindex_job(recreate or STATE.reindex_required))
    return JobAccepted(job_id=job.id)


# ---- Resolved (expert) knowledge -------------------------------------------------------------
from pydantic import BaseModel, Field  # noqa: E402

from app.models.chat import Ticket  # noqa: E402
from app.models.knowledge import KnowledgeRecord  # noqa: E402
from app.services.knowledge import lifecycle  # noqa: E402


def _record(db: Session, r: KnowledgeRecord) -> dict:
    from app.models.identity import User as U

    t = db.get(Ticket, r.ticket_id) if r.ticket_id else None
    return {
        "id": str(r.id),
        "knowledge_group_id": str(r.knowledge_group_id),
        "version": r.version,
        "question_normalised": r.question_normalised,
        "answer": r.answer,
        "category": r.category,
        "validity": r.validity,
        "status_reason": r.status_reason,
        "index_status": r.index_status,
        "indexed_at": r.indexed_at,
        "author": (db.get(U, r.author_user_id) or U(display_name="?")).display_name,
        "approver": (db.get(U, r.approver_user_id) or U(display_name="?")).display_name,
        "approved_at": r.approved_at,
        "ticket_display_id": t.display_id if t else None,
        "supporting_references": r.supporting_references,
    }


@router.get("")
def list_resolved(validity: str | None = None, _: User = Depends(admin_only), db: Session = Depends(get_db)):
    q = select(KnowledgeRecord).order_by(KnowledgeRecord.approved_at.desc())
    if validity:
        q = q.where(KnowledgeRecord.validity.in_(validity.split(",")))
    return [_record(db, r) for r in db.scalars(q.limit(200))]


class SupersedeIn(BaseModel):
    answer: str = Field(min_length=40, max_length=8000)
    question_normalised: str | None = Field(default=None, min_length=5, max_length=1000)
    category: str | None = None
    supporting_references: list[dict] | None = None
    privacy_confirmed: bool


@router.post("/{record_id}/supersede")
def supersede(record_id: uuid.UUID, body: SupersedeIn, user: User = Depends(admin_only), db: Session = Depends(get_db)):
    if not body.privacy_confirmed:
        raise AppError("VALIDATION_ERROR", "Confirm that the answer contains no buyer-private or customer-specific information.", 422)
    new = lifecycle.supersede(db, record_id, user, body.answer, body.question_normalised, body.category, body.supporting_references)
    return _record(db, new)


class RevokeIn(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)


@router.post("/{record_id}/revoke")
def revoke(record_id: uuid.UUID, body: RevokeIn, user: User = Depends(admin_only), db: Session = Depends(get_db)):
    return _record(db, lifecycle.revoke(db, record_id, user, body.reason))
