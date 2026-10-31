"""Section-based chunking of OKF concept bodies (build prompt §8.3).

- One chunk per `##` section, excluding `## Not stated in the documentation` (reviewers only).
- Sections over MAX_CHARS are split at paragraph / list-item boundaries into pieces of at most MAX_CHARS,
  with OVERLAP characters carried over from the previous piece.
- A section under MIN_CHARS is merged with the next section of the same file.
- chunk_id = uuid5(NAMESPACE, f"{knowledge_id}|{chunk_index}|{sha256(chunk_text)}") so unchanged chunks keep ids.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass

from markdown_it import MarkdownIt

from app.services.ingestion.okf_loader import NOT_INDEXED_SECTION

MAX_CHARS = 1800
OVERLAP = 150
MIN_CHARS = 300
CHUNK_NAMESPACE = uuid.UUID("2b8f0e5c-7d1a-4c3b-9e6f-0a1b2c3d4e5f")

_md = MarkdownIt("commonmark")


@dataclass
class Chunk:
    index: int
    chunk_id: str
    heading_path: str
    text: str
    chunk_hash: str

    def embed_text(self, title: str) -> str:
        return f"{title} | {self.heading_path}\n{self.text}"


def _sections(body: str) -> list[tuple[str, str]]:
    """(heading, text) for each `##` section, using markdown-it token line maps."""
    lines = body.splitlines()
    tokens = _md.parse(body)
    heads: list[tuple[int, int, str]] = []  # (heading line, first content line, heading text)
    for i, tok in enumerate(tokens):
        if tok.type == "heading_open" and tok.tag == "h2" and tok.map:
            heads.append((tok.map[0], tok.map[1], tokens[i + 1].content.strip()))
    out = []
    for n, (_, content_start, heading) in enumerate(heads):
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        out.append((heading, "\n".join(lines[content_start:end]).strip()))
    return out


def _blocks(text: str) -> list[str]:
    """Top-level blocks; lists are split into individual items."""
    lines = text.splitlines()
    tokens = _md.parse(text)
    blocks: list[str] = []
    for tok in tokens:
        if not tok.map:
            continue
        if tok.level == 0 and tok.nesting in (1, 0) and tok.type not in ("bullet_list_open", "ordered_list_open"):
            blocks.append("\n".join(lines[tok.map[0] : tok.map[1]]).strip())
        elif tok.type == "list_item_open" and tok.level == 1:
            blocks.append("\n".join(lines[tok.map[0] : tok.map[1]]).strip())
    blocks = [b for b in blocks if b]
    return blocks or [text]


def _hard_split(block: str, limit: int) -> list[str]:
    pieces, cur = [], ""
    for word in block.split(" "):
        if len(cur) + len(word) + 1 > limit and cur:
            pieces.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}" if cur else word
    if cur:
        pieces.append(cur)
    return pieces


def _split_long(text: str) -> list[str]:
    if len(text) <= MAX_CHARS:
        return [text]
    budget = MAX_CHARS - OVERLAP - 1
    units: list[str] = []
    for b in _blocks(text):
        units.extend(_hard_split(b, budget) if len(b) > budget else [b])
    pieces: list[str] = []
    cur = ""
    for u in units:
        candidate = f"{cur}\n\n{u}" if cur else u
        if len(candidate) > budget and cur:
            pieces.append(cur)
            cur = u
        else:
            cur = candidate
    if cur:
        pieces.append(cur)
    out = [pieces[0]]
    for prev, piece in zip(pieces, pieces[1:], strict=False):
        tail = prev[-OVERLAP:]
        cut = tail.find(" ")
        tail = tail[cut + 1 :] if 0 <= cut < len(tail) - 1 else tail
        out.append(f"{tail}\n{piece}")
    return out


def chunk_concept(knowledge_id: str, title: str, body: str) -> list[Chunk]:
    secs = [(h, t) for h, t in _sections(body) if h != NOT_INDEXED_SECTION and t]
    merged: list[tuple[str, str]] = []
    i = 0
    while i < len(secs):
        heading, text = secs[i]
        # Merge short sections forward (within the same file).
        while len(text) < MIN_CHARS and i + 1 < len(secs):
            nxt_heading, nxt_text = secs[i + 1]
            heading = f"{heading} / {nxt_heading}"
            text = f"{text}\n\n{nxt_heading}:\n{nxt_text}"
            i += 1
        merged.append((heading, text))
        i += 1
    chunks: list[Chunk] = []
    for heading, text in merged:
        for piece in _split_long(text):
            idx = len(chunks)
            digest = hashlib.sha256(piece.encode("utf-8")).hexdigest()
            cid = str(uuid.uuid5(CHUNK_NAMESPACE, f"{knowledge_id}|{idx}|{digest}"))
            chunks.append(Chunk(index=idx, chunk_id=cid, heading_path=f"{title} > {heading}", text=piece, chunk_hash=digest))
    return chunks
