from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class JobOut(BaseModel):
    id: uuid.UUID
    type: str
    status: str
    assessment_id: uuid.UUID | None
    progress_done: int
    progress_total: int
    progress_message: str | None
    result: dict | None
    error_code: str | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    @classmethod
    def of(cls, j) -> JobOut:
        return cls(**{k: getattr(j, k) for k in cls.model_fields})


class JobAccepted(BaseModel):
    job_id: uuid.UUID
