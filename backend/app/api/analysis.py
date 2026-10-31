"""Run assessments, read results, versions and comparisons (buyer)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.assessments import owned_assessment
from app.core import ratelimit
from app.core.enums import JobType
from app.core.errors import AppError
from app.core.identity import require_role
from app.db.session import get_db
from app.models.assessment import AssessmentVersion, Requirement, RequirementAssessment
from app.models.identity import User
from app.schemas.common import JobAccepted
from app.services.assessment import analyze, versions
from app.services.assessment import requirement_service as RS
from app.services.assessment.summary import build_results
from app.services.jobs import active_job, create_job, run_job

router = APIRouter(tags=["analysis"])
buyer = require_role("BUYER")


@router.post("/assessments/{assessment_id}/analyze", response_model=JobAccepted, status_code=202)
def run(assessment_id: uuid.UUID, background: BackgroundTasks, user: User = Depends(buyer), db: Session = Depends(get_db)):
    owned_assessment(db, user, assessment_id)
    if active_job(db, JobType.ANALYZE.value, assessment_id) or active_job(db, JobType.EXTRACT_PDF.value, assessment_id):
        raise AppError("JOB_IN_PROGRESS", "An assessment run is already in progress.", 409)
    a = RS.lock_assessment(db, assessment_id)
    confirmed = db.scalar(
        select(func.count(Requirement.id)).where(
            Requirement.assessment_id == a.id, Requirement.is_removed.is_(False), Requirement.buyer_confirmed.is_(True)
        )
    )
    if not confirmed:
        raise AppError("NO_CONFIRMED_REQUIREMENTS", "Confirm at least one requirement before running the assessment.", 422)
    from app.services.llm.client import get_llm

    get_llm()  # 503 LLM_NOT_CONFIGURED before anything changes
    ratelimit.check("job", str(user.id))
    previous = analyze.start_analysis(db, a)
    job = create_job(db, JobType.ANALYZE.value, user, a.id, total=confirmed)
    db.commit()
    aid, jid, uid = a.id, job.id, user.id

    def fn(session: Session, ctx) -> dict:
        return analyze.run_analysis(session, aid, jid, session.get(User, uid), ctx.progress)

    def on_failure(session: Session) -> None:
        analyze.restore_status(session, aid, previous)

    background.add_task(run_job, job.id, fn, on_failure)
    return JobAccepted(job_id=job.id)


@router.get("/assessments/{assessment_id}/results")
def results(assessment_id: uuid.UUID, version: int | None = None, user: User = Depends(buyer), db: Session = Depends(get_db)):
    a = owned_assessment(db, user, assessment_id)
    return build_results(db, a, versions.get_version(db, a.id, version))


@router.get("/assessments/{assessment_id}/versions")
def list_versions(assessment_id: uuid.UUID, user: User = Depends(buyer), db: Session = Depends(get_db)):
    a = owned_assessment(db, user, assessment_id)
    rows = db.scalars(
        select(AssessmentVersion).where(AssessmentVersion.assessment_id == a.id).order_by(AssessmentVersion.version_no.desc())
    ).all()
    out = []
    for v in rows:
        n = db.scalar(select(func.count(RequirementAssessment.id)).where(RequirementAssessment.version_id == v.id))
        out.append(
            {
                "version_no": v.version_no,
                "analyzed_at": v.analyzed_at,
                "requirement_set_revision": v.requirement_set_revision,
                "status_counts": v.summary.get("status_counts", {}),
                "requirement_count": n,
                "knowledge_epoch": v.knowledge_epoch,
            }
        )
    return out


@router.get("/assessments/{assessment_id}/versions/{a_no}/compare/{b_no}")
def compare(assessment_id: uuid.UUID, a_no: int, b_no: int, user: User = Depends(buyer), db: Session = Depends(get_db)):
    a = owned_assessment(db, user, assessment_id)
    return {"from_version": a_no, "to_version": b_no, "changes": versions.compare(db, a.id, a_no, b_no)}


@router.get("/assessments/{assessment_id}/pending-changes")
def pending(assessment_id: uuid.UUID, user: User = Depends(buyer), db: Session = Depends(get_db)):
    a = owned_assessment(db, user, assessment_id)
    return {"changes": versions.pending_changes(db, a.id)}
