from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from app.core.config import get_settings
from app.storage.users_repo import UsersRepository

router = APIRouter(tags=["users"])


class EnsureUserRequest(BaseModel):
    user_id: str
    email: EmailStr | None = None
    display_name: str | None = None


@router.post("/users/ensure")
def ensure_user(payload: EnsureUserRequest) -> dict[str, Any]:
    settings = get_settings()
    repo = UsersRepository(settings)
    row = repo.upsert_profile(
        user_id=payload.user_id,
        email=payload.email,
        display_name=payload.display_name,
        auth_user_id=payload.user_id,
    )
    if not row.get("id"):
        raise HTTPException(status_code=500, detail="Failed to save user")
    return {"user": row}
