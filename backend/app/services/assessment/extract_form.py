"""Guided requirement form (§10.6). Resubmission is field-wise: only changed fields are re-processed."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import RequirementSource
from app.core.errors import AppError
from app.models.assessment import Assessment, Requirement
from app.prompts import extract_pdf as P
from app.services.assessment import requirement_service as RS
from app.services.llm.client import get_llm

DEPLOYMENT_TEXT = {
    "ON_PREMISES": "on-premises",
    "OWN_CLOUD": "in our own cloud account",
    "HYBRID": "hybrid (on-premises and cloud)",
    "AIR_GAPPED": "air-gapped (isolated, no internet access)",
    "PUBLIC_CLOUD": "public cloud",
}

# field_key -> (label, category hint, mode). mode: llm | deterministic | context
FIELDS: dict[str, tuple[str, str | None, str]] = {
    "organisation_name": ("Organisation", None, "context"),
    "industry": ("Industry", None, "context"),
    "use_case": ("Intended use case", "FUNCTIONAL_CAPABILITY", "llm"),
    "deployment_preference": ("Deployment preference", "DEPLOYMENT_INFRASTRUCTURE", "deterministic"),
    "data_sovereignty": ("Data sovereignty and residency", "DATA_SOVEREIGNTY_RESIDENCY", "llm"),
    "data_scale": ("Data volume or scale", "PERFORMANCE_SCALABILITY", "deterministic"),
    "existing_technologies": ("Existing data technologies and integrations", "INTEGRATION_COMPATIBILITY", "llm"),
    "security_access": ("Security and access-control needs", "SECURITY_ACCESS_CONTROL", "llm"),
    "compliance": ("Compliance or certification requirements", "COMPLIANCE_GOVERNANCE", "llm"),
    "performance_availability": ("Performance and availability expectations", None, "llm"),
    "budget_operations": ("Budget or operational constraints", "COST_OPERATIONS", "llm"),
    "other": ("Other requirements", None, "llm"),
}
PERF_HINT = "Use category PERFORMANCE_SCALABILITY or AVAILABILITY_RELIABILITY."


def _value(form: dict, key: str) -> str:
    v = form.get(key)
    return v.strip() if isinstance(v, str) else ""


def _priority(form: dict, key: str) -> str:
    return (form.get("priorities") or {}).get(key) or "NOT_SPECIFIED"


def submit(db: Session, a: Assessment, user, form: dict) -> dict:
    if not _value(form, "use_case"):
        raise AppError("VALIDATION_ERROR", "Intended use case is required.", 422)
    previous = a.intake_form or {}
    actor = RS.Actor(user, "FORM")
    ctx = dict(a.context or {})
    for k in ("organisation_name", "industry", "use_case"):
        if _value(form, k):
            ctx[k] = _value(form, k)
        else:
            ctx.pop(k, None)
    a.context = ctx
    created = removed = 0
    changed_fields = []
    for key, (label, cat, mode) in FIELDS.items():
        if mode == "context":
            continue
        new_v, old_v = _value(form, key), _value(previous, key)
        new_p, old_p = _priority(form, key), _priority(previous, key)
        if new_v == old_v and new_p == old_p:
            continue  # unchanged field: no action
        changed_fields.append(key)
        # Remove requirements previously created from this field.
        olds = db.scalars(
            select(Requirement).where(
                Requirement.assessment_id == a.id,
                Requirement.source_type == RequirementSource.FORM.value,
                Requirement.is_removed.is_(False),
                Requirement.source_reference["field_key"].astext == key,
            )
        ).all()
        for r in olds:
            RS.remove(db, a, r.id, actor, reason="form field changed")
            removed += 1
        if not new_v:
            continue  # cleared field
        ref = {"field_key": key, "field_label": label}
        if mode == "deterministic":
            if key == "deployment_preference":
                if new_v == "UNDECIDED" or new_v not in DEPLOYMENT_TEXT:
                    continue
                text = f"Deployment preference: {DEPLOYMENT_TEXT[new_v]}."
            else:
                text = f"Data volume or scale: {new_v.rstrip('.')}."
            RS.create(
                db,
                a,
                actor,
                original_text=text,
                normalized_text=text,
                category=cat,
                priority=new_p,
                source_type="FORM",
                source_reference=ref,
            )
            created += 1
            continue
        hint = f"Source: guided form field '{label}' (field_key {key})."
        hint += (
            f" Use category {cat} unless clearly wrong."
            if cat
            else (f" {PERF_HINT}" if key == "performance_availability" else " Choose the category.")
        )
        result = get_llm().complete_structured("main", P.SYSTEM, P.build_messages(new_v, hint), P.ExtractionResult, P.TOOL, 3000, 0.0)
        for item in result.requirements:
            category = cat or item.category
            if key == "performance_availability" and item.category not in ("PERFORMANCE_SCALABILITY", "AVAILABILITY_RELIABILITY"):
                category = "PERFORMANCE_SCALABILITY"
            RS.create(
                db,
                a,
                actor,
                original_text=item.original_text[:500],
                normalized_text=item.normalized_text,
                category=category,
                priority=new_p,
                priority_basis="Set in the guided form" if new_p != "NOT_SPECIFIED" else None,
                source_type="FORM",
                source_reference=ref,
                needs_clarification=item.needs_clarification,
                clarifying_question=item.clarifying_question,
            )
            created += 1
    a.intake_form = form
    db.commit()
    return {"created": created, "removed": removed, "changed_fields": changed_fields}
