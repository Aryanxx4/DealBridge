"""Idempotent ingestion of the OKF bundle into the official Qdrant collection (build prompt §8.4)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import AuditAction
from app.models.knowledge import IngestionRun, OkfFile
from app.services.audit import audit
from app.services.embeddings.embedder import Embedder, get_embedder
from app.services.ingestion.chunker import chunk_concept
from app.services.ingestion.okf_loader import render_index, validate_bundle
from app.services.knowledge.state import bump_epoch, record_collection
from app.services.vector.qdrant_store import QdrantStore, get_store

log = logging.getLogger("dealbridge.ingest")

EMBED_BATCH = 32


@dataclass
class IngestOptions:
    validate_only: bool = False
    dry_run: bool = False
    force: bool = False
    recreate: bool = False
    triggered_by: str = "cli"


@dataclass
class IngestResult:
    status: str = "completed"
    files_scanned: int = 0
    added: int = 0
    updated: int = 0
    unchanged: int = 0
    removed: int = 0
    skipped: int = 0
    chunks_upserted: int = 0
    chunks_deleted: int = 0
    errors: list[dict] = field(default_factory=list)
    plan: list[dict] = field(default_factory=list)
    run_id: str | None = None
    epoch_changed: bool = False

    def as_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


def _payload(meta: dict, chunk, file_hash: str, now: str) -> dict:
    return {
        "knowledge_id": meta["knowledge_id"],
        "chunk_id": chunk.chunk_id,
        "title": meta["title"],
        "heading_path": chunk.heading_path,
        "category": meta["category"],
        "source_type": "official",
        "source_url": meta["source_url"],
        "source_document": meta["source_document"],
        "last_verified_at": str(meta["last_verified_at"]),
        "version": int(meta["version"]),
        "approval_status": "approved",
        "validity_status": "ACTIVE",
        "content_hash": file_hash,
        "chunk_hash": chunk.chunk_hash,
        "updated_at": now,
        "text": chunk.text,
    }


def ingest_bundle(
    db: Session,
    options: IngestOptions,
    bundle: Path | None = None,
    store: QdrantStore | None = None,
    embedder: Embedder | None = None,
    progress=None,
) -> IngestResult:
    s = get_settings()
    bundle = bundle or s.bundle_dir
    store = store or get_store()
    res = IngestResult()
    report = validate_bundle(bundle)
    res.files_scanned = len(report.concepts)
    for rel, errs in report.reserved_errors.items():
        for e in errs:
            res.errors.append({"path": rel, "error": e})
    if options.validate_only:
        for c in report.concepts:
            for e in c.errors:
                res.errors.append({"path": c.rel_path, "error": e})
        res.status = "valid" if report.ok else "invalid"
        return res

    embedder = embedder or get_embedder()
    now_dt = datetime.now(UTC)
    now = now_dt.isoformat()
    run = None
    if not options.dry_run:
        run = IngestionRun(
            started_at=now_dt,
            triggered_by=options.triggered_by,
            mode="recreate" if options.recreate else ("force" if options.force else "incremental"),
            spec_conformance="OKF",
            embedding_model=s.EMBEDDING_MODEL,
            status="running",
        )
        db.add(run)
        db.flush()
        if options.recreate:
            store.create_collection(store.official, recreate=True)
            record_collection(db, store.official, reindexed=True)
            res.epoch_changed = True

    force = options.force or options.recreate
    existing = {f.path: f for f in db.scalars(select(OkfFile)).all()}
    seen_paths: set[str] = set()
    total = len(report.concepts)

    for n, c in enumerate(report.concepts, start=1):
        if progress:
            progress(n - 1, total, f"Processing {c.rel_path} ({n} of {total})")
        seen_paths.add(c.rel_path)
        rec = existing.get(c.rel_path)
        prev_ids: list[str] = list(rec.chunk_ids) if rec and rec.status == "INDEXED" else []
        if options.recreate:
            prev_ids = []  # collection was dropped

        if c.errors:
            res.errors.extend({"path": c.rel_path, "error": e} for e in c.errors)
            res.plan.append({"path": c.rel_path, "action": "error"})
            if not options.dry_run:
                rec = rec or OkfFile(path=c.rel_path, status="ERROR")
                if rec.id is None:
                    db.add(rec)
                rec.status, rec.error, rec.last_ingested_at = "ERROR", "; ".join(c.errors)[:2000], now_dt
            continue

        meta = c.meta
        if not c.approved:
            res.skipped += 1
            res.plan.append({"path": c.rel_path, "action": "skip_not_approved", "delete_points": len(prev_ids)})
            if not options.dry_run:
                if prev_ids:
                    res.chunks_deleted += store.delete(store.official, prev_ids)
                    res.epoch_changed = True
                rec = rec or OkfFile(path=c.rel_path, status="SKIPPED_NOT_APPROVED")
                if rec.id is None:
                    db.add(rec)
                _fill(rec, meta, c.content_hash)
                rec.status, rec.chunk_ids, rec.chunk_count, rec.error = "SKIPPED_NOT_APPROVED", [], 0, None
                rec.last_ingested_at = now_dt
            continue

        if rec and rec.status == "INDEXED" and rec.content_hash == c.content_hash and not force:
            res.unchanged += 1
            res.plan.append({"path": c.rel_path, "action": "unchanged"})
            continue

        chunks = chunk_concept(meta["knowledge_id"], meta["title"], c.body)
        new_ids = [ch.chunk_id for ch in chunks]
        stale = [i for i in prev_ids if i not in set(new_ids)]
        is_new = not (rec and rec.status == "INDEXED")
        res.plan.append({"path": c.rel_path, "action": "add" if is_new else "update", "chunks": len(chunks), "delete_points": len(stale)})
        if options.dry_run:
            continue
        points = []
        for start in range(0, len(chunks), EMBED_BATCH):
            batch = chunks[start : start + EMBED_BATCH]
            vectors = embedder.embed_documents([ch.embed_text(meta["title"]) for ch in batch])
            points.extend((ch.chunk_id, vec, _payload(meta, ch, c.content_hash, now)) for ch, vec in zip(batch, vectors, strict=True))
        res.chunks_upserted += store.upsert(store.official, points)
        res.chunks_deleted += store.delete(store.official, stale)
        res.epoch_changed = True
        if is_new:
            res.added += 1
        else:
            res.updated += 1
        rec = rec or OkfFile(path=c.rel_path, status="INDEXED")
        if rec.id is None:
            db.add(rec)
        _fill(rec, meta, c.content_hash)
        rec.status, rec.chunk_ids, rec.chunk_count, rec.error, rec.last_ingested_at = "INDEXED", new_ids, len(new_ids), None, now_dt

    # Files that disappeared from disk.
    for path, rec in existing.items():
        if path in seen_paths or rec.status == "REMOVED":
            continue
        ids = list(rec.chunk_ids or [])
        res.plan.append({"path": path, "action": "remove", "delete_points": len(ids)})
        if options.dry_run:
            continue
        if ids and not options.recreate:
            res.chunks_deleted += store.delete(store.official, ids)
        res.removed += 1
        res.epoch_changed = True
        rec.status, rec.chunk_ids, rec.chunk_count, rec.last_ingested_at = "REMOVED", [], 0, now_dt

    if res.errors:
        res.status = "completed_with_errors"
    if options.dry_run:
        res.status = "dry_run"
        return res

    if res.epoch_changed:
        bump_epoch(db)
    record_collection(db, store.official)
    assert run is not None
    for k in ("files_scanned", "added", "updated", "unchanged", "removed", "skipped", "chunks_upserted", "chunks_deleted"):
        setattr(run, k, getattr(res, k))
    run.errors, run.status, run.finished_at = res.errors, res.status, datetime.now(UTC)
    audit(db, AuditAction.OKF_INGESTED, "ingestion_run", run.id, None, {"status": res.status, "chunks_upserted": res.chunks_upserted})
    db.commit()
    res.run_id = str(run.id)
    if progress:
        progress(total, total, "Ingestion finished")
    return res


def _fill(rec: OkfFile, meta: dict, file_hash: str) -> None:
    rec.knowledge_id = meta.get("knowledge_id")
    rec.title = meta.get("title")
    rec.category = meta.get("category")
    rec.source_url = meta.get("source_url")
    rec.last_verified_at = str(meta.get("last_verified_at") or "")
    rec.version = meta.get("version")
    rec.approval_status = meta.get("approval_status")
    rec.content_hash = file_hash


def rebuild_index(bundle: Path | None = None) -> list[str]:
    bundle = bundle or get_settings().bundle_dir
    written = []
    for rel, content in render_index(bundle).items():
        path = bundle / rel
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            path.write_text(content, encoding="utf-8")
            written.append(rel)
    return written
