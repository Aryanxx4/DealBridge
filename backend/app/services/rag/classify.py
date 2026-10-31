from __future__ import annotations

from app.prompts import classify as P
from app.services.llm.client import get_llm


def classify(history: list[dict], question: str) -> P.Classification:
    return get_llm().complete_structured("fast", P.SYSTEM, P.build_messages(history, question), P.Classification, P.TOOL, 400, 0.0)
