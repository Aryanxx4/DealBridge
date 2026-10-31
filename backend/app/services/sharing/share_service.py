"""Explicit, version-bound sharing with seller organisations (R6, §10.11)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import AuditAction, OrgKind
from app.core.errors import AppError, not_found
from app.models.assessment import Assessment, AssessmentVersion
from app.models.identity import Organization, User
from app.models.sharing import AssessmentShare
from app.services.assessment.versions import get_version
from app.services.audit import audit


def seller_org(db: Session, org_id: uuid.UUID) -> Organization:
    org = db.get(Organization, org_id)
    if org is None or org.kind != OrgKind.SELLER_ORG.value:
        raise not_found("Seller organisation")
    return org


def share(db: Session, a: Assessment, user: User, seller_org_id: uuid.UUID, version_no: int | None, confirm: bool) -> AssessmentShare:
    if not confirm:
        raise AppError("CONSENT_REQUIRED", "Confirm that you consent to sharing this version with the seller.", 400)
    org = seller_org(db, seller_org_id)
    v = get_version(db, a.id, version_no)  # 409 NO_ANALYSIS if none
    existing = db.scalar(
        select(AssessmentShare).where(
            AssessmentShare.assessment_id == a.id,
            AssessmentShare.seller_org_id == org.id,
            AssessmentShare.version_id == v.id,
            AssessmentShare.revoked_at.is_(None),
        )
    )
    if existing:
        return existing
    s = AssessmentShare(assessment_id=a.id, seller_org_id=org.id, version_id=v.id, shared_by=user.id, shared_at=datetime.now(UTC))
    db.add(s)
    db.flush()
    audit(db, AuditAction.ASSESSMENT_SHARED, "assessment", a.id, user, {"seller_org": org.name, "version_no": v.version_no})
    return s


def unshare(db: Session, a: Assessment, user: User, seller_org_id: uuid.UUID) -> int:
    org = seller_org(db, seller_org_id)
    rows = db.scalars(
        select(AssessmentShare).where(
            AssessmentShare.assessment_id == a.id, AssessmentShare.seller_org_id == org.id, AssessmentShare.revoked_at.is_(None)
        )
    ).all()
    now = datetime.now(UTC)
    for r in rows:
        r.revoked_at, r.revoked_by = now, user.id
    if rows:
        audit(db, AuditAction.ASSESSMENT_SHARE_REVOKED, "assessment", a.id, user, {"seller_org": org.name, "rows": len(rows)})
    return len(rows)


def active_shares(db: Session, *, assessment_id=None, seller_org_id=None) -> list[AssessmentShare]:
    q = select(AssessmentShare).where(AssessmentShare.revoked_at.is_(None))
    if assessment_id is not None:
        q = q.where(AssessmentShare.assessment_id == assessment_id)
    if seller_org_id is not None:
        q = q.where(AssessmentShare.seller_org_id == seller_org_id)
    return list(db.scalars(q.order_by(AssessmentShare.shared_at.desc())))


def shared_versions(db: Session, assessment_id: uuid.UUID, seller_org_id: uuid.UUID) -> list[AssessmentVersion]:
    ids = {s.version_id for s in active_shares(db, assessment_id=assessment_id, seller_org_id=seller_org_id)}
    if not ids:
        return []
    return list(db.scalars(select(AssessmentVersion).where(AssessmentVersion.id.in_(ids)).order_by(AssessmentVersion.version_no.desc())))


def seller_assessment(db: Session, user: User, assessment_id: uuid.UUID) -> Assessment:
    """The assessment if the seller's organisation holds an unrevoked share; 404 otherwise."""
    a = db.get(Assessment, assessment_id)
    if a is None or not active_shares(db, assessment_id=assessment_id, seller_org_id=user.organization_id):
        raise not_found("Assessment")
    return a


def seller_version(db: Session, user: User, a: Assessment, version_no: int | None) -> AssessmentVersion:
    versions = shared_versions(db, a.id, user.organization_id)
    if not versions:
        raise not_found("Assessment")
    if version_no is None:
        return versions[0]
    for v in versions:
        if v.version_no == version_no:
            return v
    raise not_found("Version")  # never reveal versions that were not shared
