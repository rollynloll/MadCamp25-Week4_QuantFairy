from __future__ import annotations

import base64
import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Header, Query
from jsonschema import Draft7Validator

from app.core.auth import resolve_my_user_id
from app.core.config import get_settings
from app.core.errors import APIError
from app.schemas.strategies_v1 import (
    CloneMyStrategyRequest,
    CreateMyStrategyRequest,
    MyStrategyDetailResponse,
    PublicStrategyDetail,
    PublicStrategyListItem,
    UpdateMyStrategyRequest,
    UpgradeMyStrategyRequest,
    ValidateParamsRequest,
    ValidateParamsResponse,
)
from app.storage.my_strategies_repo import MyStrategiesRepository
from app.storage.public_strategies_repo import PublicStrategiesRepository


router = APIRouter()
logger = logging.getLogger("quantfairy.strategies")


def _encode_cursor(value: str) -> str:
    raw = value.encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def _decode_cursor(cursor: str | None) -> str | None:
    if not cursor:
        return None
    try:
        return base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
    except Exception:
        return None


def _format_public_strategy(row: dict) -> dict:
    return {
        "public_strategy_id": row["public_strategy_id"],
        "name": row.get("name", ""),
        "one_liner": row.get("one_liner", ""),
        "category": row.get("category", ""),
        "tags": row.get("tags", []) or [],
        "risk_level": row.get("risk_level", "mid"),
        "version": row.get("version", "1.0.0"),
        "author": {
            "name": row.get("author_name", ""),
            "type": row.get("author_type", "official"),
        },
        "sample_metrics": row.get("sample_metrics", {}) or {},
        "sample_trade_stats": row.get("sample_trade_stats", {}) or {},
        "popularity": {
            "adds_count": row.get("adds_count", 0),
            "likes_count": row.get("likes_count", 0),
            "runs_count": row.get("runs_count", 0),
        },
        "supported_assets": row.get("supported_assets", []) or [],
        "supported_timeframes": row.get("supported_timeframes", []) or [],
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }


def _format_public_detail(row: dict) -> dict:
    base = _format_public_strategy(row)
    base.update(
        {
            "full_description": row.get("full_description", ""),
            "thesis": row.get("thesis", ""),
            "rules": row.get("rules", {}) or {},
            "param_schema": row.get("param_schema", {}) or {},
            "default_params": row.get("default_params", {}) or {},
            "recommended_presets": row.get("recommended_presets", []) or [],
            "requirements": row.get("requirements", {}) or {},
            "sample_backtest_spec": row.get("sample_backtest_spec", {}) or {},
            "sample_performance": row.get("sample_performance", {}) or {},
            "known_failure_modes": row.get("known_failure_modes", []) or [],
            "risk_disclaimer": row.get("risk_disclaimer", ""),
        }
    )
    return base


