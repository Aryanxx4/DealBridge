"""Deterministic guardrails G1-G8 applied to every LLM judgement (§10.8 step d).

Each automatic downgrade appends a sentence to guardrail_notes so the buyer can see why the status changed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.prompts.judge import EvidenceItem, RequirementJudgement
from app.services.retrieval.quote_verify import contains_term, verify_quote

DEFAULT_NEXT_STEP = "Confirm this requirement with the vendor, including your environment's specifics, and test it before relying on it."
DEFAULT_MISSING = "Product documentation that explicitly addresses this requirement."
DEFAULT_CONFLICT = "The available sources disagree on this requirement; both positions are shown and need review."

_STANDARDS = re.compile(
    r"\b(soc\s?[123]|iso[\s/-]?(iec[\s-]?)?\d{4,5}|hipaa|hitrust|pci[\s-]?dss|gdpr|ccpa|fedramp|fips[\s-]?\d*|nist|sox|dora|nis\s?2|"
    r"csa\s?star|c5|iso|certif\w*|complian\w*|accredit\w*|attest\w*)\b",
    re.IGNORECASE,
)
_CODE_LIKE = re.compile(r"\b[A-Z]{2,}[-\s]?\d{2,}[A-Z0-9-]*\b")


def is_certification_or_standard(term: str) -> bool:
    return bool(_STANDARDS.search(term) or _CODE_LIKE.search(term))


@dataclass
class GuardedResult:
    status: str
    evidence: list[EvidenceItem]
    notes: list[str] = field(default_factory=list)
    next_step: str = ""
    missing_information: list[str] = field(default_factory=list)
    has_conflict: bool = False
    conflict_description: str | None = None
    key_terms: list[str] = field(default_factory=list)


def apply_guardrails(
    j: RequirementJudgement,
    chunks_by_n: dict[int, dict],
    requirement_text: str,
    category: str,
    clarification_waived: bool,
) -> GuardedResult:
    notes: list[str] = []
    status = j.status

    # G1: drop every evidence item whose quote is not verbatim in its chunk.
    verified = [e for e in j.evidence if e.chunk_number in chunks_by_n and verify_quote(chunks_by_n[e.chunk_number]["text"], e.quote)]
    dropped = len(j.evidence) - len(verified)
    if dropped:
        notes.append(f"{dropped} cited excerpt(s) could not be found verbatim in the source and were discarded.")
    supports = [e for e in verified if e.role == "SUPPORTS"]
    limits = [e for e in verified if e.role == "LIMITS"]

    # G2: SUPPORTED needs at least one verified SUPPORTS item.
    if status == "SUPPORTED" and not supports:
        status = "UNKNOWN" if not verified else "NEEDS_VALIDATION"
        notes.append(f"Changed from Supported to {_label(status)}: no verified excerpt supports the requirement.")
    # G3: NOT_SUPPORTED needs at least one verified LIMITS item (absence of evidence is not non-support).
    if status == "NOT_SUPPORTED" and not limits:
        status = "UNKNOWN"
        notes.append("Changed from Not supported to Unknown: no verified excerpt explicitly states a limitation.")
    # G4: PARTIALLY_SUPPORTED needs both parts and a verified SUPPORTS item.
    if status == "PARTIALLY_SUPPORTED" and not ((j.supported_part or "").strip() and (j.unestablished_part or "").strip() and supports):
        status = "NEEDS_VALIDATION"
        notes.append("Changed from Partially supported to Needs validation: the supported and unestablished parts were not both evidenced.")

    # G6: key terms must occur in the requirement; remaining terms must appear in supporting evidence.
    key_terms = [t for t in j.key_terms if t.strip() and contains_term(requirement_text, t)]
    discarded = [t for t in j.key_terms if t not in key_terms]
    if discarded:
        notes.append(f"Ignored key term(s) not present in the requirement: {', '.join(discarded)}.")
    support_text = " ".join(chunks_by_n[e.chunk_number]["text"] for e in supports)
    missing_terms = [t for t in key_terms if not contains_term(support_text, t)]
    if status == "SUPPORTED" and missing_terms:
        strict = category == "COMPLIANCE_GOVERNANCE" or any(is_certification_or_standard(t) for t in missing_terms)
        status = "UNKNOWN" if strict else "NEEDS_VALIDATION"
        notes.append(f"Changed from Supported to {_label(status)}: {', '.join(missing_terms)} is not named in the supporting evidence.")

    # G7: conflicts are never resolved silently.
    has_conflict = bool(j.conflict) or any(s.chunk_number != lim.chunk_number for s in supports for lim in limits)
    conflict_description = (j.conflict_description or "").strip() or None
    if has_conflict:
        if status != "NEEDS_VALIDATION":
            notes.append(f"Changed from {_label(status)} to Needs validation: sources conflict.")
        status = "NEEDS_VALIDATION"
        if not conflict_description:
            conflict_description = DEFAULT_CONFLICT

    # G8: a vague requirement kept as written is never Supported.
    if clarification_waived and status == "SUPPORTED":
        status = "NEEDS_VALIDATION"
        notes.append("Changed from Supported to Needs validation: the requirement is vague and was kept as written.")

    # G5: required explanations (applied last so late downgrades are covered too).
    next_step = (j.next_step or "").strip()
    missing = [m for m in j.missing_information if m.strip()]
    if status == "NEEDS_VALIDATION" and not next_step:
        next_step = DEFAULT_NEXT_STEP
        notes.append("Added a default next step.")
    if status == "UNKNOWN" and not missing:
        missing = [DEFAULT_MISSING]
        notes.append("Added default missing information.")

    order = {"SUPPORTS": 0, "LIMITS": 1, "RELATED": 2}
    return GuardedResult(
        status=status,
        evidence=sorted(verified, key=lambda e: order[e.role]),
        notes=notes,
        next_step=next_step,
        missing_information=missing,
        has_conflict=has_conflict,
        conflict_description=conflict_description if has_conflict else None,
        key_terms=key_terms,
    )


def _label(status: str) -> str:
    return {
        "SUPPORTED": "Supported",
        "PARTIALLY_SUPPORTED": "Partially supported",
        "NEEDS_VALIDATION": "Needs validation",
        "NOT_SUPPORTED": "Not supported",
        "UNKNOWN": "Unknown",
    }[status]
