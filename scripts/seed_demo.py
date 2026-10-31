"""Seed demo identities (idempotent). Fixed UUIDs (uuid5) so the frontend can rely on them.

All names and e-mail addresses are fictional. 'IOMETE Sales' is a demo seller organisation,
not a statement about IOMETE's real staff.
"""

import _bootstrap  # noqa: F401

from app.db.session import session_scope
from app.services.seed import seed_identities

if __name__ == "__main__":
    with session_scope() as db:
        created = seed_identities(db)
    print(f"Seed complete: {created['organizations']} organisations and {created['users']} users created (others already existed).")
