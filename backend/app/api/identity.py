from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.identity import get_current_user
from app.db.session import get_db
from app.models.identity import User
from app.schemas.identity import UserOut

router = APIRouter(prefix="/identity", tags=["identity"])


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    users = db.scalars(select(User).order_by(User.role, User.display_name)).all()
    return [UserOut.of(u) for u in users]


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return UserOut.of(user)
