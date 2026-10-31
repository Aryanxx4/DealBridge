"""Rebuild both Qdrant collections with the configured embedding model.

- Official: re-ingests the OKF bundle into a recreated collection (ingest_okf --recreate).
- Resolved: recreates the collection and re-embeds every INDEXED knowledge record from PostgreSQL (the source of
  truth), keeping SUPERSEDED and REVOKED points with their validity so the audit trail survives; the mandatory
  filter keeps them out of retrieval.
Updates vector_collections and increments the knowledge epoch. Use after changing EMBEDDING_MODEL or dimension.
"""

import sys

import _bootstrap  # noqa: F401
from sqlalchemy import select

from app.db.session import session_scope
from app.models.knowledge import KnowledgeRecord
from app.services.embeddings.embedder import get_embedder
from app.services.ingestion.okf_ingest import IngestOptions, ingest_bundle
from app.services.knowledge.publish import payload_for
from app.services.knowledge.state import bump_epoch, record_collection
from app.services.vector.qdrant_store import get_store


def main() -> int:
    store, emb = get_store(), get_embedder()
    with session_scope() as db:
        res = ingest_bundle(db, IngestOptions(recreate=True, triggered_by="reindex"))
        print(f"Official: {res.status}, {res.chunks_upserted} chunks upserted from {res.added + res.updated} files")
    with session_scope() as db:
        store.create_collection(store.resolved, recreate=True)
        recs = db.scalars(select(KnowledgeRecord).where(KnowledgeRecord.index_status == "INDEXED")).all()
        for i in range(0, len(recs), 32):
            batch = recs[i : i + 32]
            vecs = emb.embed_documents([f"{r.question_normalised}\n{r.answer}" for r in batch])
            store.upsert(store.resolved, [(str(r.id), v, payload_for(r, db)) for r, v in zip(batch, vecs, strict=True)])
        for r in recs:
            r.embedding_model = emb.model_name
        record_collection(db, store.resolved, reindexed=True)
        bump_epoch(db)
        active = sum(1 for r in recs if r.validity == "ACTIVE")
        print(f"Resolved: {len(recs)} records re-embedded ({active} active)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
