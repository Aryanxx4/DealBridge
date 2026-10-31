from __future__ import annotations

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
