"""Untrusted PDF upload handling (§10.4, R12).

Validation: content type + %PDF- magic bytes, size enforced while streaming, page count, encryption, malformed files.
Text extraction uses PyMuPDF `get_text("text")` only: pages are never rendered and no JavaScript, form actions or
embedded files are executed. Storage names are generated; the original filename is metadata only.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from pathlib import Path

import pymupdf

from app.core.config import get_settings
from app.core.errors import AppError

SCANNED_MESSAGE = (
    "This PDF looks scanned or image-only. DealBridge cannot read scanned documents yet (OCR is not implemented). "
    "Upload a text-based PDF, describe your needs in the chat, or use the guided form."
)
CHUNK = 64 * 1024


@dataclass
class StoredPdf:
    document_id: uuid.UUID
    path: Path
    sha256: str
    size_bytes: int
    page_count: int
    pages: list[dict]
    extraction_status: str
    extraction_message: str | None


def _limit_bytes() -> int:
    return get_settings().MAX_UPLOAD_MB * 1024 * 1024


def save_stream(stream, dest: Path, content_type: str | None, max_bytes: int | None = None, require_pdf: bool = True) -> tuple[str, int]:
    """Stream to disk enforcing the size limit; returns (sha256, size). Deletes the partial file on failure."""
    max_bytes = max_bytes or _limit_bytes()
    dest.parent.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    size = 0
    first = b""
    try:
        with open(dest, "wb") as out:
            while True:
                block = stream.read(CHUNK)
                if not block:
                    break
                if not first:
                    first = block[:5]
                    if require_pdf and (
                        first != b"%PDF-" or (content_type and content_type not in ("application/pdf", "application/x-pdf"))
                    ):
                        raise AppError("NOT_A_PDF", "Only PDF files are accepted (the file is not a valid PDF).", 415)
                size += len(block)
                if size > max_bytes:
                    raise AppError("FILE_TOO_LARGE", f"The file exceeds the {max_bytes // (1024 * 1024)} MB limit.", 413)
                h.update(block)
                out.write(block)
        if size == 0:
            raise AppError("NOT_A_PDF", "The file is empty.", 415)
    except Exception:
        dest.unlink(missing_ok=True)
        raise
    return h.hexdigest(), size


def extract_pages(path: Path) -> tuple[int, list[dict]]:
    try:
        doc = pymupdf.open(path, filetype="pdf")
    except Exception as exc:
        raise AppError("MALFORMED_PDF", "The PDF could not be read. It may be damaged.", 422) from exc
    try:
        if doc.needs_pass or doc.is_encrypted:
            raise AppError("ENCRYPTED_PDF", "The PDF is encrypted or password-protected. Upload an unprotected copy.", 422)
        if doc.page_count > get_settings().MAX_PDF_PAGES:
            raise AppError("TOO_MANY_PAGES", f"The PDF has {doc.page_count} pages; the limit is {get_settings().MAX_PDF_PAGES}.", 422)
        pages = []
        for i in range(doc.page_count):
            try:
                text = doc.load_page(i).get_text("text") or ""
            except Exception as exc:
                raise AppError("MALFORMED_PDF", "The PDF could not be read. It may be damaged.", 422) from exc
            pages.append({"page": i + 1, "text": text.replace("\x00", "")})
        return doc.page_count, pages
    finally:
        doc.close()


def classify_text(page_count: int, pages: list[dict]) -> tuple[str, str | None]:
    total = sum(len(p["text"].strip()) for p in pages)
    if page_count == 0:
        return "EMPTY", "The PDF has no pages."
    if total < 200 or total / page_count < 50:
        return "SCANNED", SCANNED_MESSAGE
    return "OK", None


def store_buyer_pdf(stream, content_type: str | None, assessment_id: uuid.UUID) -> StoredPdf:
    doc_id = uuid.uuid4()
    path = get_settings().upload_dir / "assessments" / str(assessment_id) / f"{doc_id}.pdf"
    sha, size = save_stream(stream, path, content_type)
    try:
        page_count, pages = extract_pages(path)
    except AppError:
        path.unlink(missing_ok=True)
        raise
    status, message = classify_text(page_count, pages)
    return StoredPdf(doc_id, path, sha, size, page_count, pages, status, message)
