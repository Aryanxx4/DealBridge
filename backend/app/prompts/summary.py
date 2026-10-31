"""Executive summary and next steps from structured results only (main model)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.prompts._shared import SHARED_RULES, tag

PROMPT_VERSION = "summary.v1"
TOOL = "assessment_summary"


class AssessmentSummary(BaseModel):
    executive_summary: str = Field(description="At most 120 words")
    next_steps: list[str] = Field(default_factory=list, max_length=8)


SYSTEM = f"""You write the executive summary of a preliminary, evidence-based product-fit assessment for a buyer.
You receive ONLY structured results (statuses, short explanations, blockers). Do not introduce any capability,
certification, integration or number that is not in the results. Say plainly how many requirements are supported,
partly supported, need validation, are not supported or are unknown, and name the potential blockers.
executive_summary: at most 120 words. next_steps: at most 8 concrete actions (for example questions to put to the
vendor, tests to run). Do not compute or mention any overall fit score or percentage.

{SHARED_RULES}"""


def build_messages(results: list[dict], blockers: list[str], counts: dict) -> list[dict]:
    lines = "\n".join(
        f"{r['display_id']} [{r['priority']}] {r['status']}: {r['text']} | established: {r['established']} | unverified: {r['unverified']}"
        for r in results
    )
    return [
        {
            "role": "user",
            "content": tag(
                "document",
                f"Status counts: {counts}\nPotential blockers: {', '.join(blockers) or 'none'}\n\n{lines}",
                kind="structured_results",
            )
            + "\n\nWrite the summary.",
        }
    ]
