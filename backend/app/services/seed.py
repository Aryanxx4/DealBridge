"""Demo identities with deterministic ids."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.enums import OrgKind, UserRole
from app.models.identity import Organization, User

NAMESPACE = uuid.UUID("6f1c2d3e-4b5a-4c6d-8e7f-9a0b1c2d3e4f")


def demo_id(key: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, key)


ORGS = [
    ("org:finbank", "FinBank", OrgKind.BUYER_ORG),
    ("org:northwind", "Northwind Retail", OrgKind.BUYER_ORG),
    ("org:iomete-sales", "IOMETE Sales", OrgKind.SELLER_ORG),
    ("org:dealbridge-product", "DealBridge Product Team", OrgKind.INTERNAL),
]

USERS = [
    ("user:priya", "Priya Nair", "priya.nair@finbank.example", UserRole.BUYER, "org:finbank"),
    ("user:daniel", "Daniel Okoye", "daniel.okoye@northwind.example", UserRole.BUYER, "org:northwind"),
    ("user:meera", "Meera Kapoor", "meera.kapoor@sales.example", UserRole.SELLER, "org:iomete-sales"),
    ("user:arjun", "Arjun Rao", "arjun.rao@sales.example", UserRole.SELLER, "org:iomete-sales"),
    ("user:sam", "Sam Admin", "sam.admin@dealbridge.example", UserRole.ADMIN, "org:dealbridge-product"),
]


def seed_identities(db: Session) -> dict[str, int]:
    created = {"organizations": 0, "users": 0}
    for key, name, kind in ORGS:
        if db.get(Organization, demo_id(key)) is None:
            db.add(Organization(id=demo_id(key), name=name, kind=kind.value))
            created["organizations"] += 1
    db.flush()
    for key, name, email, role, org in USERS:
        if db.get(User, demo_id(key)) is None:
            db.add(User(id=demo_id(key), display_name=name, email=email, role=role.value, organization_id=demo_id(org)))
            created["users"] += 1
    db.flush()
    return created
