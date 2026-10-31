"""Buyer-seller follow-up threads (§10.13). Messages are append-only; CLOSED threads are read-only."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import AuditAction, FollowUpStatus
from app.core.errors import AppError, invalid_state, not_found
from app.models.assessment import Assessment
from app.models.identity import Organization, User
from app.models.sharing import FollowUpMessage, FollowUpRequest
from app.services.audit import audit
from app.services.sharing.share_service import active_shares, seller_org

F = FollowUpStatus


def access(db: Session, user: User, follow_up_id: uuid.UUID) -> tuple[FollowUpRequest, Assessment]:
    f = db.get(FollowUpRequest, follow_up_id)
    if f is None:
        raise not_found("Follow-up")
    a = db.get(Assessment, f.assessment_id)
    if user.role == "BUYER" and a.owner_user_id == user.id:
        return f, a
    if (
        user.role == "SELLER"
        and f.seller_org_id == user.organization_id
        and active_shares(db, assessment_id=a.id, seller_org_id=user.organization_id)
    ):
        return f, a  # revoking the share removes access immediately
    raise not_found("Follow-up")


def _message(db: Session, f: FollowUpRequest, user: User, body: str) -> FollowUpMessage:
    m = FollowUpMessage(follow_up_id=f.id, author_user_id=user.id, author_role=user.role, body=body.strip())
    db.add(m)
    return m


def create(
    db: Session, a: Assessment, buyer: User, seller_org_id: uuid.UUID, subject: str, message: str, requirement_ids: list[str]
) -> FollowUpRequest:
    org = seller_org(db, seller_org_id)
    if not active_shares(db, assessment_id=a.id, seller_org_id=org.id):
        raise AppError("NOT_SHARED", "Share the assessment with this seller before requesting a follow-up.", 409)
    f = FollowUpRequest(
        assessment_id=a.id,
        seller_org_id=org.id,
        requested_by=buyer.id,
        subject=subject.strip(),
        related_requirement_ids=requirement_ids,
        status=F.REQUESTED.value,
        seller_decision="PENDING",
    )
    db.add(f)
    db.flush()
    if message.strip():
        _message(db, f, buyer, message)
    audit(db, AuditAction.FOLLOWUP_CREATED, "follow_up", f.id, buyer, {"assessment_id": str(a.id), "seller_org": org.name})
    return f


def _closed_guard(f: FollowUpRequest) -> None:
    if f.status == F.CLOSED.value:
        raise invalid_state("This follow-up is closed and read-only.", [])


def _updated(db, f, user, what):
    audit(db, AuditAction.FOLLOWUP_UPDATED, "follow_up", f.id, user, {"action": what, "status": f.status})


def accept(db: Session, f: FollowUpRequest, seller: User) -> None:
    if f.status != F.REQUESTED.value:
        raise invalid_state("Only a requested follow-up can be accepted.", _allowed(f, seller))
    f.status, f.seller_decision = F.IN_PROGRESS.value, "ACCEPTED"
    _updated(db, f, seller, "accept")


def reject(db: Session, f: FollowUpRequest, seller: User, reason: str) -> None:
    if f.status != F.REQUESTED.value:
        raise invalid_state("Only a requested follow-up can be rejected.", _allowed(f, seller))
    f.status, f.seller_decision, f.decision_reason = F.CLOSED.value, "REJECTED", reason.strip()
    f.closed_at, f.closed_by = datetime.now(UTC), seller.id
    _updated(db, f, seller, "reject")


def respond(db: Session, f: FollowUpRequest, seller: User, body: str) -> None:
    if f.status not in (F.REQUESTED.value, F.IN_PROGRESS.value):
        raise invalid_state("You can respond to a requested or in-progress follow-up.", _allowed(f, seller))
    if f.status == F.REQUESTED.value:
        f.seller_decision = "ACCEPTED"
    _message(db, f, seller, body)
    f.status = F.RESPONDED.value
    _updated(db, f, seller, "respond")


def buyer_message(db: Session, f: FollowUpRequest, buyer: User, body: str) -> None:
    _closed_guard(f)
    _message(db, f, buyer, body)
    if f.status == F.RESPONDED.value:
        f.status = F.IN_PROGRESS.value
    _updated(db, f, buyer, "add_information")


def close(db: Session, f: FollowUpRequest, user: User) -> None:
    _closed_guard(f)
    f.status, f.closed_at, f.closed_by = F.CLOSED.value, datetime.now(UTC), user.id
    _updated(db, f, user, "close")


def _allowed(f: FollowUpRequest, user: User) -> list[str]:
    if f.status == F.CLOSED.value:
        return []
    if user.role == "SELLER":
        return {
            F.REQUESTED.value: ["accept", "reject", "respond", "close"],
            F.IN_PROGRESS.value: ["respond", "close"],
            F.RESPONDED.value: ["close"],
        }[f.status]
    return ["messages", "close"]


def out(db: Session, f: FollowUpRequest, user: User, with_messages: bool = False) -> dict:
    names = {}

    def name(uid):
        if uid not in names:
            u = db.get(User, uid)
            names[uid] = (u.display_name, db.get(Organization, u.organization_id).name) if u else ("?", "")
        return names[uid]

    a = db.get(Assessment, f.assessment_id)
    d = {
        "id": str(f.id),
        "assessment_id": str(f.assessment_id),
        "assessment_title": a.title if a else None,
        "seller_org": db.get(Organization, f.seller_org_id).name,
        "seller_org_id": str(f.seller_org_id),
        "requested_by": name(f.requested_by)[0],
        "buyer_org": name(f.requested_by)[1],
        "subject": f.subject,
        "related_requirement_ids": f.related_requirement_ids,
        "status": f.status,
        "seller_decision": f.seller_decision,
        "decision_reason": f.decision_reason,
        "assigned_owner": name(f.assigned_owner_user_id)[0] if f.assigned_owner_user_id else None,
        "created_at": f.created_at,
        "updated_at": f.updated_at,
        "closed_at": f.closed_at,
        "allowed_actions": _allowed(f, user),
    }
    if with_messages:
        msgs = db.scalars(select(FollowUpMessage).where(FollowUpMessage.follow_up_id == f.id).order_by(FollowUpMessage.created_at)).all()
        d["messages"] = [
            {
                "id": str(m.id),
                "author": name(m.author_user_id)[0],
                "author_org": name(m.author_user_id)[1],
                "author_role": m.author_role,
                "body": m.body,
                "created_at": m.created_at,
            }
            for m in msgs
        ]
    return d
