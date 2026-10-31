"""Redaction of personal and customer-identifying text before it is stored on a ticket (§9.4 step 1)."""

from __future__ import annotations

import re

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
URL_WITH_QUERY = re.compile(r"https?://[^\s?#]+\?[^\s]*")
PHONE = re.compile(r"(?<![\w.])(?:\+?\d[\d\s().-]{7,}\d)(?![\w.])")


def redact(text: str, org_names: list[str] | None = None) -> str:
    out = EMAIL.sub("[email]", text or "")
    out = URL_WITH_QUERY.sub("[url]", out)
    out = PHONE.sub("[phone]", out)
    for name in sorted({n.strip() for n in (org_names or []) if n and len(n.strip()) >= 2}, key=len, reverse=True):
        out = re.sub(re.escape(name), "[customer]", out, flags=re.IGNORECASE)
    return out
