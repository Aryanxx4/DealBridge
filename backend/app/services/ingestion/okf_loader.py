"""OKF v0.2 bundle loading and validation.

Spec: https://github.com/GoogleCloudPlatform/open-knowledge-format (SPEC.md @ ad30107).
Conformance (§11): every non-reserved .md has parseable YAML frontmatter with a non-empty `type`;
reserved files (index.md, log.md) follow §8 / §9. DealBridge adds stricter project rules on top.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import frontmatter
import yaml

RESERVED = {"index.md", "log.md"}
CATEGORIES = {"deployment", "architecture", "security", "platform", "integrations", "concepts"}
REQUIRED_EXTENSION_KEYS = (
    "knowledge_id",
    "title",
    "description",
    "category",
    "source_type",
    "source_url",
    "source_document",
    "last_verified_at",
    "version",
    "approval_status",
)
REQUIRED_SECTIONS = ("Summary", "Details", "Source excerpts", "Not stated in the documentation")
NOT_INDEXED_SECTION = "Not stated in the documentation"
_DATE_HEADING = re.compile(r"^## (\d{4}-\d{2}-\d{2})\s*$", re.M)


@dataclass
class ConceptFile:
    path: Path
    rel_path: str
    meta: dict
    body: str
    content_hash: str
    errors: list[str] = field(default_factory=list)

    @property
    def concept_id(self) -> str:  # OKF concept ID: path without .md
        return self.rel_path[:-3]

    @property
    def approved(self) -> bool:
        return self.meta.get("approval_status") == "approved"


def content_hash(raw: str) -> str:
    """SHA-256 after normalising line endings and trailing whitespace."""
    norm = "\n".join(line.rstrip() for line in raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")).strip() + "\n"
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def iter_concept_files(bundle: Path) -> list[Path]:
    return sorted(p for p in bundle.rglob("*.md") if p.name not in RESERVED and not any(x.startswith(".") for x in p.parts))


def iter_reserved_files(bundle: Path) -> list[Path]:
    return sorted(p for p in bundle.rglob("*.md") if p.name in RESERVED)


def parse_concept(path: Path) -> tuple[dict, str]:
    post = frontmatter.load(path)
    return dict(post.metadata), post.content


def sections(body: str) -> list[tuple[str, str]]:
    """Split a body into (## heading, text) pairs. Text before the first ## is returned under ''."""
    out: list[tuple[str, str]] = []
    current, buf = "", []
    in_fence = False
    for line in body.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
        if not in_fence and line.startswith("## "):
            out.append((current, "\n".join(buf).strip()))
            current, buf = line[3:].strip(), []
        else:
            buf.append(line)
    out.append((current, "\n".join(buf).strip()))
    return [(h, t) for h, t in out if h or t]


def section_text(body: str, heading: str) -> str | None:
    for h, t in sections(body):
        if h == heading:
            return t
    return None


def _as_date(v) -> bool:
    if isinstance(v, (date, datetime)):
        return True
    try:
        date.fromisoformat(str(v))
        return True
    except ValueError:
        return False


def load_concept(path: Path, bundle: Path) -> ConceptFile:
    raw = path.read_text(encoding="utf-8")
    rel = path.relative_to(bundle).as_posix()
    errors: list[str] = []
    meta: dict = {}
    body = ""
    if not raw.startswith("---"):
        errors.append("OKF §11.1: missing YAML frontmatter block")
    else:
        try:
            post = frontmatter.loads(raw)
            meta, body = dict(post.metadata), post.content
        except yaml.YAMLError as exc:
            errors.append(f"OKF §11.1: frontmatter is not parseable YAML ({type(exc).__name__})")
    cf = ConceptFile(path=path, rel_path=rel, meta=meta, body=body, content_hash=content_hash(raw), errors=errors)
    if errors:
        return cf
    if not str(meta.get("type") or "").strip():
        errors.append("OKF §11.2: frontmatter has no non-empty `type`")
    # ---- DealBridge project rules ----
    for key in REQUIRED_EXTENSION_KEYS:
        if meta.get(key) in (None, ""):
            errors.append(f"missing required key `{key}`")
    if meta.get("category") and meta["category"] not in CATEGORIES:
        errors.append(f"invalid category `{meta['category']}`")
    if meta.get("source_type") not in (None, "official"):
        errors.append("source_type must be `official`")
    url = str(meta.get("source_url") or "")
    if url and not re.match(r"^https?://", url):
        errors.append("source_url must be an http(s) URL")
    if meta.get("last_verified_at") and not _as_date(meta["last_verified_at"]):
        errors.append("last_verified_at is not a valid date")
    if meta.get("version") is not None and (not isinstance(meta["version"], int) or meta["version"] < 1):
        errors.append("version must be a positive integer")
    status, approval = meta.get("status", "stable"), meta.get("approval_status")
    if approval not in (None, "approved", "draft"):
        errors.append("approval_status must be `approved` or `draft`")
    elif approval == "approved" and status != "stable":
        errors.append("approval_status approved requires OKF status `stable`")
    elif approval == "draft" and status != "draft":
        errors.append("approval_status draft requires OKF status `draft`")
    verified = meta.get("verified")
    if verified is not None:
        items = verified if isinstance(verified, list) else [verified]  # OKF §5.2: bare mapping = one-element list
        for v in items:
            if not isinstance(v, dict) or not v.get("by"):
                errors.append("verified entries need `by`")
    present = {h for h, _ in sections(body)}
    for sec in REQUIRED_SECTIONS:
        if sec not in present:
            errors.append(f"missing body section `## {sec}`")
    if not body.lstrip().startswith("# "):
        errors.append("body must start with a `# Title` heading")
    return cf


def validate_reserved(path: Path, bundle: Path) -> list[str]:
    """OKF §8 (index.md) and §9 (log.md)."""
    raw = path.read_text(encoding="utf-8")
    errors: list[str] = []
    is_root = path.parent == bundle
    if path.name == "index.md" and raw.startswith("---"):
        try:
            post = frontmatter.loads(raw)
            extra = set(post.metadata) - {"okf_version"}
            if not is_root:
                errors.append("OKF §8: only the bundle-root index.md may carry frontmatter")
            elif extra:
                errors.append(f"OKF §8/§12: root index.md frontmatter may only contain okf_version (found {sorted(extra)})")
        except yaml.YAMLError:
            errors.append("index.md frontmatter is not parseable")
    if path.name == "log.md":
        dates = _DATE_HEADING.findall(raw)
        for d in dates:
            try:
                date.fromisoformat(d)
            except ValueError:
                errors.append(f"OKF §9: invalid date heading {d}")
        if dates != sorted(dates, reverse=True):
            errors.append("OKF §9: log entries must be newest first")
    return errors


@dataclass
class BundleReport:
    concepts: list[ConceptFile]
    reserved_errors: dict[str, list[str]]
    duplicate_ids: list[str]

    @property
    def ok(self) -> bool:
        return not self.duplicate_ids and not any(c.errors for c in self.concepts) and not any(self.reserved_errors.values())


def validate_bundle(bundle: Path) -> BundleReport:
    concepts = [load_concept(p, bundle) for p in iter_concept_files(bundle)]
    seen: dict[str, str] = {}
    dups: list[str] = []
    for c in concepts:
        kid = c.meta.get("knowledge_id")
        if kid:
            if kid in seen:
                dups.append(kid)
                c.errors.append(f"duplicate knowledge_id `{kid}` (also in {seen[kid]})")
            seen[kid] = c.rel_path
    reserved = {p.relative_to(bundle).as_posix(): validate_reserved(p, bundle) for p in iter_reserved_files(bundle)}
    return BundleReport(concepts=concepts, reserved_errors=reserved, duplicate_ids=dups)


def render_index(bundle: Path, okf_version: str = "0.2") -> dict[str, str]:
    """Build index.md content for the bundle root and each category directory (OKF §8)."""
    concepts = [load_concept(p, bundle) for p in iter_concept_files(bundle)]
    by_dir: dict[str, list[ConceptFile]] = {}
    for c in concepts:
        by_dir.setdefault(str(Path(c.rel_path).parent.as_posix()), []).append(c)
    out: dict[str, str] = {}
    root = [f'---\nokf_version: "{okf_version}"\n---\n', "# IOMETE official product knowledge\n"]
    root.append(
        "Curated from the official IOMETE documentation (https://iomete.com/resources/). "
        "Each concept records its source page, its knowledge_id and its approval status.\n"
    )
    for d in sorted(by_dir):
        root.append(f"\n# {d.capitalize()}\n")
        for c in sorted(by_dir[d], key=lambda x: x.rel_path):
            mark = "" if c.approved else " (draft, not indexed)"
            root.append(
                f"* [{c.meta.get('title', c.rel_path)}]({c.rel_path}) - `{c.meta.get('knowledge_id')}`: {c.meta.get('description', '')}{mark}"
            )
        sub = [f"# {d.capitalize()}\n"]
        for c in sorted(by_dir[d], key=lambda x: x.rel_path):
            sub.append(f"* [{c.meta.get('title')}]({Path(c.rel_path).name}) - {c.meta.get('description', '')}")
        out[f"{d}/index.md"] = "\n".join(sub) + "\n"
    out["index.md"] = "\n".join(root) + "\n"
    return out
