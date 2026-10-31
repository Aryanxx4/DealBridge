"""Per-requirement product-fit judgement (main model, temperature 0)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.prompts._shared import SHARED_RULES, tag

PROMPT_VERSION = "judge.v1"
TOOL = "requirement_judgement"

Status = Literal["SUPPORTED", "PARTIALLY_SUPPORTED", "NEEDS_VALIDATION", "NOT_SUPPORTED", "UNKNOWN"]


class EvidenceItem(BaseModel):
    chunk_number: int
    quote: str = Field(description="Exact words copied verbatim from that chunk (at least 20 characters)")
    role: Literal["SUPPORTS", "LIMITS", "RELATED"]


class RequirementJudgement(BaseModel):
    status: Status
    meaning: str = Field(description="What the requirement means, in plain language")
    established: str = Field(description="What the cited evidence establishes")
    unverified: str = Field(description="What remains unverified")
    next_step: str = ""
    supported_part: str | None = None
    unestablished_part: str | None = None
    evidence: list[EvidenceItem] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    questions_for_seller: list[str] = Field(default_factory=list)
    conflict: bool = False
    conflict_description: str | None = None
    key_terms: list[str] = Field(
        default_factory=list, description="Certifications, standards, products or tools explicitly named in the requirement"
    )


SYSTEM = f"""You assess ONE buyer requirement against numbered chunks of IOMETE product knowledge. Chunks are labelled
"Official documentation" or "Expert-verified answer".

Choose exactly one status:
- SUPPORTED: reliable evidence directly supports the requirement.
- PARTIALLY_SUPPORTED: evidence supports only part of the requirement or describes material limitations. Fill both
  supported_part and unestablished_part.
- NEEDS_VALIDATION: a related capability exists, but buyer-specific details or technical confirmation are needed.
  next_step must say what information or test is required.
- NOT_SUPPORTED: reliable, current evidence explicitly states a mismatch. Absence of evidence is NOT proof of non-support.
- UNKNOWN: there is insufficient reliable evidence to reach a conclusion. missing_information must say what is missing.
When unsure, choose UNKNOWN.

Rules:
- A similarity score or a topically related chunk is not evidence. Only what a chunk explicitly says counts.
- Every evidence item quotes words copied VERBATIM from its numbered chunk (at least 20 characters).
- role SUPPORTS: the chunk states the product does what is required. role LIMITS: ONLY when the chunk explicitly states
  the product does not or cannot do the thing. role RELATED: relevant context that neither supports nor limits.
- Never infer a certification, regulation, compliance status, integration or number that the chunks do not state.
- If chunks disagree (or official documentation and an expert answer conflict), set conflict=true and describe it in
  conflict_description; do not pick a side.
- key_terms: certifications, standards, products or tools explicitly named in the requirement text (copied exactly).
- questions_for_seller: concrete questions that would resolve what is unverified.
- Write meaning / established / unverified / next_step as short, plain sentences for a buyer who is not an expert.

{SHARED_RULES}"""


def build_messages(requirement: dict, chunks: list[dict]) -> list[dict]:
    parts = "\n\n".join(
        tag("retrieved_chunk", c["text"], n=str(c["n"]), label=c["label"], title=c["title"], heading=c["heading_path"]) for c in chunks
    )
    req = f"{requirement['display_id']} ({requirement['category']}, priority {requirement['priority']}): {requirement['normalized_text']}"
    return [
        {
            "role": "user",
            "content": tag("document", req, kind="buyer_requirement") + "\n\nRetrieved chunks:\n" + parts + "\n\nAssess the requirement.",
        }
    ]
