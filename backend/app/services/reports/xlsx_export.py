"""Excel export (P1): a Requirements sheet and an Evidence sheet from the results payload."""

from __future__ import annotations

import io

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from app.services.reports.pdf_report import DISCLAIMER, PRIORITY_TEXT, STATUS_TEXT


def _sheet(ws, headers: list[str], rows: list[list], widths: list[int]) -> None:
    ws.append(headers)
    for c in ws[1]:
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="EEF2FF")
    for r in rows:
        ws.append([_safe(v) for v in r])
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A2"


def _safe(v):
    """Neutralise spreadsheet formula injection from buyer- or seller-provided text."""
    if isinstance(v, str) and v[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + v
    return v


def build_xlsx(results: dict) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Requirements"
    reqs = results["requirements"]
    _sheet(
        ws,
        [
            "ID",
            "Requirement",
            "Category",
            "Priority",
            "Status",
            "Blocker",
            "What the evidence establishes",
            "What remains unverified",
            "Next step",
            "Missing information",
            "Questions for the seller",
            "Evidence count",
        ],
        [
            [
                r["display_id"],
                r["text"],
                r["category"],
                PRIORITY_TEXT[r["priority"]],
                STATUS_TEXT[r["status"]],
                "Yes" if r["is_blocker"] else "No",
                (r.get("explanation") or {}).get("established"),
                (r.get("explanation") or {}).get("unverified"),
                (r.get("explanation") or {}).get("next_step"),
                "; ".join(r.get("missing_information") or []),
                "; ".join(r.get("questions_for_seller") or []),
                len(r.get("evidence") or []),
            ]
            for r in reqs
        ],
        [10, 60, 26, 14, 20, 9, 50, 50, 40, 40, 40, 10],
    )
    ev = wb.create_sheet("Evidence")
    _sheet(
        ev,
        ["Requirement ID", "Role", "Source label", "Title", "Heading", "Source URL", "Excerpt", "Version", "Last verified / approved"],
        [
            [
                r["display_id"],
                e["role"],
                e["label"],
                e["title"],
                e.get("heading_path"),
                e.get("source_url"),
                e["excerpt"],
                e.get("version"),
                e.get("last_verified_at") or e.get("approved_at"),
            ]
            for r in reqs
            for e in r.get("evidence") or []
        ],
        [14, 10, 24, 34, 40, 50, 80, 8, 20],
    )
    info = wb.create_sheet("About")
    info.append(["Assessment", results["assessment"]["title"]])
    info.append(["Version", results["version"]["version_no"]])
    info.append(["Analysed", str(results["version"]["analyzed_at"])])
    info.append(["Disclaimer", DISCLAIMER])
    info.column_dimensions["B"].width = 120
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
