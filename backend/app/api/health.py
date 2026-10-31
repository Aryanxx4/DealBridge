from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.core.runtime import STATE, check_vectors
from app.db.session import session_factory
from app.services.embeddings.embedder import get_embedder
from app.services.vector.qdrant_store import get_store

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    s = get_settings()
    pg_ok = True
    try:
        with session_factory()() as db:
            db.execute(text("SELECT 1"))
            if not STATE.qdrant_checked:
                check_vectors(db)
    except Exception:
        pg_ok = False
    qdrant_ok = get_store().ping()
    emb = get_embedder()
    deps = {
        "postgres": {"ok": pg_ok},
        "qdrant": {"ok": qdrant_ok},
        "embedding_model": {"ok": emb.loaded, "model": s.EMBEDDING_MODEL, "error": emb.load_error},
        "llm": {"configured": s.llm_configured, "provider": s.LLM_PROVIDER},
    }
    degraded = not (pg_ok and qdrant_ok and emb.loaded and s.llm_configured) or STATE.reindex_required
    return {
        "status": "degraded" if degraded else "ok",
        "dependencies": deps,
        "reindex_required": STATE.reindex_required,
        "reindex_problems": STATE.reindex_problems,
        "embedding_loading": (not emb.loaded) and emb.load_error is None,
    }
