"""Seller-side reads and attributed responses. Responses never change requirements or system statuses."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import AuditAction
from app.core.errors import AppError, not_found
from app.models.assessment import Assessment, AssessmentVersion, Requirement
from app.models.identity import Organization, User
from app.models.sharing import SellerResponse
from app.services.audit import audit
from app.services.sharing.share_service import seller_assessment, seller_version


def responses_for_version(db: Session, a: Assessment, v: AssessmentVersion) -> dict[str, list[dict]]:
    """Seller responses made on this version or earlier versions, per requirement id."""
    versions = {x.id: x.version_no for x in db.scalars(select(AssessmentVersion).where(AssessmentVersion.assessment_id == a.id))}
    out: dict[str, list[dict]] = {}
    for r in db.scalars(select(SellerResponse).where(SellerResponse.assessment_id == a.id).order_by(SellerResponse.created_at)):
        vno = versions.get(r.version_id, 0)
        if vno > v.version_no:
            continue
        u = db.get(User, r.seller_user_id)
        org = db.get(Organization, u.organization_id) if u else None
        out.setdefault(str(r.requirement_id), []).append(
            {
                "id": str(r.id),
                "seller_name": u.display_name if u else "Seller",
                "seller_org": org.name if org else "",
                "assertion": r.assertion,
                "body": r.body,
                "created_at": r.created_at,
                "version_no": vno,
                "label": "Seller statement — not verified by product documentation",
                "attachments": _attachments(db, r.attachment_document_ids or []),
            }
        )
    return out


def _attachments(db: Session, ids: list[str]) -> list[dict]:
    from app.models.assessment import UploadedDocument

    out = []
    for i in ids:
        d = db.get(UploadedDocument, i)
        if d is not None:
            out.append({"id": str(d.id), "filename": d.original_filename, "label": "Seller-provided document (not official knowledge)"})
    return out


def add_response(db: Session, seller: User, requirement_id, version_no: int, body: str, assertion: str) -> SellerResponse:
    r = db.get(Requirement, requirement_id)
    if r is None:
        raise not_found("Requirement")
    a = seller_assessment(db, seller, r.assessment_id)
    v = seller_version(db, seller, a, version_no)
    if str(r.id) not in {s["id"] for s in v.requirements_snapshot}:
        raise AppError("VALIDATION_ERROR", "This requirement is not part of the shared version.", 422)
    resp = SellerResponse(
        assessment_id=a.id, requirement_id=r.id, version_id=v.id, seller_user_id=seller.id, body=body.strip(), assertion=assertion
    )
    db.add(resp)
    db.flush()
    audit(
        db,
        AuditAction.SELLER_RESPONSE_ADDED,
        "seller_response",
        resp.id,
        seller,
        {"assessment_id": str(a.id), "requirement": r.display_id, "assertion": assertion},
    )
    return resp
