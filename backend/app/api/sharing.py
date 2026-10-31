"""Sharing, report download, seller workspace, seller responses and follow-ups."""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.assessments import owned_assessment
from app.core.enums import AuditAction, OrgKind
from app.core.errors import forbidden_role
from app.core.identity import get_current_user, require_role
from app.db.session import get_db
from app.models.assessment import Assessment
from app.models.chat import Ticket
from app.models.identity import Organization, User
from app.models.sharing import FollowUpRequest
from app.services.assessment.summary import FINAL_TICKETS, build_results
from app.services.assessment.versions import get_version
from app.services.audit import audit
from app.services.reports.pdf_report import build_report, filename
from app.services.sharing import followup_service as FU
from app.services.sharing import share_service as SH
from app.services.sharing.seller_service import add_response

router = APIRouter(tags=["sharing"])
buyer = require_role("BUYER")
seller = require_role("SELLER")


# ---- buyer: sharing -------------------------------------------------------------------------
@router.get("/seller-orgs")
def seller_orgs(_: User = Depends(buyer), db: Session = Depends(get_db)):
    return [
        {"id": str(o.id), "name": o.name}
        for o in db.scalars(select(Organization).where(Organization.kind == OrgKind.SELLER_ORG.value).order_by(Organization.name))
    ]


class ShareIn(BaseModel):
    seller_org_id: uuid.UUID
    version_no: int | None = None
    confirm: bool = False


@router.post("/assessments/{assessment_id}/share")
def share(assessment_id: uuid.UUID, body: ShareIn, user: User = Depends(buyer), db: Session = Depends(get_db)):
    a = owned_assessment(db, user, assessment_id)
    s = SH.share(db, a, user, body.seller_org_id, body.version_no, body.confirm)
    db.commit()
    return {"share_id": str(s.id), "stale": a.status == "STALE"}


class UnshareIn(BaseModel):
    seller_org_id: uuid.UUID


@router.post("/assessments/{assessment_id}/unshare")
def unshare(assessment_id: uuid.UUID, body: UnshareIn, user: User = Depends(buyer), db: Session = Depends(get_db)):
    a = owned_assessment(db, user, assessment_id)
    n = SH.unshare(db, a, user, body.seller_org_id)
    db.commit()
    return {"revoked": n}


@router.get("/assessments/{assessment_id}/shares")
def shares(assessment_id: uuid.UUID, user: User = Depends(buyer), db: Session = Depends(get_db)):
    from app.models.assessment import AssessmentVersion
    from app.models.sharing import AssessmentShare

    a = owned_assessment(db, user, assessment_id)
    rows = db.scalars(select(AssessmentShare).where(AssessmentShare.assessment_id == a.id).order_by(AssessmentShare.shared_at.desc())).all()
    return [
        {
            "id": str(s.id),
            "seller_org_id": str(s.seller_org_id),
            "seller_org": db.get(Organization, s.seller_org_id).name,
            "version_no": db.get(AssessmentVersion, s.version_id).version_no,
            "shared_at": s.shared_at,
            "revoked_at": s.revoked_at,
            "active": s.revoked_at is None,
        }
        for s in rows
    ]


# ---- report (buyer owner, or seller with a share of that version) -----------------------------
@router.get("/assessments/{assessment_id}/report.pdf")
def report(assessment_id: uuid.UUID, version: int | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == "BUYER":
        a = owned_assessment(db, user, assessment_id)
        v = get_version(db, a.id, version)
        open_t = [
            {"display_id": t.display_id, "normalised_question": t.normalised_question, "status": t.status}
            for t in db.scalars(
                select(Ticket).where(Ticket.assessment_id == a.id, Ticket.created_by == user.id).order_by(Ticket.created_at)
            )
            if t.status not in FINAL_TICKETS
        ]
        results = build_results(db, a, v)
    elif user.role == "SELLER":
        a = SH.seller_assessment(db, user, assessment_id)
        v = SH.seller_version(db, user, a, version)
        results = build_results(db, a, v, viewer="SELLER", include_tickets=False)
        open_t = None  # tickets are never shown to sellers
    else:
        raise forbidden_role()
    org = db.get(Organization, a.organization_id)
    pdf = build_report(results, org.name if org else None, open_t)
    audit(db, AuditAction.REPORT_DOWNLOADED, "assessment", a.id, user, {"version_no": v.version_no})
    db.commit()
    return Response(
        pdf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename(a.title, v.version_no)}"'}
    )


# ---- seller workspace -----------------------------------------------------------------------
def _buyer_info(db: Session, a: Assessment) -> dict:
    owner = db.get(User, a.owner_user_id)
    org = db.get(Organization, a.organization_id)
    return {"buyer_name": owner.display_name if owner else None, "buyer_org": org.name if org else None}


@router.get("/seller/assessments")
def seller_assessments(user: User = Depends(seller), db: Session = Depends(get_db)):
    out, seen = [], set()
    for s in SH.active_shares(db, seller_org_id=user.organization_id):
        if s.assessment_id in seen:
            continue
        seen.add(s.assessment_id)
        a = db.get(Assessment, s.assessment_id)
        v = SH.seller_version(db, user, a, None)
        open_fu = db.scalars(
            select(FollowUpRequest).where(
                FollowUpRequest.assessment_id == a.id,
                FollowUpRequest.seller_org_id == user.organization_id,
                FollowUpRequest.status != "CLOSED",
            )
        ).all()
        out.append(
            {
                "id": str(a.id),
                "title": a.title,
                **_buyer_info(db, a),
                "shared_version": v.version_no,
                "shared_at": s.shared_at,
                "status_counts": v.summary.get("status_counts", {}),
                "open_follow_ups": len(open_fu),
            }
        )
    return out


