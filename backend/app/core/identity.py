"""Demo identity resolution. NOT authentication: the caller simply names a seeded user."""

from __future__ import annotations

import uuid
from collections.abc import Callable

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.errors import AppError, forbidden_role
from app.core.logging import user_id_var
from app.db.session import get_db
from app.models.identity import User

DEMO_HEADER = "X-Demo-User-Id"


def get_current_user(
    x_demo_user_id: str | None = Header(default=None, alias=DEMO_HEADER),
    db: Session = Depends(get_db),
) -> User:
    if not x_demo_user_id:
        raise AppError("UNKNOWN_IDENTITY", f"Missing {DEMO_HEADER} header. Pick a demo identity.", 401)
    try:
        uid = uuid.UUID(x_demo_user_id)
    except ValueError:
        raise AppError("UNKNOWN_IDENTITY", "Unknown demo identity.", 401) from None
    user = db.get(User, uid)
    if user is None:
        raise AppError("UNKNOWN_IDENTITY", "Unknown demo identity.", 401)
    user_id_var.set(str(user.id))
    return user


def require_role(*roles: str) -> Callable[..., User]:
    allowed = {str(r) for r in roles}

    def _dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise forbidden_role()
        return user

    return _dep
