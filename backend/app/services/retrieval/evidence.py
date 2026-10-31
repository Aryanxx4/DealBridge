"""Citation objects returned to clients. Scores are included only for admins (R3)."""

from __future__ import annotations

from app.services.retrieval.search import LABELS


def citation(c: dict, quote: str, include_score: bool = False) -> dict:
    out = {
        "n": c["n"],
        "collection": c["collection"],
        "label": LABELS[c["collection"]],
        "knowledge_id": c["knowledge_id"],
        "chunk_id": c["chunk_id"],
        "title": c["title"],
        "heading_path": c["heading_path"],
        "source_url": c["source_url"],
        "source_document": c["source_document"],
        "excerpt": quote,
        "version": c.get("version"),
        "last_verified_at": c.get("last_verified_at") if c["collection"] == "OFFICIAL" else None,
        "approved_at": c.get("approved_at") if c["collection"] == "RESOLVED" else None,
    }
    if include_score:
        out["relevance_score"] = c.get("score")
    return out


def strip_scores(citations: list[dict]) -> list[dict]:
    return [{k: v for k, v in c.items() if k != "relevance_score"} for c in citations]
