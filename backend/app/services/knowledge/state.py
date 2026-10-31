"""Knowledge epoch and vector-collection bookkeeping."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.system import KnowledgeState, VectorCollection


def ensure_state(db: Session) -> KnowledgeState:
    st = db.get(KnowledgeState, 1)
    if st is None:
        st = KnowledgeState(id=1, epoch=0)
        db.add(st)
        db.flush()
    return st


def current_epoch(db: Session) -> int:
    st = db.get(KnowledgeState, 1)
    return st.epoch if st else 0


def bump_epoch(db: Session) -> int:
    ensure_state(db)
    db.execute(update(KnowledgeState).where(KnowledgeState.id == 1).values(epoch=KnowledgeState.epoch + 1))
    db.flush()
    return current_epoch(db)


def record_collection(db: Session, name: str, reindexed: bool = False) -> VectorCollection:
    s = get_settings()
    vc = db.scalar(select(VectorCollection).where(VectorCollection.name == name))
    if vc is None:
        vc = VectorCollection(name=name, embedding_model=s.EMBEDDING_MODEL, dimension=s.EMBEDDING_DIMENSION)
        db.add(vc)
    if reindexed:
        vc.embedding_model = s.EMBEDDING_MODEL
        vc.dimension = s.EMBEDDING_DIMENSION
        vc.last_reindexed_at = datetime.now(UTC)
    db.flush()
    return vc


def reindex_problems(db: Session, store) -> list[str]:
    """Reasons the vector index cannot be trusted with the configured embedding model."""
    s = get_settings()
    problems: list[str] = []
    for name in (store.official, store.resolved):
        cfg = store.collection_config(name)
        if cfg is None:
            problems.append(f"Qdrant collection '{name}' does not exist (run make init-vector).")
            continue
        size, distance = cfg
        if size != s.EMBEDDING_DIMENSION:
            problems.append(f"Collection '{name}' has vector size {size}, expected {s.EMBEDDING_DIMENSION}.")
        if distance.lower() != "cosine":
            problems.append(f"Collection '{name}' uses distance {distance}, expected Cosine.")
        vc = db.scalar(select(VectorCollection).where(VectorCollection.name == name))
        if vc is None:
            problems.append(f"No bookkeeping row for collection '{name}' (run make init-vector).")
        elif vc.embedding_model != s.EMBEDDING_MODEL or vc.dimension != s.EMBEDDING_DIMENSION:
            problems.append(
                f"Collection '{name}' was built with {vc.embedding_model} ({vc.dimension}d); "
                f"configured model is {s.EMBEDDING_MODEL} ({s.EMBEDDING_DIMENSION}d)."
            )
    return problems
