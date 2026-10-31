"""Assess one requirement: retrieve, judge, apply guardrails (§10.8 step 3). No database access (thread-safe)."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.config import get_settings
from app.core.enums import CATEGORY_LABELS
from app.core.errors import ReindexRequired
from app.core.runtime import STATE
from app.prompts import judge as P
from app.services.assessment.guardrails import DEFAULT_MISSING, apply_guardrails
from app.services.embeddings.embedder import get_embedder
from app.services.llm.client import get_llm
from app.services.retrieval.search import LABELS, search_vector

KEEP = 8


@dataclass
class Assessed:
    requirement: dict
    status: str
    explanation: dict
    supported_part: str | None = None
    unestablished_part: str | None = None
    assumptions: list[str] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)
    questions_for_seller: list[str] = field(default_factory=list)
    has_conflict: bool = False
    conflict_description: str | None = None
    guardrail_notes: list[str] = field(default_factory=list)
    retrieval_summary: dict = field(default_factory=dict)
    evidence: list[dict] = field(default_factory=list)
    model: str | None = None
    prompt_version: str | None = None


def retrieve_for(requirement: dict) -> list[dict]:
    if STATE.reindex_required:
        raise ReindexRequired()
    s = get_settings()
    text = requirement["normalized_text"]
    queries = [text, f"{CATEGORY_LABELS.get(requirement['category'], 'Other')}: {text}"]
    vectors = [get_embedder().embed_query(q) for q in queries]
    best: dict[str, dict] = {}
    for v in vectors:
        r = search_vector(v, 6, 4, s.RETRIEVAL_MIN_SCORE, keep=20)
        for c in r.kept:
            prev = best.get(c["chunk_id"])
            if prev is None or c["score"] > prev["score"]:
                best[c["chunk_id"]] = c
    ranked = sorted(best.values(), key=lambda c: c["score"], reverse=True)[:KEEP]
    for i, c in enumerate(ranked, start=1):
        c["n"] = i
    return ranked


def assess_requirement(requirement: dict) -> Assessed:
    chunks = retrieve_for(requirement)
    summary = {
        "candidate_count": len(chunks),
        "top_official_score": max((c["score"] for c in chunks if c["collection"] == "OFFICIAL"), default=None),
        "top_resolved_score": max((c["score"] for c in chunks if c["collection"] == "RESOLVED"), default=None),
    }
    if not chunks:
        return Assessed(
            requirement=requirement,
            status="UNKNOWN",
            explanation={
                "meaning": requirement["normalized_text"],
                "established": "No relevant product knowledge was retrieved.",
                "unverified": "Whether the product meets this requirement.",
                "next_step": "Ask the product team through the chatbot, or request clarification from the seller",
            },
            missing_information=["Product documentation covering this requirement"],
            guardrail_notes=["no_candidates"],
            retrieval_summary=summary,
        )
    s = get_settings()
    j = get_llm().complete_structured("main", P.SYSTEM, P.build_messages(requirement, chunks), P.RequirementJudgement, P.TOOL, 1500, 0.0)
    by_n = {c["n"]: c for c in chunks}
    g = apply_guardrails(j, by_n, requirement["normalized_text"], requirement["category"], requirement.get("clarification_waived", False))
    evidence = []
    for rank, e in enumerate(g.evidence, start=1):
        c = by_n[e.chunk_number]
        evidence.append(
            {
                "rank": rank,
                "role": e.role,
                "collection": c["collection"],
                "knowledge_id": c["knowledge_id"],
                "chunk_id": c["chunk_id"],
                "source_title": c["title"],
                "heading_path": c["heading_path"],
                "source_url": c["source_url"],
                "source_document": c["source_document"],
                "source_label": LABELS[c["collection"]],
                "excerpt": e.quote,
                "knowledge_version": c.get("version"),
                "last_verified_at": c.get("last_verified_at") or c.get("approved_at"),
                "relevance_score": c["score"],
            }
        )
    partial = g.status == "PARTIALLY_SUPPORTED"
    return Assessed(
        requirement=requirement,
        status=g.status,
        explanation={
            "meaning": j.meaning,
            "established": j.established if evidence else "No cited excerpt establishes this requirement.",
            "unverified": j.unverified,
            "next_step": g.next_step,
        },
        supported_part=j.supported_part if partial else None,
        unestablished_part=j.unestablished_part if partial else None,
        assumptions=[a for a in j.assumptions if a.strip()],
        missing_information=g.missing_information or ([DEFAULT_MISSING] if g.status == "UNKNOWN" else []),
        questions_for_seller=[q for q in j.questions_for_seller if q.strip()],
        has_conflict=g.has_conflict,
        conflict_description=g.conflict_description,
        guardrail_notes=g.notes,
        retrieval_summary=summary,
        evidence=evidence,
        model=s.LLM_MODEL,
        prompt_version=P.PROMPT_VERSION,
    )
