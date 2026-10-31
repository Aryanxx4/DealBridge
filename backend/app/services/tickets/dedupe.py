"""Duplicate detection for unanswered questions (§9.4 step 2b)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import TicketStatus
from app.models.chat import Ticket
from app.prompts import ticket_dup
from app.services.embeddings.embedder import cosine
from app.services.llm.client import get_llm

DEDUPE_STATUSES = [TicketStatus.OPEN, TicketStatus.IN_REVIEW, TicketStatus.ANSWER_PROPOSED, TicketStatus.APPROVED]


def best_open_match(db: Session, vector: list[float]) -> tuple[Ticket | None, float]:
    best, best_score = None, -1.0
    rows = db.scalars(select(Ticket).where(Ticket.status.in_([s.value for s in DEDUPE_STATUSES]), Ticket.question_embedding.is_not(None)))
    for t in rows:
        score = cosine(vector, list(t.question_embedding))
        if score > best_score:
            best, best_score = t, score
    return best, best_score


def find_duplicate(db: Session, normalised_question: str, vector: list[float]) -> tuple[Ticket | None, dict]:
    """Returns (ticket to link to or None, trace). Similar embeddings alone never merge questions."""
    s = get_settings()
    cand, score = best_open_match(db, vector)
    trace: dict = {
        "best_ticket": cand.display_id if cand else None,
        "score": round(score, 4) if cand else None,
        "threshold": s.TICKET_DUP_MIN_SCORE,
    }
    if cand is None or score < s.TICKET_DUP_MIN_SCORE:
        trace["decision"] = "no_candidate_above_threshold"
        return None, trace
    verdict = get_llm().complete_structured(
        "fast",
        ticket_dup.SYSTEM,
        ticket_dup.build_messages(normalised_question, cand.normalised_question),
        ticket_dup.TicketDupResult,
        ticket_dup.TOOL,
        200,
        0.0,
    )
    trace.update({"same_intent": verdict.same_intent, "differing_qualifiers": verdict.differing_qualifiers})
    if verdict.same_intent and not verdict.differing_qualifiers:
        trace["decision"] = "linked"
        return cand, trace
    trace["decision"] = "different_intent_or_qualifiers"
    return None, trace
