"""PostgreSQL-tracked background jobs run with FastAPI BackgroundTasks (no Celery, no Redis)."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import JobStatus
from app.core.errors import INFRA_ERRORS, AppError
from app.db.session import session_factory
from app.models.system import Job

log = logging.getLogger("dealbridge.jobs")


def create_job(db: Session, job_type: str, user, assessment_id: uuid.UUID | None = None, total: int = 0) -> Job:
    job = Job(
        type=job_type,
        status=JobStatus.QUEUED.value,
        assessment_id=assessment_id,
        created_by=getattr(user, "id", None),
        progress_total=total,
    )
    db.add(job)
    db.flush()
    return job


def active_job(db: Session, job_type: str, assessment_id: uuid.UUID | None) -> Job | None:
    q = select(Job).where(Job.type == job_type, Job.status.in_([JobStatus.QUEUED.value, JobStatus.RUNNING.value]))
    if assessment_id is not None:
        q = q.where(Job.assessment_id == assessment_id)
    return db.scalar(q.limit(1))


class JobContext:
    """Handed to job functions: progress reporting with its own short transactions."""

    def __init__(self, job_id: uuid.UUID):
        self.job_id = job_id

    def progress(self, done: int, total: int, message: str) -> None:
        with session_factory()() as db:
            job = db.get(Job, self.job_id)
            if job:
                job.progress_done, job.progress_total, job.progress_message = done, total, message
                db.commit()


def run_job(job_id: uuid.UUID, fn: Callable[[Session, JobContext], dict], on_failure: Callable[[Session], None] | None = None) -> None:
    """Execute fn(db, ctx) for a job; record SUCCEEDED with its result or FAILED with a stable error code."""
    with session_factory()() as db:
        job = db.get(Job, job_id)
        if job is None:
            return
        job.status, job.started_at = JobStatus.RUNNING.value, datetime.now(UTC)
        db.commit()
    ctx = JobContext(job_id)
    try:
        with session_factory()() as db:
            result = fn(db, ctx)
            db.commit()
        status, code, message = JobStatus.SUCCEEDED.value, None, None
    except Exception as exc:  # recorded on the job; never re-raised into the server loop
        result = None
        status = JobStatus.FAILED.value
        if isinstance(exc, AppError):
            code, message = exc.code, exc.message
        else:
            code, message = "INTERNAL_ERROR", "The job failed unexpectedly."
            log.exception("job failed", extra={"job_id": str(job_id)})
        if on_failure:
            with session_factory()() as db:
                on_failure(db)
                db.commit()
        if isinstance(exc, INFRA_ERRORS):
            log.warning("job failed on infrastructure", extra={"job_id": str(job_id), "code": code})
    with session_factory()() as db:
        job = db.get(Job, job_id)
        job.status, job.result, job.error_code, job.error_message = status, result, code, message
        job.finished_at = datetime.now(UTC)
        if status == JobStatus.SUCCEEDED.value:
            job.progress_done = max(job.progress_done, job.progress_total)
        db.commit()
