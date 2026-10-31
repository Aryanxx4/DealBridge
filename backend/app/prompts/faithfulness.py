"""Second-stage faithfulness check of an answer against its cited chunks (fast model)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.prompts._shared import SHARED_RULES, tag

PROMPT_VERSION = "faithfulness.v1"
TOOL = "faithfulness_check"


class FaithfulnessResult(BaseModel):
    faithful: bool
    unsupported_statements: list[str] = Field(default_factory=list)


SYSTEM = f"""You check whether an answer about the IOMETE platform is fully supported by the cited chunks.
Mark faithful=false if ANY statement about IOMETE in the answer is not directly supported by the chunks (including added
numbers, certifications, integrations, versions or guarantees). Statements clearly presented as general background are allowed.
List each unsupported statement.

{SHARED_RULES}"""


def build_messages(answer_markdown: str, chunks: list[dict]) -> list[dict]:
    parts = "\n\n".join(tag("retrieved_chunk", c["text"], n=str(c["n"]), label=c["label"]) for c in chunks)
    return [{"role": "user", "content": tag("answer", answer_markdown) + "\n\nCited chunks:\n" + parts}]