@router.get("/seller/assessments/{assessment_id}")
def seller_assessment(assessment_id: uuid.UUID, version: int | None = None, user: User = Depends(seller), db: Session = Depends(get_db)):
    a = SH.seller_assessment(db, user, assessment_id)
    v = SH.seller_version(db, user, a, version)
    res = build_results(db, a, v, viewer="SELLER", include_tickets=False)
    res["assessment"] |= _buyer_info(db, a)
    res["shared_versions"] = [x.version_no for x in SH.shared_versions(db, a.id, user.organization_id)]
    res["knowledge_updated"] = False  # internal signal for the buyer only
    return res


class SellerResponseIn(BaseModel):
    version_no: int
    body: str = Field(min_length=1, max_length=4000)
    assertion: Literal["NONE", "CONFIRMS_SUPPORT", "CONFIRMS_LIMITATION", "NEEDS_INFO_FROM_BUYER"] = "NONE"


@router.post("/requirements/{requirement_id}/seller-response", status_code=201)
def seller_response(requirement_id: uuid.UUID, body: SellerResponseIn, user: User = Depends(seller), db: Session = Depends(get_db)):
    r = add_response(db, user, requirement_id, body.version_no, body.body, body.assertion)
    db.commit()
    return {"id": str(r.id), "assertion": r.assertion, "body": r.body, "created_at": r.created_at}


# ---- follow-ups -----------------------------------------------------------------------------
class FollowUpIn(BaseModel):
    seller_org_id: uuid.UUID
    subject: str = Field(min_length=3, max_length=200)
    message: str = Field(default="", max_length=4000)
    related_requirement_ids: list[str] = Field(default_factory=list, max_length=100)


@router.post("/assessments/{assessment_id}/follow-ups", status_code=201)
def create_follow_up(assessment_id: uuid.UUID, body: FollowUpIn, user: User = Depends(buyer), db: Session = Depends(get_db)):
    a = owned_assessment(db, user, assessment_id)
    f = FU.create(db, a, user, body.seller_org_id, body.subject, body.message, body.related_requirement_ids)
    db.commit()
    return FU.out(db, f, user, True)


@router.get("/assessments/{assessment_id}/follow-ups")
def list_follow_ups(assessment_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == "BUYER":
        a = owned_assessment(db, user, assessment_id)
        q = select(FollowUpRequest).where(FollowUpRequest.assessment_id == a.id)
    elif user.role == "SELLER":
        a = SH.seller_assessment(db, user, assessment_id)
        q = select(FollowUpRequest).where(FollowUpRequest.assessment_id == a.id, FollowUpRequest.seller_org_id == user.organization_id)
    else:
        raise forbidden_role()
    return [FU.out(db, f, user) for f in db.scalars(q.order_by(FollowUpRequest.created_at.desc()))]


@router.get("/seller/follow-ups")
def seller_follow_ups(status: str | None = None, user: User = Depends(seller), db: Session = Depends(get_db)):
    shared = {s.assessment_id for s in SH.active_shares(db, seller_org_id=user.organization_id)}
    q = select(FollowUpRequest).where(FollowUpRequest.seller_org_id == user.organization_id)
    if status:
        q = q.where(FollowUpRequest.status.in_(status.split(",")))
    return [FU.out(db, f, user) for f in db.scalars(q.order_by(FollowUpRequest.updated_at.desc())) if f.assessment_id in shared]


@router.get("/follow-ups/{follow_up_id}")
def get_follow_up(follow_up_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    f, _ = FU.access(db, user, follow_up_id)
    return FU.out(db, f, user, True)


class MessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class ReasonIn(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)


def _seller_action(fn):
    def endpoint(follow_up_id: uuid.UUID, user: User = Depends(seller), db: Session = Depends(get_db)):
        f, _ = FU.access(db, user, follow_up_id)
        fn(db, f, user)
        db.commit()
        return FU.out(db, f, user, True)

    return endpoint


router.add_api_route("/follow-ups/{follow_up_id}/accept", _seller_action(FU.accept), methods=["POST"])


@router.post("/follow-ups/{follow_up_id}/reject")
def reject_follow_up(follow_up_id: uuid.UUID, body: ReasonIn, user: User = Depends(seller), db: Session = Depends(get_db)):
    f, _ = FU.access(db, user, follow_up_id)
    FU.reject(db, f, user, body.reason)
    db.commit()
    return FU.out(db, f, user, True)


@router.post("/follow-ups/{follow_up_id}/responses")
def respond_follow_up(follow_up_id: uuid.UUID, body: MessageIn, user: User = Depends(seller), db: Session = Depends(get_db)):
    f, _ = FU.access(db, user, follow_up_id)
    FU.respond(db, f, user, body.body)
    db.commit()
    return FU.out(db, f, user, True)


@router.post("/follow-ups/{follow_up_id}/messages")
def buyer_message(follow_up_id: uuid.UUID, body: MessageIn, user: User = Depends(buyer), db: Session = Depends(get_db)):
    f, _ = FU.access(db, user, follow_up_id)
    FU.buyer_message(db, f, user, body.body)
    db.commit()
    return FU.out(db, f, user, True)


@router.post("/follow-ups/{follow_up_id}/close")
def close_follow_up(follow_up_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role not in ("BUYER", "SELLER"):
        raise forbidden_role()
    f, _ = FU.access(db, user, follow_up_id)
    FU.close(db, f, user)
    db.commit()
    return FU.out(db, f, user, True)
