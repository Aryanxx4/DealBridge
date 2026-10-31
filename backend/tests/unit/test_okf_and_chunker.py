from pathlib import Path

from app.services.ingestion.chunker import MAX_CHARS, chunk_concept
from app.services.ingestion.okf_loader import content_hash, render_index, validate_bundle

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "okf_mini"


def test_fixture_bundle_is_okf_conformant():
    report = validate_bundle(FIX)
    assert report.ok, [(c.rel_path, c.errors) for c in report.concepts if c.errors]
    assert len(report.concepts) == 6


def test_missing_type_and_bad_url_are_reported(tmp_path):
    (tmp_path / "x.md").write_text("---\ntitle: X\nsource_url: ftp://nope\n---\n# X\n")
    report = validate_bundle(tmp_path)
    errs = " ".join(report.concepts[0].errors)
    assert "type" in errs and "source_url must be an http(s) URL" in errs and not report.ok


def test_unparseable_frontmatter_is_an_error(tmp_path):
    (tmp_path / "x.md").write_text("---\ntitle: a: b: c\n---\n# X\n")
    assert "not parseable" in " ".join(validate_bundle(tmp_path).concepts[0].errors)


def test_approval_must_match_okf_status(tmp_path):
    src = (FIX / "security" / "sso.md").read_text().replace("status: stable", "status: draft")
    (tmp_path / "sso.md").write_text(src)
    assert any("requires OKF status" in e for e in validate_bundle(tmp_path).concepts[0].errors)


def test_index_frontmatter_rules(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "index.md").write_text('---\nokf_version: "0.2"\n---\n# Sub\n')
    report = validate_bundle(tmp_path)
    assert any("only the bundle-root index.md" in e for e in report.reserved_errors["sub/index.md"])


def test_content_hash_ignores_line_endings_and_trailing_space():
    assert content_hash("a  \r\nb\r\n") == content_hash("a\nb\n")
    assert content_hash("a\nb\n") != content_hash("a\nc\n")


def test_chunker_excludes_not_stated_and_ids_are_stable():
    body = (FIX / "deployment" / "self-hosted.md").read_text().split("---", 2)[2]
    a = chunk_concept("acmelake.deployment.self-hosted", "Self-hosted deployment", body)
    b = chunk_concept("acmelake.deployment.self-hosted", "Self-hosted deployment", body)
    assert [c.chunk_id for c in a] == [c.chunk_id for c in b]
    joined = " ".join(c.text for c in a)
    assert "Pricing is not stated" not in joined
    assert all(c.heading_path.startswith("Self-hosted deployment > ") for c in a)


def test_long_sections_are_split_with_limit_and_overlap():
    para = "word " * 600
    body = f"# T\n\n## Details\n\n{para}\n\n{para}\n\n## Not stated in the documentation\n\n- x\n"
    chunks = chunk_concept("k", "T", body)
    assert len(chunks) >= 2 and all(len(c.text) <= MAX_CHARS for c in chunks)


def test_short_sections_merge_with_next():
    body = "# T\n\n## Summary\n\nShort.\n\n## Details\n\n" + ("- detail line\n" * 40)
    chunks = chunk_concept("k", "T", body)
    assert chunks[0].heading_path == "T > Summary / Details"


def test_render_index_lists_concepts():
    out = render_index(FIX)
    assert out["index.md"].startswith('---\nokf_version: "0.2"\n---')
    assert "acmelake.security.sso" in out["index.md"] and "(draft, not indexed)" in out["index.md"]
