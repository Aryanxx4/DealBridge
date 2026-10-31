"""Version comparison and pending-change detection (§10.9)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError, not_found
from app.models.assessment import AssessmentVersion, RequirementAssessment
from app.services.assessment.analyze import snapshot_requirements


def get_version(db: Session, assessment_id: uuid.UUID, version_no: int | None) -> AssessmentVersion:
    q = select(AssessmentVersion).where(AssessmentVersion.assessment_id == assessment_id)
    q = q.where(AssessmentVersion.version_no == version_no) if version_no else q.order_by(AssessmentVersion.version_no.desc()).limit(1)
    v = db.scalar(q)
    if v is None:
        if version_no:
            raise not_found("Version")
        raise AppError("NO_ANALYSIS", "This assessment has not been analysed yet.", 409)
    return v


def statuses(db: Session, version_id: uuid.UUID) -> dict[str, str]:
    return {
        str(r.requirement_id): r.status
        for r in db.scalars(select(RequirementAssessment).where(RequirementAssessment.version_id == version_id))
    }


def diff(old: list[dict], new: list[dict], old_status: dict | None = None, new_status: dict | None = None) -> list[dict]:
    a, b = {r["id"]: r for r in old}, {r["id"]: r for r in new}
    out = []
    for rid in sorted(set(a) | set(b), key=lambda i: (b.get(i) or a.get(i))["seq"]):
        x, y = a.get(rid), b.get(rid)
        ref = y or x
        item = {
            "requirement_id": rid,
            "display_id": ref["display_id"],
            "previous_text": x["normalized_text"] if x else None,
            "new_text": y["normalized_text"] if y else None,
            "previous_priority": x["priority"] if x else None,
            "new_priority": y["priority"] if y else None,
            "previous_status": (old_status or {}).get(rid),
            "new_status": (new_status or {}).get(rid),
        }
        if x is None:
            change = "ADDED"
        elif y is None:
            change = "REMOVED"
        elif x["normalized_text"] != y["normalized_text"]:
            change = "TEXT_CHANGED"
        elif x["priority"] != y["priority"]:
            change = "PRIORITY_CHANGED"
        elif old_status is not None and new_status is not None and old_status.get(rid) != new_status.get(rid):
            change = "STATUS_CHANGED"
        else:
            change = "UNCHANGED"
        out.append(item | {"change": change})
    return out


def compare(db: Session, assessment_id: uuid.UUID, a_no: int, b_no: int) -> list[dict]:
    va, vb = get_version(db, assessment_id, a_no), get_version(db, assessment_id, b_no)
    return diff(va.requirements_snapshot, vb.requirements_snapshot, statuses(db, va.id), statuses(db, vb.id))


def changes_since_previous(db: Session, v: AssessmentVersion) -> list[dict] | None:
    if v.version_no <= 1:
        return None
    prev = get_version(db, v.assessment_id, v.version_no - 1)
    return [
        d
        for d in diff(prev.requirements_snapshot, v.requirements_snapshot, statuses(db, prev.id), statuses(db, v.id))
        if d["change"] != "UNCHANGED"
    ]


def pending_changes(db: Session, assessment_id: uuid.UUID) -> list[dict]:
    """Differences between the latest version's snapshot and the current confirmed requirement set."""
    try:
        v = get_version(db, assessment_id, None)
    except AppError:
        return []
    current = snapshot_requirements(db, assessment_id)
    return [d for d in diff(v.requirements_snapshot, current) if d["change"] != "UNCHANGED"]
