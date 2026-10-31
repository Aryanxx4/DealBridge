import shutil

from sqlalchemy import select

from app.core.runtime import STATE, check_vectors
from app.models.knowledge import OkfFile
from app.models.system import VectorCollection
from app.services.ingestion.okf_ingest import IngestOptions, ingest_bundle
from app.services.knowledge.state import current_epoch


def _ingest(db, bundle, store, embedder, **kw):
    return ingest_bundle(db, IngestOptions(**kw), bundle=bundle, store=store, embedder=embedder)


def _ids(store):
    return {p["id"] for p in store.scroll_all(store.official, with_payload=False)}


def test_ingestion_is_idempotent(db, store, embedder, mini_bundle):
    first = _ingest(db, mini_bundle, store, embedder)
    assert first.added == 5 and first.skipped == 1 and first.chunks_upserted > 0
    epoch = current_epoch(db)
    second = _ingest(db, mini_bundle, store, embedder)
    assert second.chunks_upserted == 0 and second.unchanged == 5 and second.chunks_deleted == 0
    assert current_epoch(db) == epoch  # nothing changed, epoch unchanged
    total = sum(f.chunk_count for f in db.scalars(select(OkfFile).where(OkfFile.status == "INDEXED")))
    assert store.count(store.official) == total


def test_ingestion_changed_file_replaces_only_its_chunks(db, store, embedder, mini_bundle):
    _ingest(db, mini_bundle, store, embedder)
    before = _ids(store)
    sso = db.scalar(select(OkfFile).where(OkfFile.path == "security/sso.md"))
    other_ids = before - set(sso.chunk_ids)
    path = mini_bundle / "security" / "sso.md"
    original = path.read_text()
    path.write_text(original.replace("- Group to role mapping.", "- Group to role mapping.\n- Nested groups are supported."))
    assert path.read_text() != original
    res = _ingest(db, mini_bundle, store, embedder)
    assert res.updated == 1 and res.unchanged == 4
    after = _ids(store)
    assert other_ids <= after  # untouched files keep their points
    db.refresh(sso)
    assert set(sso.chunk_ids) <= after
    assert after == other_ids | set(sso.chunk_ids)  # stale sso chunks deleted


def test_ingestion_removed_file_deletes_points(db, store, embedder, mini_bundle):
    _ingest(db, mini_bundle, store, embedder)
    bi = db.scalar(select(OkfFile).where(OkfFile.path == "integrations/bi.md"))
    bi_ids = set(bi.chunk_ids)
    shutil.rmtree(mini_bundle / "integrations")
    res = _ingest(db, mini_bundle, store, embedder)
    assert res.removed == 1 and res.chunks_deleted == len(bi_ids)
    assert not (bi_ids & _ids(store))
    db.refresh(bi)
    assert bi.status == "REMOVED"


def test_only_approved_files_are_indexed(db, store, embedder, mini_bundle):
    _ingest(db, mini_bundle, store, embedder)
    kids = {p["payload"]["knowledge_id"] for p in store.scroll_all(store.official)}
    assert "acmelake.architecture.storage" not in kids  # draft file
    # Demoting an indexed file to draft removes its points.
    path = mini_bundle / "platform" / "sql.md"
    path.write_text(
        path.read_text().replace("approval_status: approved", "approval_status: draft").replace("status: stable", "status: draft")
    )
    res = _ingest(db, mini_bundle, store, embedder)
    assert res.skipped == 2 and res.chunks_deleted > 0
    kids = {p["payload"]["knowledge_id"] for p in store.scroll_all(store.official)}
    assert "acmelake.platform.sql" not in kids


def test_validation_errors_skip_file_and_continue(db, store, embedder, mini_bundle):
    (mini_bundle / "broken.md").write_text("---\ntitle: no type\n---\n# Broken\n")
    res = _ingest(db, mini_bundle, store, embedder)
    assert res.status == "completed_with_errors" and res.added == 5
    assert db.scalar(select(OkfFile).where(OkfFile.path == "broken.md")).status == "ERROR"


def test_embedding_model_mismatch_blocks_serving(db, store):
    vc = db.scalar(select(VectorCollection).where(VectorCollection.name == store.official))
    vc.embedding_model = "some/other-model"
    db.commit()
    check_vectors(db)
    try:
        assert STATE.reindex_required
        assert any("some/other-model" in p for p in STATE.reindex_problems)
    finally:
        vc.embedding_model = "BAAI/bge-small-en-v1.5"
        db.commit()
        check_vectors(db)
    assert not STATE.reindex_required
