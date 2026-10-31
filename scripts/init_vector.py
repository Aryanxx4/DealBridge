"""Create both Qdrant collections and payload indexes (idempotent) and record them in PostgreSQL."""

import _bootstrap  # noqa: F401

from app.db.session import session_scope
from app.services.knowledge.state import record_collection
from app.services.vector.qdrant_store import get_store

if __name__ == "__main__":
    store = get_store()
    created = store.init_collections()
    with session_scope() as db:
        for name in (store.official, store.resolved):
            record_collection(db, name)
    for name, was_created in created.items():
        print(f"{name}: {'created' if was_created else 'already exists'} (payload indexes ensured)")
