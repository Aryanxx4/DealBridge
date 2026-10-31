from __future__ import annotations

import uuid

from pydantic import BaseModel


class OrganizationOut(BaseModel):
    id: uuid.UUID
    name: str
    kind: str


class UserOut(BaseModel):
    id: uuid.UUID
    display_name: str
    email: str
    role: str
    organization: OrganizationOut

    @classmethod
    def of(cls, u) -> UserOut:
        org = u.organization
        return cls(
            id=u.id,
            display_name=u.display_name,
            email=u.email,
            role=u.role,
            organization=OrganizationOut(id=org.id, name=org.name, kind=org.kind),
        )
