"""Builds the results payload shared by the buyer results view, the seller view and the PDF report."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import TicketStatus
from app.models.assessment import Assessment, AssessmentVersion, EvidenceReference, RequirementAssessment
from app.models.chat import Ticket
from app.services.assessment.versions import changes_since_previous
from app.services.knowledge.state import current_epoch

FINAL_TICKETS = {TicketStatus.PUBLISHED.value, TicketStatus.CLOSED.value, TicketStatus.REJECTED.value}


def evidence_out(e: EvidenceReference, include_score: bool = False) -> dict:
    d = {
        "rank": e.rank,
        "role": e.role,
        "collection": e.collection,
        "label": e.source_label,
        "knowledge_id": e.knowledge_id,
        "chunk_id": e.chunk_id,
        "title": e.source_title,
        "heading_path": e.heading_path,
        "source_url": e.source_url,
        "source_document": e.source_document,
        "excerpt": e.excerpt,
        "version": e.knowledge_version,
        "last_verified_at": e.last_verified_at if e.collection == "OFFICIAL" else None,
        "approved_at": e.last_verified_at if e.collection == "RESOLVED" else None,
    }
    if include_score:
        d["relevance_score"] = e.relevance_score
    return d


def build_results(db: Session, a: Assessment, v: AssessmentVersion, *, viewer: str = "BUYER", include_tickets: bool = True) -> dict:
    ras = db.scalars(select(RequirementAssessment).where(RequirementAssessment.version_id == v.id)).all()
    by_req = {str(r.requirement_id): r for r in ras}
    ev = {}
    for e in db.scalars(
        select(EvidenceReference)
        .where(EvidenceReference.requirement_assessment_id.in_([r.id for r in ras]))
        .order_by(EvidenceReference.rank)
    ):
        ev.setdefault(e.requirement_assessment_id, []).append(evidence_out(e, include_score=viewer == "ADMIN"))
    tickets: dict[str, list[Ticket]] = {}
    if include_tickets:
        for t in db.scalars(select(Ticket).where(Ticket.assessment_id == a.id, Ticket.requirement_id.is_not(None))):
            tickets.setdefault(str(t.requirement_id), []).append(t)
    responses = _seller_responses(db, a, v)
    items = []
    for snap in v.requirements_snapshot:
        ra = by_req.get(snap["id"])
        if ra is None:
            continue
        ts = tickets.get(snap["id"], [])
        open_t = next((t for t in ts if t.status not in FINAL_TICKETS), None)
        answered = any(t.status == TicketStatus.PUBLISHED.value and t.resolved_at and t.resolved_at > v.analyzed_at for t in ts)
        items.append(
            {
                "requirement_id": snap["id"],
                "display_id": ra.display_id,
                "text": ra.requirement_text,
                "original_text": snap.get("original_text"),
                "category": ra.category,
                "priority": ra.priority,
                "source_type": snap.get("source_type"),
                "source_quote": (snap.get("source_reference") or {}).get("quote") or snap.get("original_text"),
                "source_page": (snap.get("source_reference") or {}).get("page"),
                "status": ra.status,
                "explanation": ra.explanation,
                "supported_part": ra.supported_part,
                "unestablished_part": ra.unestablished_part,
                "assumptions": ra.assumptions,
                "missing_information": ra.missing_information,
                "questions_for_seller": ra.questions_for_seller,
                "has_conflict": ra.has_conflict,
                "conflict_description": ra.conflict_description,
                "is_blocker": ra.is_blocker,
                "guardrail_notes": [n for n in ra.guardrail_notes if n != "no_candidates"]
                + (
                    ["No relevant product knowledge was retrieved, so the language model was not asked."]
                    if "no_candidates" in ra.guardrail_notes
                    else []
                ),
                "candidate_count": (ra.retrieval_summary or {}).get("candidate_count"),
                "evidence": ev.get(ra.id, []),
                "open_ticket": {"id": str(open_t.id), "display_id": open_t.display_id, "status": open_t.status}
                if (open_t and include_tickets)
                else None,
                "answer_available": answered if include_tickets else False,
                "seller_responses": responses.get(snap["id"], []),
            }
        )
    return {
        "assessment": {
            "id": str(a.id),
            "title": a.title,
            "status": a.status,
            "context": {k: a.context.get(k) for k in ("organisation_name", "industry", "use_case") if a.context.get(k)},
        },
        "version": {
            "version_no": v.version_no,
            "analyzed_at": v.analyzed_at,
            "requirement_set_revision": v.requirement_set_revision,
            "knowledge_epoch": v.knowledge_epoch,
            "model": v.model,
            "prompt_versions": v.prompt_versions,
        },
        "summary": v.summary,
        "knowledge_updated": current_epoch(db) > v.knowledge_epoch,
        "changes_since_previous": changes_since_previous(db, v),
        "requirements": items,
    }


def _seller_responses(db: Session, a: Assessment, v: AssessmentVersion) -> dict[str, list[dict]]:
    try:
        from app.services.sharing.seller_service import responses_for_version
    except ImportError:
        return {}
    return responses_for_version(db, a, v)
