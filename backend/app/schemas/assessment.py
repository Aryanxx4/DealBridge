from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AssessmentContext(BaseModel):
    organisation_name: str | None = Field(default=None, max_length=200)
    industry: str | None = Field(default=None, max_length=200)
    use_case: str | None = Field(default=None, max_length=4000)


class AssessmentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    context: AssessmentContext = Field(default_factory=AssessmentContext)


class AssessmentPatch(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=120)
    context: AssessmentContext | None = None


class AssessmentOut(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    context: dict
    intake_form: dict | None
    requirement_set_revision: int
    latest_version_no: int
    requirement_count: int = 0
    confirmed_count: int = 0
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, a, requirement_count: int = 0, confirmed_count: int = 0) -> AssessmentOut:
        return cls(
            id=a.id,
            title=a.title,
            status=a.status,
            context=a.context or {},
            intake_form=a.intake_form,
            requirement_set_revision=a.requirement_set_revision,
            latest_version_no=a.latest_version_no,
            requirement_count=requirement_count,
            confirmed_count=confirmed_count,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )


class DocumentOut(BaseModel):
    id: uuid.UUID
    original_filename: str
    size_bytes: int
    page_count: int
    sha256: str
    extraction_status: str
    extraction_message: str | None
    created_at: datetime

    @classmethod
    def of(cls, d) -> DocumentOut:
        return cls(**{k: getattr(d, k) for k in cls.model_fields})


class RequirementOut(BaseModel):
    id: uuid.UUID
    display_id: str
    seq: int
    original_text: str
    normalized_text: str
    category: str
    priority: str
    priority_basis: str | None
    source_type: str
    source_reference: dict
    buyer_confirmed: bool
    needs_clarification: bool
    clarifying_question: str | None
    clarification_waived: bool
    is_removed: bool
    removed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, r) -> RequirementOut:
        return cls(**{k: getattr(r, k) for k in cls.model_fields})


class RequirementCreate(BaseModel):
    normalized_text: str = Field(min_length=5, max_length=1000)
    category: str = "OTHER"
    priority: str = "NOT_SPECIFIED"


class RequirementPatch(BaseModel):
    normalized_text: str | None = Field(default=None, min_length=5, max_length=1000)
    category: str | None = None
    priority: str | None = None
    original_text: str | None = None  # rejected by the service (immutable); present so the error is explicit


class ExtractRequest(BaseModel):
    document_id: uuid.UUID


class IntakeMessageIn(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class ApplyProposalIn(BaseModel):
    selected_op_indexes: list[int] | None = None
