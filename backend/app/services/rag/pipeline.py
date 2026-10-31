"""Grounded product Q&A pipeline (build prompt §9.2).

classify -> route -> retrieve -> generate -> verify quotes deterministically -> faithfulness check -> decide -> persist.
Infrastructure failures raise 503 errors and never create tickets (§9.3).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import AnswerType, TicketReason
from app.models.chat import Conversation, Message, Ticket
from app.models.identity import User
from app.prompts import answer as answer_prompt
from app.prompts import classify as classify_prompt
from app.prompts import faithfulness as faith_prompt
from app.prompts import ticket_dup as dup_prompt
from app.prompts.answer import AnswerDraft
from app.services.rag import answer as answer_mod
from app.services.rag import classify as classify_mod
from app.services.rag import faithfulness as faith_mod
from app.services.retrieval.evidence import citation
from app.services.retrieval.quote_verify import contains_term, verify_quote
from app.services.retrieval.search import retrieve
from app.services.tickets.ticket_service import raise_ticket

log = logging.getLogger("dealbridge.rag")

MAX_QUESTION_CHARS = 2000
PRIVACY_FOOTER = "Questions I cannot verify are shared with the product team for review. Your assessments and documents are not shared."

CAPABILITIES = (
    "I can help with questions about IOMETE: deployment options, architecture, security and access control, "
    "platform features, and integrations. To evaluate your own requirements, use an assessment."
)


@dataclass
class Outcome:
    content: str
    answer_type: str
    citations: list[dict] = field(default_factory=list)
    ticket: Ticket | None = None
    ticket_linked: bool = False
    structured: dict = field(default_factory=dict)
    trace: dict = field(default_factory=dict)


def _history(db: Session, conversation: Conversation, exclude_id) -> list[dict]:
    msgs = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation.id, Message.id != exclude_id)
        .order_by(Message.created_at.desc())
        .limit(6)
    ).all()
    return [{"role": m.role, "content": m.content} for m in reversed(msgs)]


def _verify_claims(draft: AnswerDraft, by_n: dict[int, dict]) -> tuple[list, list]:
    ok, failed = [], []
    for c in draft.product_claims:
        chunk = by_n.get(c.chunk_number)
        (ok if chunk and verify_quote(chunk["text"], c.supporting_quote) else failed).append(c)
    return ok, failed


def _ticket_message(t: Ticket, linked: bool, conflict: bool) -> str:
    status = t.status.replace("_", " ").title()
    lead = (
        "The available sources disagree on this, so I can't give a verified answer."
        if conflict
        else "I couldn't verify an answer to this from the available product knowledge, so I haven't guessed."
    )
    if linked:
        return f"{lead} A matching question is already with the product team: **{t.display_id}** (status: {status}). You can follow it under My questions."
    return f"{lead} I've raised it with the product team for review: **{t.display_id}** (status: {status}). You can follow it under My questions."


def answer_question(db: Session, user: User, conversation: Conversation, question: str, user_message: Message) -> Outcome:
    s = get_settings()
    versions = {"classify": classify_prompt.PROMPT_VERSION}
    history = _history(db, conversation, user_message.id)
    cls = classify_mod.classify(history, question)
    trace: dict = {"classification": cls.model_dump()}
    structured: dict = {"classification": cls.model_dump(), "prompt_versions": versions}

    if cls.intent == "SMALL_TALK":
        return Outcome(
            "Hello! Ask me anything about IOMETE's deployment, architecture, security or integrations.",
            AnswerType.SMALL_TALK,
            structured=structured,
            trace=trace,
        )
    if cls.intent == "OUT_OF_SCOPE":
        return Outcome(
            f"That's outside what DealBridge covers. {CAPABILITIES}", AnswerType.OUT_OF_SCOPE, structured=structured, trace=trace
        )
    if cls.intent == "REQUIREMENT_STATEMENT":
        structured["action"] = {
            "type": "OPEN_ASSESSMENT",
            "assessment_id": str(conversation.assessment_id) if conversation.assessment_id else None,
        }
        return Outcome(
            "That sounds like one of your requirements. Requirements are best captured in an assessment, where each one is checked "
            "against the documentation with cited evidence.",
            AnswerType.REDIRECT,
            structured=structured,
            trace=trace,
        )

    standalone = cls.standalone_question.strip() or question
    retrieved, _ = retrieve(standalone)
    trace.update({"thresholds": retrieved.thresholds, "hits": retrieved.trace_hits, "kept": [c["chunk_id"] for c in retrieved.kept]})
    by_n = {c["n"]: c for c in retrieved.kept}
    product = cls.intent == "PRODUCT_SPECIFIC"
    reason = TicketReason.NO_EVIDENCE

    draft: AnswerDraft | None = None
    verified: list = []
    if retrieved.kept or not product:
        versions["answer"] = answer_prompt.PROMPT_VERSION
        draft = answer_mod.generate(standalone, retrieved.kept)
        verified, failed = _verify_claims(draft, by_n)
        if failed:
            trace["failed_claims_first_try"] = [f.model_dump() for f in failed]
            feedback = "\n".join(f"- chunk [{f.chunk_number}]: {f.supporting_quote!r}" for f in failed)
            draft = answer_mod.generate(standalone, retrieved.kept, feedback)
            verified, failed = _verify_claims(draft, by_n)
            if failed:
                trace["failed_claims_retry"] = [f.model_dump() for f in failed]
                trace["decision"] = "discarded: unverifiable quotes after retry"
                draft = draft.model_copy(update={"answerability": "NONE", "answer_markdown": ""})
                verified = []
                reason = TicketReason.WEAK_EVIDENCE
    answerability = draft.answerability if draft else "NONE"

    if draft and answerability != "NONE" and cls.mentions_certification:
        terms = cls.certification_terms or []
        explicit = any(any(contains_term(by_n[c.chunk_number]["text"], t) for t in terms) for c in verified) if terms else False
        if not explicit:
            answerability, reason = "NONE", TicketReason.WEAK_EVIDENCE
            trace["decision"] = "certification not named explicitly in any verified chunk"
    if product and answerability != "NONE" and not verified:
        answerability, reason = "NONE", TicketReason.WEAK_EVIDENCE
        trace["decision"] = "product question without verified claims"

    cited_ns = sorted({c.chunk_number for c in verified})
    cited_chunks = [by_n[n] for n in cited_ns]
    if draft and answerability in ("FULL", "PARTIAL") and verified and s.ENABLE_FAITHFULNESS_CHECK:
        versions["faithfulness"] = faith_prompt.PROMPT_VERSION
        f = faith_mod.check(draft.answer_markdown, cited_chunks)
        trace["faithfulness"] = f.model_dump()
        if not f.faithful:
            answerability, reason = "NONE", TicketReason.WEAK_EVIDENCE
            trace["decision"] = "faithfulness check failed"

    # Resolved answers that scored as reusable but were not relied on (e.g. qualifier mismatch) are linked to the ticket.
    related = [c["knowledge_id"] for c in retrieved.kept if c.get("reuse_candidate") and c["n"] not in cited_ns and c.get("knowledge_id")]
    conflict = bool(draft and draft.conflict)
    quotes = {}
    for c in verified:
        quotes.setdefault(c.chunk_number, c.supporting_quote)
    citations = [citation(by_n[n], quotes[n]) for n in cited_ns]
    general = draft.general_explanation_markdown if draft else None
    structured.update(
        {
            "general_explanation_markdown": general,
            "unverified_aspects": draft.unverified_aspects if draft else [],
            "conflict_note": draft.conflict_note if draft else None,
            "answerability": answerability,
        }
    )

    if conflict:
        reason = TicketReason.CONFLICT
        structured["conflict"] = True
        out = raise_ticket(db, user, conversation, user_message, question, standalone, cls.category, reason, trace, related)
        versions["ticket_dup"] = dup_prompt.PROMPT_VERSION
        shown = draft.answer_markdown if (draft and verified and answerability != "NONE") else ""
        body = shown + "\n\n" + _ticket_message(out.ticket, out.linked, True)
        return Outcome(body.strip(), AnswerType.UNVERIFIED, citations, out.ticket, out.linked, structured, trace)

    if answerability == "FULL" and verified:
        cols = {c["collection"] for c in citations}
        at = (
            AnswerType.OFFICIAL_VERIFIED
            if cols == {"OFFICIAL"}
            else AnswerType.EXPERT_VERIFIED
            if cols == {"RESOLVED"}
            else AnswerType.MIXED_VERIFIED
        )
        trace.setdefault("decision", "answered with verified citations")
        return Outcome(draft.answer_markdown, at, citations, structured=structured, trace=trace)
    if answerability == "PARTIAL" and verified:
        trace.setdefault("decision", "partially answered")
        return Outcome(draft.answer_markdown, AnswerType.PARTIAL, citations, structured=structured, trace=trace)
    if not product:
        # General question: allowed without product evidence, clearly labelled as general.
        trace.setdefault("decision", "general explanation")
        body = general or (draft.answer_markdown if draft else "") or "I don't have a general explanation for that."
        structured["general_explanation_markdown"] = None
        return Outcome(body, AnswerType.GENERAL_EXPLANATION, [], structured=structured, trace=trace)

    trace.setdefault("decision", "no verified evidence: ticket")
    versions["ticket_dup"] = dup_prompt.PROMPT_VERSION
    out = raise_ticket(db, user, conversation, user_message, question, standalone, cls.category, reason, trace, related)
    return Outcome(_ticket_message(out.ticket, out.linked, False), AnswerType.UNVERIFIED, [], out.ticket, out.linked, structured, trace)
