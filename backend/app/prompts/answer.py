"""Grounded answer generation (main model)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.prompts._shared import SHARED_RULES, tag

PROMPT_VERSION = "answer.v1"
TOOL = "grounded_answer"


class ProductClaim(BaseModel):
    claim: str
    chunk_number: int
    supporting_quote: str = Field(description="Exact words copied from that numbered chunk (at least 20 characters)")


class AnswerDraft(BaseModel):
    answerability: Literal["FULL", "PARTIAL", "NONE"]
    answer_markdown: str = ""
    product_claims: list[ProductClaim] = Field(default_factory=list)
    general_explanation_markdown: str | None = None
    unverified_aspects: list[str] = Field(default_factory=list)
    conflict: bool = False
    conflict_note: str | None = None


SYSTEM = f"""You answer buyer questions about the IOMETE data lakehouse platform using ONLY the numbered retrieved chunks provided.
Chunks are labelled "Official documentation" (curated from IOMETE's documentation) or "Expert-verified answer" (an answer approved
by the product team).

Rules:
(a) Every statement about IOMETE must correspond to an entry in product_claims with chunk_number and a supporting_quote copied
    VERBATIM from that numbered chunk (at least 20 characters; copy exact words, do not paraphrase inside the quote). Put inline
    markers like [1] or [2] in answer_markdown after each product statement, using the chunk numbers.
(b) General background that is not specific to IOMETE goes ONLY into general_explanation_markdown. It will be shown under the heading
    "General explanation (not specific to IOMETE)". Never put IOMETE capabilities there.
(c) If an "Expert-verified answer" chunk is marked reuse_candidate="true", prefer it, but ONLY if the new question does not differ
    from the stored question in product version, deployment environment or customer-specific conditions. Otherwise do not rely on it.
(d) If chunks disagree, set conflict to true, present both positions with their labels in answer_markdown, describe the disagreement
    in conflict_note, and do not pick one.
(e) For any certification, compliance or standards question, claim support only if a chunk explicitly names that certification or
    standard. Absence of evidence is not evidence of absence: if no chunk names it, say it could not be verified.
(f) Never say or imply that the answer cannot be wrong.
answerability:
- FULL: the chunks fully answer the question.
- PARTIAL: the chunks answer part of it; list each unanswered part in unverified_aspects.
- NONE: the chunks do not answer the question about IOMETE. For a purely general question you may still fill
  general_explanation_markdown.
Keep answer_markdown concise and plain (short paragraphs or bullets).

{SHARED_RULES}"""


def build_messages(question: str, chunks: list[dict], feedback: str | None = None) -> list[dict]:
    parts = []
    for c in chunks:
        attrs = {"n": str(c["n"]), "label": c["label"], "title": c["title"], "heading": c["heading_path"]}
        if c.get("reuse_candidate"):
            attrs["reuse_candidate"] = "true"
            attrs["stored_question"] = c.get("question_normalised", "")
        parts.append(tag("retrieved_chunk", c["text"], **attrs))
    content = (
        tag("question", question)
        + "\n\nRetrieved chunks:\n"
        + ("\n\n".join(parts) if parts else "(no chunks were retrieved)")
        + "\n\nAnswer the question following the rules."
    )
    if feedback:
        content += f"\n\nIMPORTANT: your previous draft had claims whose quotes were not found verbatim in their chunks:\n{feedback}\nFix or remove them."
    return [{"role": "user", "content": content}]
