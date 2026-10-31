"""Check every '## Source excerpts' quote in the OKF bundle against the live official page.

For each concept file: fetch its source_url (cached under .cache/docs/), extract the article text and verify
that every excerpt occurs verbatim (after normalisation) and is at most 40 words.

  python scripts/verify_knowledge_excerpts.py            # report only
  python scripts/verify_knowledge_excerpts.py --approve  # files whose excerpts all pass become
                                                         # approval_status: approved, status: stable,
                                                         # verified: { by: process:dealbridge-excerpt-check }
  python scripts/verify_knowledge_excerpts.py --refresh  # re-fetch pages instead of using the cache

Files with any failing excerpt are never approved.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import _bootstrap  # noqa: F401

from app.core.config import REPO_ROOT, get_settings
from app.services.ingestion.html_text import extract_article
from app.services.ingestion.okf_loader import iter_concept_files, parse_concept, section_text
from app.services.retrieval.quote_verify import verify_quote

CACHE = REPO_ROOT / ".cache" / "docs"
MAX_WORDS = 40
ACTOR = "process:dealbridge-excerpt-check"


def fetch(url: str, refresh: bool) -> str:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / (hashlib.sha256(url.encode()).hexdigest()[:24] + ".html")
    if path.exists() and not refresh:
        return path.read_text(encoding="utf-8", errors="replace")
    req = urllib.request.Request(url, headers={"User-Agent": "DealBridge-curation/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 (fixed https documentation URLs)
        html = resp.read().decode("utf-8", errors="replace")
    path.write_text(html, encoding="utf-8")
    return html


def excerpts_of(body: str) -> list[str]:
    sec = section_text(body, "Source excerpts") or ""
    quotes, cur = [], []
    for line in sec.splitlines():
        if line.startswith(">"):
            cur.append(line[1:].strip())
        elif cur:
            quotes.append(" ".join(cur).strip())
            cur = []
    if cur:
        quotes.append(" ".join(cur).strip())
    return [q for q in quotes if q]


def stamp(path: Path, now: str) -> None:
    text = path.read_text(encoding="utf-8")
    head, sep, rest = text.partition("\n---\n")
    head = re.sub(r"^status: draft$", "status: stable", head, flags=re.M)
    head = re.sub(r"^approval_status: draft$", "approval_status: approved", head, flags=re.M)
    head = re.sub(r"^verified: .*$\n?", "", head, flags=re.M)
    head = head.replace("\nsources:", f"\nverified: {{ by: {ACTOR}, at: {now} }}\nsources:", 1)
    path.write_text(head + sep + rest, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--approve", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    bundle = get_settings().bundle_dir
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    failures = 0
    for path in iter_concept_files(bundle):
        meta, body = parse_concept(path)
        url = meta.get("source_url", "")
        _, page = extract_article(fetch(url, args.refresh))
        problems = []
        quotes = excerpts_of(body)
        if not quotes:
            problems.append("no excerpts")
        for q in quotes:
            if len(q.split()) > MAX_WORDS:
                problems.append(f"excerpt over {MAX_WORDS} words: {q[:60]}...")
            if not verify_quote(page, q):
                problems.append(f"NOT FOUND on page: {q[:80]}")
        rel = path.relative_to(bundle)
        if problems:
            failures += 1
            print(f"FAIL {rel}")
            for p in problems:
                print(f"     - {p}")
        else:
            print(f"ok   {rel} ({len(quotes)} excerpts)")
            if args.approve and meta.get("approval_status") != "approved":
                stamp(path, now)
    print(f"\n{failures} file(s) failed." if failures else "\nAll excerpts verified against the live pages.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
