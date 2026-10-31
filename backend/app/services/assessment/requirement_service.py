"""RequirementService: the only code allowed to create, change, confirm or remove requirements (§10.3).

Every mutation, in the caller's transaction: validates input, writes a requirement_revisions row, increments
assessments.requirement_set_revision, turns ANALYZED into STALE, and writes an audit event.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import AssessmentStatus, AuditAction, Priority, RequirementCategory
from app.core.errors import AppError, invalid_state, not_found
from app.models.assessment import Assessment, Requirement, RequirementRevision
from app.services.audit import audit

MAX_ACTIVE = 100
EDITABLE = ("normalized_text", "category", "priority")


@dataclass
class Actor:
    """Who caused a change. user may be None for SYSTEM-origin changes."""

    user: object | None
    origin: str  # UI | CHAT | FORM | PDF | SYSTEM


def _check_text(text: str) -> str:
    t = (text or "").strip()
    if not 5 <= len(t) <= 1000:
        raise AppError("VALIDATION_ERROR", "Requirement text must be between 5 and 1,000 characters.", 422)
    return t


def _check_enum(value: str, enum_cls, field: str) -> str:
    if value not in {m.value for m in enum_cls}:
        raise AppError("VALIDATION_ERROR", f"Invalid {field}: {value}.", 422)
    return value


def lock_assessment(db: Session, assessment_id: uuid.UUID) -> Assessment:
    a = db.scalar(select(Assessment).where(Assessment.id == assessment_id).with_for_update())
    if a is None:
        raise not_found("Assessment")
    if a.status == AssessmentStatus.ANALYZING.value:
        raise AppError("JOB_IN_PROGRESS", "An assessment run is in progress. Wait for it to finish before changing requirements.", 409)
    return a


def _bump(db: Session, a: Assessment) -> None:
    a.requirement_set_revision += 1
    if a.status == AssessmentStatus.ANALYZED.value:
        a.status = AssessmentStatus.STALE.value


def _revision(db: Session, a: Assessment, r: Requirement, change_type: str, changes: dict, actor: Actor) -> None:
    n = (db.scalar(select(func.max(RequirementRevision.revision_no)).where(RequirementRevision.requirement_id == r.id)) or 0) + 1
    db.add(
        RequirementRevision(
            requirement_id=r.id,
            revision_no=n,
            change_type=change_type,
            changes=changes,
            actor_user_id=getattr(actor.user, "id", None),
            actor_role=getattr(actor.user, "role", None) or "SYSTEM",
            origin=actor.origin,
            assessment_revision=a.requirement_set_revision,
        )
    )


def active_count(db: Session, assessment_id: uuid.UUID) -> int:
    return (
        db.scalar(select(func.count(Requirement.id)).where(Requirement.assessment_id == assessment_id, Requirement.is_removed.is_(False)))
        or 0
    )


def create(
    db: Session,
    a: Assessment,
    actor: Actor,
    *,
    original_text: str,
    normalized_text: str,
    category: str,
    priority: str = Priority.NOT_SPECIFIED.value,
    priority_basis: str | None = None,
    source_type: str,
    source_reference: dict | None = None,
    buyer_confirmed: bool = False,
    needs_clarification: bool = False,
    clarifying_question: str | None = None,
) -> Requirement:
    if active_count(db, a.id) >= MAX_ACTIVE:
        raise AppError("VALIDATION_ERROR", f"An assessment can have at most {MAX_ACTIVE} active requirements.", 422)
    norm = _check_text(normalized_text)
    orig = (original_text or norm).strip()[:2000]
    _check_enum(category, RequirementCategory, "category")
    _check_enum(priority, Priority, "priority")
    seq = a.next_req_seq
    a.next_req_seq += 1  # sequence numbers are never reused
    r = Requirement(
        id=uuid.uuid4(),
        assessment_id=a.id,
        seq=seq,
        display_id=f"REQ-{seq:03d}",
        original_text=orig,
        normalized_text=norm,
        category=category,
        priority=priority,
        priority_basis=priority_basis,
        source_type=source_type,
        source_reference=source_reference or {},
        buyer_confirmed=buyer_confirmed and not needs_clarification,
        needs_clarification=needs_clarification,
        clarifying_question=clarifying_question if needs_clarification else None,
    )
    db.add(r)
    db.flush()
    _bump(db, a)
    _revision(
        db,
        a,
        r,
        "CREATED",
        {k: {"before": None, "after": getattr(r, k)} for k in ("normalized_text", "category", "priority", "buyer_confirmed")},
        actor,
    )
    audit(db, AuditAction.REQUIREMENT_CREATED, "requirement", r.id, actor.user, {"display_id": r.display_id, "origin": actor.origin})
    return r


def _get(db: Session, a: Assessment, requirement_id) -> Requirement:
    r = db.get(Requirement, requirement_id)
    if r is None or r.assessment_id != a.id:
        raise not_found("Requirement")
    return r


def edit(db: Session, a: Assessment, requirement_id, actor: Actor, **fields) -> Requirement:
    """Buyer edit of normalized_text / category / priority. Any buyer edit confirms the requirement and clears
    the clarification flag. original_text is immutable."""
    if "original_text" in fields:
        raise AppError("VALIDATION_ERROR", "original_text cannot be changed.", 422)
    r = _get(db, a, requirement_id)
    if r.is_removed:
        raise invalid_state("Restore the requirement before editing it.", ["restore"])
    changes = {}
    for k, v in fields.items():
        if k not in EDITABLE or v is None:
            continue
        if k == "normalized_text":
            v = _check_text(v)
        elif k == "category":
            _check_enum(v, RequirementCategory, "category")
        elif k == "priority":
            _check_enum(v, Priority, "priority")
            r.priority_basis = "Set by the buyer"
        if getattr(r, k) != v:
            changes[k] = {"before": getattr(r, k), "after": v}
            setattr(r, k, v)
    if not changes and r.buyer_confirmed and not r.needs_clarification:
        return r
    for flag, value in (("buyer_confirmed", True), ("needs_clarification", False)):
        if getattr(r, flag) != value:
            changes[flag] = {"before": getattr(r, flag), "after": value}
            setattr(r, flag, value)
    _bump(db, a)
    _revision(db, a, r, "EDITED", changes, actor)
    audit(db, AuditAction.REQUIREMENT_EDITED, "requirement", r.id, actor.user, {"display_id": r.display_id, "fields": sorted(changes)})
    db.flush()
    return r


def confirm(db: Session, a: Assessment, requirement_id, actor: Actor) -> Requirement:
    r = _get(db, a, requirement_id)
    if r.is_removed:
        raise invalid_state("A removed requirement cannot be confirmed.", ["restore"])
    if r.needs_clarification and not r.clarification_waived:
        raise AppError(
            "VALIDATION_ERROR",
            "This requirement needs clarification. Edit it, or choose 'Keep as written', before confirming.",
            422,
            {"clarifying_question": r.clarifying_question},
        )
    if r.buyer_confirmed:
        return r
    r.buyer_confirmed = True
    _bump(db, a)
    _revision(db, a, r, "CONFIRMED", {"buyer_confirmed": {"before": False, "after": True}}, actor)
    audit(db, AuditAction.REQUIREMENT_CONFIRMED, "requirement", r.id, actor.user, {"display_id": r.display_id})
    db.flush()
    return r


def waive_clarification(db: Session, a: Assessment, requirement_id, actor: Actor) -> Requirement:
    """'Keep as written': the buyer accepts the wording; it can then be confirmed (it is treated as vague in analysis)."""
    r = _get(db, a, requirement_id)
    if not r.needs_clarification:
        raise invalid_state("This requirement does not need clarification.")
    if r.clarification_waived:
        return r
    r.clarification_waived = True
    _bump(db, a)
    _revision(db, a, r, "CLARIFICATION_WAIVED", {"clarification_waived": {"before": False, "after": True}}, actor)
    audit(db, AuditAction.REQUIREMENT_EDITED, "requirement", r.id, actor.user, {"display_id": r.display_id, "waived": True})
    db.flush()
    return r


def remove(db: Session, a: Assessment, requirement_id, actor: Actor, reason: str | None = None) -> Requirement:
    r = _get(db, a, requirement_id)
    if r.is_removed:
        return r
    r.is_removed, r.removed_at = True, datetime.now(UTC)
    _bump(db, a)
    _revision(db, a, r, "REMOVED", {"is_removed": {"before": False, "after": True}} | ({"reason": reason} if reason else {}), actor)
    audit(db, AuditAction.REQUIREMENT_REMOVED, "requirement", r.id, actor.user, {"display_id": r.display_id, "reason": reason})
    db.flush()
    return r


def restore(db: Session, a: Assessment, requirement_id, actor: Actor) -> Requirement:
    r = _get(db, a, requirement_id)
    if not r.is_removed:
        return r
    if active_count(db, a.id) >= MAX_ACTIVE:
        raise AppError("VALIDATION_ERROR", f"An assessment can have at most {MAX_ACTIVE} active requirements.", 422)
    r.is_removed, r.removed_at = False, None
    _bump(db, a)
    _revision(db, a, r, "RESTORED", {"is_removed": {"before": True, "after": False}}, actor)
    audit(db, AuditAction.REQUIREMENT_EDITED, "requirement", r.id, actor.user, {"display_id": r.display_id, "restored": True})
    db.flush()
    return r


def confirm_all(db: Session, a: Assessment, actor: Actor) -> list[Requirement]:
    """Confirms every active, unconfirmed requirement that does not still need clarification."""
    rows = db.scalars(
        select(Requirement).where(
            Requirement.assessment_id == a.id, Requirement.is_removed.is_(False), Requirement.buyer_confirmed.is_(False)
        )
    ).all()
    done = []
    for r in rows:
        if r.needs_clarification and not r.clarification_waived:
            continue
        done.append(confirm(db, a, r.id, actor))
    return done
