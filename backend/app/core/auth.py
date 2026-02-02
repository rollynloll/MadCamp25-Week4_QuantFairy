from __future__ import annotations

from app.core.config import Settings
from app.core.errors import APIError
from app.storage.users_repo import UsersRepository


def require_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise APIError("UNAUTHORIZED", "Authorization required", status_code=401)
    if not authorization.lower().startswith("bearer "):
        raise APIError("UNAUTHORIZED", "Invalid authorization scheme", status_code=401)
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise APIError("UNAUTHORIZED", "Token missing", status_code=401)
    return token


def resolve_my_user_id(settings: Settings, authorization: str | None) -> str:
    if settings.api_token:
        token = require_bearer_token(authorization)
        if token != settings.api_token:
            raise APIError("FORBIDDEN", "Invalid token", status_code=403)

    if settings.default_user_id:
        return settings.default_user_id

    users_repo = UsersRepository(settings)
    user = users_repo.get_any()
    if user and user.get("id"):
        return user["id"]

    raise APIError(
        "USER_ID_REQUIRED",
        "User id is required",
        "Set DEFAULT_USER_ID or create an app_users record",
        status_code=401,
    )
