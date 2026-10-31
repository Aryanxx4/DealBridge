"""Conversational requirement intake (main model)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.prompts._shared import SHARED_RULES, tag
from app.prompts.extract_pdf import Category, PriorityT

PROMPT_VERSION = "intake_chat.v1"
TOOL = "intake_turn"


class ProposedOp(BaseModel):
    op: Literal["ADD", "UPDATE", "REMOVE"]
    target_display_id: str | None = Field(default=None, description="Required for UPDATE and REMOVE, e.g. REQ-003")
    normalized_text: str | None = None
    category: Category | None = None
    priority: PriorityT | None = None
    priority_basis: str | None = None
    source_quote: str = Field(description="The words from the buyer's message that justify this operation, copied exactly")


class IntakeTurn(BaseModel):
    assistant_message: str
    clarifying_questions: list[str] = Field(default_factory=list, max_length=3)
    proposed_ops: list[ProposedOp] = Field(default_factory=list)
    assumptions_noted: list[str] = Field(default_factory=list)
    is_ambiguous: bool = False


SYSTEM = f"""You help a buyer capture their requirements for evaluating a data platform. You receive their current
requirement list and the conversation, and you propose structured changes. The buyer reviews and applies every change
explicitly; you never apply anything yourself.

Rules:
- One ADD per atomic requirement, preserving every qualifier (numbers, versions, environments, conditions).
- Never record an assumption as a requirement: an assumption becomes a clarifying question (and goes in assumptions_noted).
- Never infer a legal or compliance requirement from vague wording; ask which regulation or certification is meant.
- UPDATE or REMOVE only when the buyer clearly identifies the requirement by id or by an unambiguous description.
  Otherwise ask which one and emit no op for it.
- Example: "We no longer require air-gapped deployment, but hybrid deployment is now mandatory" must produce a REMOVE
  for the existing air-gapped requirement and an ADD for hybrid deployment with priority HIGH (priority_basis "mandatory").
- Priority only from explicit wording (must/shall/mandatory/required -> HIGH; critical/non-negotiable -> CRITICAL;
  should/preferred -> MEDIUM; nice to have/optional -> LOW; otherwise NOT_SPECIFIED).
- source_quote must be copied exactly from the buyer's latest message.
- Do not evaluate the product or state any product capability.
- assistant_message: a short, friendly reply summarising the proposed changes and asking any clarifying questions
  (at most 3).

{SHARED_RULES}"""


def build_messages(requirements: list[dict], history: list[dict], message: str) -> list[dict]:
    reqs = (
        "\n".join(
            f"{r['display_id']} [{r['category']}, {r['priority']}, {'confirmed' if r['buyer_confirmed'] else 'unconfirmed'}]: {r['normalized_text']}"
            for r in requirements
        )
        or "(no requirements yet)"
    )
    convo = "\n".join(f"{m['role'].lower()}: {m['content'][:1000]}" for m in history[-10:]) or "(no earlier messages)"
    return [
        {
            "role": "user",
            "content": tag("requirements", reqs)
            + "\n\n"
            + tag("conversation", convo)
            + "\n\n"
            + tag("buyer_message", message)
            + "\n\nPropose the intake turn.",
        }
    ]
