from __future__ import annotations

from app.prompts import answer as P
from app.services.llm.client import get_llm


def generate(question: str, chunks: list[dict], feedback: str | None = None) -> P.AnswerDraft:
    return get_llm().complete_structured("main", P.SYSTEM, P.build_messages(question, chunks, feedback), P.AnswerDraft, P.TOOL, 1500, 0.2)
