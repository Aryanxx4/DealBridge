from __future__ import annotations

from app.prompts import faithfulness as P
from app.services.llm.client import get_llm


def check(answer_markdown: str, chunks: list[dict]) -> P.FaithfulnessResult:
    return get_llm().complete_structured(
        "fast", P.SYSTEM, P.build_messages(answer_markdown, chunks), P.FaithfulnessResult, P.TOOL, 400, 0.0
    )