def _format_my_strategy(row: dict) -> dict:
    return {
        "my_strategy_id": row["strategy_id"],
        "name": row.get("name", ""),
        "source_public_strategy_id": row.get("source_public_strategy_id", ""),
        "public_version_snapshot": row.get("public_version_snapshot", ""),
        "params": row.get("params", {}) or {},
        "note": row.get("note"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }


def _validate_params(param_schema: dict, params: dict) -> list[dict[str, str]]:
    validator = Draft7Validator(param_schema)
    errors = []
    for error in validator.iter_errors(params):
        field = ".".join([str(p) for p in error.path])
        errors.append({"field": field, "reason": error.message})
    return errors


@router.get("/public-strategies")
async def list_public_strategies(
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    q: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    category: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    sort: str = Query(default="updated_at"),
    order: str = Query(default="desc"),
):
    settings = get_settings()
    repo = PublicStrategiesRepository(settings)
    repo.ensure_seed()

    if sort not in {"updated_at", "adds_count", "name"}:
        raise APIError("VALIDATION_ERROR", "Invalid sort", status_code=400)
    if order not in {"asc", "desc"}:
        raise APIError("VALIDATION_ERROR", "Invalid order", status_code=400)

    cursor_value = _decode_cursor(cursor)
    data = repo.list(
        {
            "q": q,
            "tag": tag,
            "category": category,
            "risk_level": risk_level,
        },
        sort,
        order,
        limit + 1,
        cursor_value,
    )

    next_cursor = None
    if len(data) > limit:
        last = data[limit - 1]
        next_cursor = _encode_cursor(str(last.get(sort)))
        data = data[:limit]

    items = [PublicStrategyListItem.model_validate(_format_public_strategy(row)).model_dump() for row in data]
    return {"items": items, "next_cursor": next_cursor}


@router.get("/public-strategies/{public_strategy_id}", response_model=PublicStrategyDetail)
async def get_public_strategy(public_strategy_id: str):
    settings = get_settings()
    repo = PublicStrategiesRepository(settings)
    row = repo.get(public_strategy_id)
    if not row:
        raise APIError("NOT_FOUND", "Public strategy not found", status_code=404)
    return PublicStrategyDetail.model_validate(_format_public_detail(row))


@router.post("/public-strategies/{public_strategy_id}/validate", response_model=ValidateParamsResponse)
async def validate_public_strategy(public_strategy_id: str, payload: ValidateParamsRequest):
    settings = get_settings()
    repo = PublicStrategiesRepository(settings)
    row = repo.get(public_strategy_id)
    if not row:
        raise APIError("NOT_FOUND", "Public strategy not found", status_code=404)

    schema = row.get("param_schema", {}) or {}
    errors = _validate_params(schema, payload.params)
    if errors:
        raise APIError(
            "VALIDATION_ERROR",
            "Invalid params",
            details=errors,
            status_code=422,
        )
    return ValidateParamsResponse(valid=True, errors=[])


@router.post("/my-strategies")
async def create_my_strategy(
    payload: CreateMyStrategyRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    settings = get_settings()
    user_id = resolve_my_user_id(settings, authorization)
    public_repo = PublicStrategiesRepository(settings)
    my_repo = MyStrategiesRepository(settings)

    public_row = public_repo.get(payload.source_public_strategy_id)
    if not public_row:
        raise APIError("NOT_FOUND", "Public strategy not found", status_code=404)

    schema = public_row.get("param_schema", {}) or {}
    errors = _validate_params(schema, payload.params)
    if errors:
        raise APIError(
            "VALIDATION_ERROR",
            "Invalid params",
            details=errors,
            status_code=422,
        )

    name = payload.name or f"{public_row.get('name', 'Strategy')} copy"
    my_strategy_id = f"my_{uuid.uuid4().hex}"

    row = my_repo.create(
        user_id,
        {
            "strategy_id": my_strategy_id,
            "name": name,
            "source_public_strategy_id": payload.source_public_strategy_id,
            "public_version_snapshot": public_row.get("version", ""),
            "entrypoint_snapshot": public_row.get("entrypoint"),
            "code_version_snapshot": public_row.get("code_version"),
            "params": payload.params,
            "note": payload.note,
        },
    )

    return _format_my_strategy(row)


@router.get("/my-strategies")
async def list_my_strategies(
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    q: str | None = Query(default=None),
    source_public_strategy_id: str | None = Query(default=None),
    sort: str = Query(default="updated_at"),
    order: str = Query(default="desc"),
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    settings = get_settings()
    user_id = resolve_my_user_id(settings, authorization)
    repo = MyStrategiesRepository(settings)

    if sort not in {"updated_at", "created_at", "name"}:
        raise APIError("VALIDATION_ERROR", "Invalid sort", status_code=400)
    if order not in {"asc", "desc"}:
        raise APIError("VALIDATION_ERROR", "Invalid order", status_code=400)

    cursor_value = _decode_cursor(cursor)
    data = repo.list(
        user_id,
        {
            "q": q,
            "source_public_strategy_id": source_public_strategy_id,
        },
        sort,
        order,
        limit + 1,
        cursor_value,
    )

    next_cursor = None
    if len(data) > limit:
        last = data[limit - 1]
        next_cursor = _encode_cursor(str(last.get(sort)))
        data = data[:limit]

    items = [_format_my_strategy(row) for row in data]
    return {"items": items, "next_cursor": next_cursor}


@router.get("/my-strategies/{my_strategy_id}", response_model=MyStrategyDetailResponse)
async def get_my_strategy(
    my_strategy_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    settings = get_settings()
    user_id = resolve_my_user_id(settings, authorization)
    my_repo = MyStrategiesRepository(settings)
    public_repo = PublicStrategiesRepository(settings)

    row = my_repo.get(user_id, my_strategy_id)
    if not row:
        raise APIError("NOT_FOUND", "My strategy not found", status_code=404)

    public_row = public_repo.get(row.get("source_public_strategy_id"))
    brief = {
        "public_strategy_id": row.get("source_public_strategy_id"),
        "name": public_row.get("name") if public_row else "",
        "version": public_row.get("version") if public_row else row.get("public_version_snapshot"),
    }

    return MyStrategyDetailResponse(
        my_strategy=_format_my_strategy(row),
        public_strategy_brief=brief,
    )


@router.patch("/my-strategies/{my_strategy_id}")
async def update_my_strategy(
    my_strategy_id: str,
    payload: UpdateMyStrategyRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    settings = get_settings()
    user_id = resolve_my_user_id(settings, authorization)
    my_repo = MyStrategiesRepository(settings)
    public_repo = PublicStrategiesRepository(settings)

    current = my_repo.get(user_id, my_strategy_id)
    if not current:
        raise APIError("NOT_FOUND", "My strategy not found", status_code=404)

    updates: dict[str, Any] = {}
    if payload.name is not None:
        updates["name"] = payload.name
    if payload.note is not None:
        updates["note"] = payload.note
    if payload.params is not None:
        public_row = public_repo.get(current.get("source_public_strategy_id"))
        if not public_row:
            raise APIError("NOT_FOUND", "Public strategy not found", status_code=404)
        schema = public_row.get("param_schema", {}) or {}
        errors = _validate_params(schema, payload.params)
        if errors:
            raise APIError(
                "VALIDATION_ERROR",
                "Invalid params",
                details=errors,
                status_code=422,
            )
        updates["params"] = payload.params

    updated = my_repo.update(user_id, my_strategy_id, updates)
    if not updated:
        raise APIError("NOT_FOUND", "My strategy not found", status_code=404)
    return _format_my_strategy(updated)


@router.delete("/my-strategies/{my_strategy_id}", status_code=204)
async def delete_my_strategy(
    my_strategy_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    settings = get_settings()
    user_id = resolve_my_user_id(settings, authorization)
    my_repo = MyStrategiesRepository(settings)

    current = my_repo.get(user_id, my_strategy_id)
    if not current:
        raise APIError("NOT_FOUND", "My strategy not found", status_code=404)

    my_repo.delete(user_id, my_strategy_id)
    return None


@router.post("/my-strategies/{my_strategy_id}/clone")
async def clone_my_strategy(
    my_strategy_id: str,
    payload: CloneMyStrategyRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    settings = get_settings()
    user_id = resolve_my_user_id(settings, authorization)
    my_repo = MyStrategiesRepository(settings)

    current = my_repo.get(user_id, my_strategy_id)
    if not current:
        raise APIError("NOT_FOUND", "My strategy not found", status_code=404)

    params = current.get("params", {}) or {}
    params.update(payload.params_overrides)

    new_id = f"my_{uuid.uuid4().hex}"
    row = my_repo.create(
        user_id,
        {
            "strategy_id": new_id,
            "name": payload.name,
            "source_public_strategy_id": current.get("source_public_strategy_id"),
            "public_version_snapshot": current.get("public_version_snapshot"),
            "entrypoint_snapshot": current.get("entrypoint_snapshot"),
            "code_version_snapshot": current.get("code_version_snapshot"),
            "params": params,
            "note": current.get("note"),
        },
    )
    return _format_my_strategy(row)


@router.post("/my-strategies/{my_strategy_id}/upgrade")
async def upgrade_my_strategy(
    my_strategy_id: str,
    payload: UpgradeMyStrategyRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    settings = get_settings()
    user_id = resolve_my_user_id(settings, authorization)
    my_repo = MyStrategiesRepository(settings)
    public_repo = PublicStrategiesRepository(settings)

    current = my_repo.get(user_id, my_strategy_id)
    if not current:
        raise APIError("NOT_FOUND", "My strategy not found", status_code=404)

    public_row = public_repo.get(current.get("source_public_strategy_id"))
    if not public_row:
        raise APIError("NOT_FOUND", "Public strategy not found", status_code=404)

    updates: dict[str, Any] = {
        "public_version_snapshot": public_row.get("version", current.get("public_version_snapshot")),
        "entrypoint_snapshot": public_row.get("entrypoint", current.get("entrypoint_snapshot")),
        "code_version_snapshot": public_row.get("code_version", current.get("code_version_snapshot")),
    }

    updated = my_repo.update(user_id, my_strategy_id, updates)
    if not updated:
        raise APIError("NOT_FOUND", "My strategy not found", status_code=404)
    return _format_my_strategy(updated)
