from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.errors import not_found
from app.core.identity import get_current_user
from app.db.session import get_db
from app.models.identity import User
from app.models.system import Job
from app.schemas.common import JobOut

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if job is None or (job.created_by != user.id and user.role != "ADMIN"):
        raise not_found("Job")
    return JobOut.of(job)
