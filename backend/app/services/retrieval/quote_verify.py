"""Deterministic quote verification: a cited quote must literally occur in its source text.

Normalisation: lowercase, strip zero-width characters, unify dashes and apostrophes, strip markdown emphasis
markers and quotation marks, collapse whitespace. A quote must be at least MIN_QUOTE_CHARS long after
normalisation.
"""

from __future__ import annotations

import re
import unicodedata

MIN_QUOTE_CHARS = 20

_ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍⁠﻿"), None)
_TRANSLATE = str.maketrans(
    {
        "‘": "'",
        "’": "'",
        "“": "",
        "”": "",
        '"': "",
        "–": "-",
        "—": "-",
        " ": " ",
        "*": "",
        "`": "",
    }
)
_WS = re.compile(r"\s+")
# Markdown emphasis with underscores (_x_ / __x__) only at word boundaries, so snake_case survives.
_UNDERSCORE_EMPH = re.compile(r"(?<!\w)_{1,2}([^_\n]+?)_{1,2}(?!\w)")
_BLOCKQUOTE = re.compile(r"^\s*>\s?", re.MULTILINE)


def normalize(text: str) -> str:
    if not text:
        return ""
    t = unicodedata.normalize("NFKC", text).translate(_ZERO_WIDTH)
    t = _BLOCKQUOTE.sub("", t)
    t = _UNDERSCORE_EMPH.sub(r"\1", t)
    t = t.translate(_TRANSLATE)
    t = t.lower()
    return _WS.sub(" ", t).strip()


def verify_quote(chunk_text: str, quote: str) -> bool:
    """True only if the normalised quote is a substring of the normalised chunk and long enough."""
    q = normalize(quote)
    if len(q) < MIN_QUOTE_CHARS:
        return False
    return q in normalize(chunk_text)


def contains_term(text: str, term: str) -> bool:
    """Normalised, word-boundary-aware containment (used for certification and key-term checks)."""
    t, n = normalize(term), normalize(text)
    if not t:
        return False
    return re.search(r"(?<![a-z0-9])" + re.escape(t) + r"(?![a-z0-9])", n) is not None
