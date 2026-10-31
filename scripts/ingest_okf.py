"""Ingest the OKF bundle into the official Qdrant collection.

Flags:
  --validate-only   parse and validate (OKF v0.2 §11 plus DealBridge rules); write nothing
  --dry-run         print the plan; write nothing
  --force           ignore content hashes (re-embed every approved file)
  --recreate        drop and recreate the official collection (required after an embedding model change)
  --rebuild-index   regenerate index.md files from concept frontmatter before ingesting
"""

import argparse
import sys

import _bootstrap  # noqa: F401

from app.db.session import session_scope
from app.services.ingestion.okf_ingest import IngestOptions, ingest_bundle, rebuild_index


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for flag in ("--validate-only", "--dry-run", "--force", "--recreate", "--rebuild-index"):
        ap.add_argument(flag, action="store_true")
    a = ap.parse_args()

    if a.rebuild_index:
        written = rebuild_index()
        print(f"index.md files rewritten: {', '.join(written) if written else 'none (already in sync)'}")

    opts = IngestOptions(validate_only=a.validate_only, dry_run=a.dry_run, force=a.force, recreate=a.recreate, triggered_by="cli")
    with session_scope() as db:
        res = ingest_bundle(db, opts)

    if a.validate_only:
        print(f"Validated {res.files_scanned} concept files against OKF v0.2 + DealBridge rules: {res.status.upper()}")
        for e in res.errors:
            print(f"  ERROR {e['path']}: {e['error']}")
        return 0 if res.status == "valid" else 1
    if a.dry_run:
        print(f"Dry run over {res.files_scanned} files:")
        for p in res.plan:
            if p["action"] != "unchanged":
                print(f"  {p['action']:<18} {p['path']}  {p.get('chunks', '')}")
        print(f"  unchanged: {sum(1 for p in res.plan if p['action'] == 'unchanged')}")
        return 0

    rows = [
        ("files scanned", res.files_scanned),
        ("added", res.added),
        ("updated", res.updated),
        ("unchanged", res.unchanged),
        ("removed", res.removed),
        ("skipped (not approved)", res.skipped),
        ("chunks upserted", res.chunks_upserted),
        ("chunks deleted", res.chunks_deleted),
        ("errors", len(res.errors)),
    ]
    print(f"Ingestion run {res.run_id}: {res.status}")
    for k, v in rows:
        print(f"  {k:<24}{v:>6}")
    for e in res.errors:
        print(f"  ERROR {e['path']}: {e['error']}")
    print(f"  knowledge epoch {'incremented' if res.epoch_changed else 'unchanged'}")
    return 0 if res.status in ("completed", "completed_with_errors") else 1


if __name__ == "__main__":
    sys.exit(main())
