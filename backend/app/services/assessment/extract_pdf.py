"""PDF requirement extraction job (§10.4)."""

from __future__ import annotations

import re
import uuid

from rapidfuzz import fuzz, utils
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import AuditAction, RequirementSource
from app.core.errors import AppError, not_found
from app.models.assessment import Requirement, UploadedDocument
from app.prompts import extract_pdf as P
from app.services.assessment import requirement_service as RS
from app.services.audit import audit
from app.services.llm.client import get_llm
from app.services.retrieval.quote_verify import normalize

WINDOW_CHARS = 12_000
MAX_PER_RUN = 60
DEDUPE_RATIO = 92
FUZZY_PAGE_RATIO = 85


def build_windows(pages: list[dict], limit: int = WINDOW_CHARS) -> list[str]:
    """Windows of at most `limit` chars split at page boundaries, with [[PAGE n]] markers. Oversized pages are split
    at paragraph boundaries (each piece keeps its page marker)."""
    pieces: list[str] = []
    for p in pages:
        text = p["text"].strip()
        if not text:
            continue
        marker = f"[[PAGE {p['page']}]]\n"
        if len(marker) + len(text) <= limit:
            pieces.append(marker + text)
            continue
        cur = ""
        for para in re.split(r"\n\s*\n", text):
            para = para.strip()
            while len(para) > limit - len(marker):
                head, para = para[: limit - len(marker)], para[limit - len(marker) :]
                if cur:
                    pieces.append(marker + cur)
                    cur = ""
                pieces.append(marker + head)
            if len(marker) + len(cur) + len(para) + 2 > limit and cur:
                pieces.append(marker + cur)
                cur = para
            else:
                cur = f"{cur}\n\n{para}" if cur else para
        if cur:
            pieces.append(marker + cur)
    windows, cur = [], ""
    for piece in pieces:
        if cur and len(cur) + len(piece) + 2 > limit:
            windows.append(cur)
            cur = piece
        else:
            cur = f"{cur}\n\n{piece}" if cur else piece
    if cur:
        windows.append(cur)
    return windows


def locate(pages: list[dict], original_text: str, claimed_page: int | None) -> tuple[int | None, bool]:
    """(page, quote_verified). Exact normalised match first, then best rapidfuzz partial_ratio >= 85."""
    q = normalize(original_text)
    if not q:
        return claimed_page, False
    ordered = sorted(pages, key=lambda p: p["page"] != claimed_page)
    for p in ordered:
        if q in normalize(p["text"]):
            return p["page"], True
    best, best_page = 0.0, None
    for p in pages:
        score = fuzz.partial_ratio(q, normalize(p["text"]), processor=utils.default_process)
        if score > best:
            best, best_page = score, p["page"]
    if best >= FUZZY_PAGE_RATIO:
        return best_page, True
    return claimed_page, False


def is_duplicate(text: str, existing: list[str]) -> bool:
    n = normalize(text)
    return any(fuzz.token_sort_ratio(n, normalize(e), processor=utils.default_process) >= DEDUPE_RATIO for e in existing)


def run_extraction(db: Session, assessment_id: uuid.UUID, document_id: uuid.UUID, user, progress) -> dict:
    a = RS.lock_assessment(db, assessment_id)
    doc = db.get(UploadedDocument, document_id)
    if doc is None or doc.assessment_id != a.id:
        raise not_found("Document")
    if doc.extraction_status != "OK":
        raise AppError("DOCUMENT_NOT_EXTRACTABLE", doc.extraction_message or "This document has no extractable text.", 422)
    windows = build_windows(doc.pages)
    existing = [
        r.normalized_text
        for r in db.scalars(select(Requirement).where(Requirement.assessment_id == a.id, Requirement.is_removed.is_(False)))
    ]
    llm = get_llm()
    created = dupes = clar = 0
    truncated = False
    actor = RS.Actor(user, "PDF")
    for i, window in enumerate(windows, start=1):
        progress(i - 1, len(windows), f"Reading part {i} of {len(windows)}")
        result = llm.complete_structured("main", P.SYSTEM, P.build_messages(window), P.ExtractionResult, P.TOOL, 8000, 0.0)
        for item in result.requirements:
            if is_duplicate(item.normalized_text, existing):
                dupes += 1
                continue
            if created >= MAX_PER_RUN:
                truncated = True
                break
            page, verified = locate(doc.pages, item.original_text, item.page)
            RS.create(
                db,
                a,
                actor,
                original_text=item.original_text[:500],
                normalized_text=item.normalized_text,
                category=item.category,
                priority=item.priority,
                priority_basis=item.priority_basis if item.priority != "NOT_SPECIFIED" else None,
                source_type=RequirementSource.PDF.value,
                source_reference={
                    "document_id": str(doc.id),
                    "filename": doc.original_filename,
                    "page": page,
                    "quote": item.original_text[:500],
                    "quote_verified": verified,
                },
                buyer_confirmed=False,
                needs_clarification=item.needs_clarification,
                clarifying_question=item.clarifying_question,
            )
            existing.append(item.normalized_text)
            created += 1
            clar += int(item.needs_clarification)
        progress(i, len(windows), f"Read part {i} of {len(windows)}")
        if truncated:
            break
    result = {
        "created": created,
        "duplicates_skipped": dupes,
        "needs_clarification_count": clar,
        "truncated": truncated,
        "document_id": str(doc.id),
    }
    audit(db, AuditAction.REQUIREMENTS_EXTRACTED, "assessment", a.id, user, result)
    db.commit()
    return result
