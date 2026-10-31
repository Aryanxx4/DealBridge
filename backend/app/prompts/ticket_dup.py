"""Same-intent check between a new unanswered question and an existing ticket (fast model)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.prompts._shared import SHARED_RULES, tag

PROMPT_VERSION = "ticket_dup.v1"
TOOL = "duplicate_check"


class TicketDupResult(BaseModel):
    same_intent: bool
    differing_qualifiers: list[str] = Field(default_factory=list)


SYSTEM = f"""Decide whether two product questions ask for the same information.
same_intent is true only if one answer would fully answer both. List every differing qualifier: product version, deployment
environment (for example on-premises vs cloud vs air-gapped), scale or numbers, specific tools, regulations or customer-specific
conditions. Similar wording is not enough.

{SHARED_RULES}"""


def build_messages(new_question: str, existing_question: str) -> list[dict]:
    return [
        {
            "role": "user",
            "content": tag("ticket", existing_question, which="existing") + "\n\n" + tag("question", new_question, which="new"),
        }
    ]
