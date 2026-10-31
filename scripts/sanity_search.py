"""Print the top-3 official hits (with raw scores, an admin-only signal) for sample queries."""

import sys

import _bootstrap  # noqa: F401
from sqlalchemy import func, select

from app.db.session import session_scope
from app.models.knowledge import OkfFile
from app.services.embeddings.embedder import get_embedder
from app.services.vector.qdrant_store import get_store

QUERIES = sys.argv[1:] or [
    "Can IOMETE be installed in our own data center?",
    "Does it support single sign-on with Okta?",
    "Can we restrict access to specific columns?",
    "Which BI tools can connect?",
    "How does it scale when data grows?",
]

if __name__ == "__main__":
    store, emb = get_store(), get_embedder()
    with session_scope() as db:
        pg_chunks = db.scalar(select(func.coalesce(func.sum(OkfFile.chunk_count), 0)).where(OkfFile.status == "INDEXED"))
    print(
        f"Qdrant points (official, retrievable): {store.count(store.official, only_retrievable=True)} | PostgreSQL chunk_count sum: {pg_chunks}"
    )
    for q in QUERIES:
        print(f"\nQ: {q}")
        for h in store.search("OFFICIAL", emb.embed_query(q), 3):
            print(f"  {h.score:.3f}  {h.payload['knowledge_id']:<40} {h.payload['heading_path']}")
