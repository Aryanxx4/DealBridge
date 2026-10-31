"""Retrieval over both knowledge collections with the mandatory approved+ACTIVE filter (§9.2 step 3)."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.config import get_settings
from app.core.errors import ReindexRequired
from app.core.runtime import STATE
from app.services.embeddings.embedder import get_embedder
from app.services.vector.qdrant_store import Hit, get_store

LABELS = {"OFFICIAL": "Official documentation", "RESOLVED": "Expert-verified answer"}


@dataclass
class Retrieved:
    kept: list[dict] = field(default_factory=list)  # numbered candidates passed to the LLM
    trace_hits: list[dict] = field(default_factory=list)  # every hit (admin trace)
    best_resolved: dict | None = None
    thresholds: dict = field(default_factory=dict)


def _candidate(h: Hit) -> dict:
    p = h.payload
    return {
        "collection": h.collection,
        "point_id": h.id,
        "score": round(h.score, 4),
        "label": LABELS[h.collection],
        "knowledge_id": p.get("knowledge_id"),
        "chunk_id": p.get("chunk_id") or h.id,
        "title": p.get("title", ""),
        "heading_path": p.get("heading_path") or p.get("title", ""),
        "source_url": p.get("source_url"),
        "source_document": p.get("source_document"),
        "text": p.get("text", ""),
        "version": p.get("version"),
        "last_verified_at": p.get("last_verified_at"),
        "approved_at": p.get("approved_at"),
        "question_normalised": p.get("question_normalised"),
    }


def search_vector(vector: list[float], top_official: int, top_resolved: int, min_score: float, keep: int = 10) -> Retrieved:
    store = get_store()
    hits = store.search("OFFICIAL", vector, top_official) + store.search("RESOLVED", vector, top_resolved)
    out = Retrieved(thresholds={"retrieval_min_score": min_score})
    for h in hits:
        c = _candidate(h)
        out.trace_hits.append(
            {k: c[k] for k in ("collection", "knowledge_id", "chunk_id", "title", "heading_path", "score")} | {"excerpt": c["text"][:300]}
        )
    passing = sorted((_candidate(h) for h in hits if h.score >= min_score), key=lambda c: c["score"], reverse=True)[:keep]
    for i, c in enumerate(passing, start=1):
        c["n"] = i
    out.kept = passing
    resolved = [c for c in passing if c["collection"] == "RESOLVED"]
    out.best_resolved = resolved[0] if resolved else None
    return out


def retrieve(question: str) -> tuple[Retrieved, list[float]]:
    if STATE.reindex_required:
        raise ReindexRequired()
    s = get_settings()
    vec = get_embedder().embed_query(question)
    r = search_vector(vec, s.TOP_K_OFFICIAL, s.TOP_K_RESOLVED, s.RETRIEVAL_MIN_SCORE)
    r.thresholds["resolved_reuse_min_score"] = s.RESOLVED_REUSE_MIN_SCORE
    for c in r.kept:
        if c["collection"] == "RESOLVED" and c["score"] >= s.RESOLVED_REUSE_MIN_SCORE:
            c["reuse_candidate"] = True
    return r, vec
