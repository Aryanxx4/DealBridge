"""Reset demo data: truncate application tables, recreate resolved_query_knowledge, clear UPLOAD_DIR, reset the knowledge
epoch, then re-seed identities. Never touches the official collection or the OKF bundle. Requires --yes."""

import argparse
import shutil
import sys

import _bootstrap  # noqa: F401
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import get_engine, session_scope
from app.services.knowledge.state import record_collection
from app.services.seed import seed_identities
from app.services.vector.qdrant_store import get_store

APP_TABLES = [
    "follow_up_messages",
    "follow_up_requests",
    "seller_responses",
    "assessment_shares",
    "evidence_references",
    "requirement_assessments",
    "assessment_versions",
    "change_proposals",
    "requirement_revisions",
    "knowledge_records",
    "ticket_occurrences",
    "messages",
    "tickets",
    "conversations",
    "requirements",
    "uploaded_documents",
    "jobs",
    "assessments",
    "audit_events",
    "users",
    "organizations",
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--yes", action="store_true", help="confirm that demo data will be deleted")
    if not ap.parse_args().yes:
        print("Refusing to reset without --yes. This deletes all assessments, chats, tickets and expert answers.")
        return 2
    with get_engine().begin() as c:
        c.execute(text("TRUNCATE " + ", ".join(APP_TABLES) + " RESTART IDENTITY CASCADE"))
        c.execute(text("ALTER SEQUENCE ticket_display_seq RESTART WITH 1"))
        c.execute(text("UPDATE knowledge_state SET epoch = 0 WHERE id = 1"))
    store = get_store()
    store.create_collection(store.resolved, recreate=True)
    up = get_settings().upload_dir
    if up.exists():
        shutil.rmtree(up)
    with session_scope() as db:
        record_collection(db, store.resolved, reindexed=True)
        created = seed_identities(db)
    print(
        f"Demo reset: application tables truncated, {store.resolved} recreated, uploads cleared, epoch 0, {created['users']} users re-seeded."
    )
    print(f"Official collection {store.official} and the OKF bundle were not touched ({store.count(store.official)} points).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
