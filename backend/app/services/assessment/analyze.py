"""The ANALYZE job: assess every confirmed requirement and create a new immutable version (§10.8)."""

from __future__ import annotations

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import AssessmentStatus, AuditAction
from app.models.assessment import Assessment, AssessmentVersion, EvidenceReference, Requirement, RequirementAssessment
from app.prompts import judge as judge_prompt
from app.prompts import summary as summary_prompt
from app.services.assessment.judge import Assessed, assess_requirement
from app.services.audit import audit
from app.services.knowledge.state import current_epoch
from app.services.llm.client import get_llm

log = logging.getLogger("dealbridge.analyze")

BLOCKING_PRIORITIES = {"CRITICAL", "HIGH"}
BLOCKING_STATUSES = {"NOT_SUPPORTED", "PARTIALLY_SUPPORTED", "UNKNOWN"}
STATUSES = ["SUPPORTED", "PARTIALLY_SUPPORTED", "NEEDS_VALIDATION", "NOT_SUPPORTED", "UNKNOWN"]
WORKERS = 4


def snapshot_requirements(db: Session, assessment_id: uuid.UUID) -> list[dict]:
    rows = db.scalars(
        select(Requirement)
        .where(Requirement.assessment_id == assessment_id, Requirement.is_removed.is_(False), Requirement.buyer_confirmed.is_(True))
        .order_by(Requirement.seq)
    ).all()
    return [
        {
            "id": str(r.id),
            "display_id": r.display_id,
            "seq": r.seq,
            "original_text": r.original_text,
            "normalized_text": r.normalized_text,
            "category": r.category,
            "priority": r.priority,
            "source_type": r.source_type,
            "source_reference": r.source_reference,
            "clarification_waived": r.clarification_waived,
        }
        for r in rows
    ]


def _dedupe(items: list[str]) -> list[str]:
    seen, out = set(), []
    for i in items:
        k = " ".join(i.lower().split())
        if k and k not in seen:
            seen.add(k)
            out.append(i.strip())
    return out


def _words(text: str, limit: int) -> str:
    w = text.split()
    return text.strip() if len(w) <= limit else " ".join(w[:limit]).rstrip(",;:") + "…"


def run_analysis(db: Session, assessment_id: uuid.UUID, job_id: uuid.UUID, user, progress) -> dict:
    s = get_settings()
    a = db.get(Assessment, assessment_id)
    reqs = snapshot_requirements(db, assessment_id)
    epoch = current_epoch(db)
    total = len(reqs)
    results: dict[str, Assessed] = {}
    done = 0
    progress(0, total, f"Assessing {total} requirement(s)")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(assess_requirement, r): r for r in reqs}
        for fut in as_completed(futures):
            r = futures[fut]
            results[r["id"]] = fut.result()  # an infrastructure error aborts the whole job (no fabricated UNKNOWN)
            done += 1
            progress(done, total, f"Assessing {r['display_id']} ({done} of {total})")

    ordered = [results[r["id"]] for r in reqs]
    counts = {st: sum(1 for x in ordered if x.status == st) for st in STATUSES}
    blockers = [
        x.requirement["display_id"] for x in ordered if x.requirement["priority"] in BLOCKING_PRIORITIES and x.status in BLOCKING_STATUSES
    ]
    progress(total, total, "Writing the summary")
    summ = get_llm().complete_structured(
        "main",
        summary_prompt.SYSTEM,
        summary_prompt.build_messages(
            [
                {
                    "display_id": x.requirement["display_id"],
                    "priority": x.requirement["priority"],
                    "status": x.status,
                    "text": x.requirement["normalized_text"],
                    "established": x.explanation.get("established", ""),
                    "unverified": x.explanation.get("unverified", ""),
                }
                for x in ordered
            ],
            blockers,
            counts,
        ),
        summary_prompt.AssessmentSummary,
        summary_prompt.TOOL,
        800,
        0.0,
    )
    now = datetime.now(UTC)
    a = db.scalar(select(Assessment).where(Assessment.id == assessment_id).with_for_update())
    version = AssessmentVersion(
        id=uuid.uuid4(),
        assessment_id=a.id,
        version_no=a.latest_version_no + 1,
        requirement_set_revision=a.requirement_set_revision,
        requirements_snapshot=reqs,
        knowledge_epoch=epoch,
        summary={
            "executive_summary": _words(summ.executive_summary, 120),
            "status_counts": counts,
            "blockers": blockers,
            "next_steps": [n for n in summ.next_steps if n.strip()][:8],
            "assumptions": _dedupe([i for x in ordered for i in x.assumptions]),
            "missing_information": _dedupe([i for x in ordered for i in x.missing_information]),
            "questions_for_seller": _dedupe([i for x in ordered for i in x.questions_for_seller]),
        },
        model=s.LLM_MODEL,
        prompt_versions={"judge": judge_prompt.PROMPT_VERSION, "summary": summary_prompt.PROMPT_VERSION},
        job_id=job_id,
        analyzed_at=now,
    )
    db.add(version)
    db.flush()
    for x in ordered:
        ra = RequirementAssessment(
            id=uuid.uuid4(),
            version_id=version.id,
            requirement_id=uuid.UUID(x.requirement["id"]),
            display_id=x.requirement["display_id"],
            requirement_text=x.requirement["normalized_text"],
            category=x.requirement["category"],
            priority=x.requirement["priority"],
            status=x.status,
            explanation=x.explanation,
            supported_part=x.supported_part,
            unestablished_part=x.unestablished_part,
            assumptions=x.assumptions,
            missing_information=x.missing_information,
            questions_for_seller=x.questions_for_seller,
            has_conflict=x.has_conflict,
            conflict_description=x.conflict_description,
            is_blocker=x.requirement["display_id"] in blockers,
            guardrail_notes=x.guardrail_notes,
            retrieval_summary=x.retrieval_summary,
            model=x.model,
            prompt_version=x.prompt_version,
            assessed_at=now,
        )
        db.add(ra)
        db.flush()
        for e in x.evidence:
            db.add(EvidenceReference(requirement_assessment_id=ra.id, **e))
    a.status, a.latest_version_no = AssessmentStatus.ANALYZED.value, version.version_no
    # If the requirement set changed during the run (it is locked, so this should not happen), mark it stale.
    audit(db, AuditAction.ASSESSMENT_ANALYZED, "assessment", a.id, user, {"version_no": version.version_no, "status_counts": counts})
    db.commit()
    return {"version_no": version.version_no, "status_counts": counts, "blockers": blockers}


def start_analysis(db: Session, a: Assessment) -> str:
    """Lock the assessment for the run and remember the status to restore on failure."""
    previous = a.status
    a.status = AssessmentStatus.ANALYZING.value
    return previous


def restore_status(db: Session, assessment_id: uuid.UUID, previous: str) -> None:
    a = db.get(Assessment, assessment_id)
    if a is not None and a.status == AssessmentStatus.ANALYZING.value:
        a.status = previous
