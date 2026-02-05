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
    AddPublicStrategyRequest,
    CloneMyStrategyRequest,
    CreateMyStrategyRequest,
    MyStrategyDetailResponse,
    MyStrategy,
    PublicStrategyDetail,
    PublicStrategyListItem,
    UpdateMyStrategyRequest,
    UpgradeMyStrategyRequest,
    ValidateParamsRequest,
    ValidateParamsResponse,
)
from app.storage.my_strategies_repo import MyStrategiesRepository
from app.storage.public_strategies_repo import PublicStrategiesRepository
from app.strategies.sandbox import (
    PYTHON_ENTRYPOINT,
    PYTHON_META_KEY,
    extract_python_body,
    hash_code,
    validate_python_strategy,
)


router = APIRouter()
logger = logging.getLogger("quantfairy.strategies")

DEFAULT_SAMPLE_METRICS = {
    "pnl_amount": 0.0,
    "pnl_pct": 0.0,
    "sharpe": 0.0,
    "max_drawdown_pct": 0.0,
    "win_rate_pct": 0.0,
}

DEFAULT_SAMPLE_TRADE_STATS = {
    "trades_count": 0.0,
    "avg_hold_hours": 0.0,
}

DEFAULT_POPULARITY = {
    "adds_count": 0,
    "likes_count": 0,
    "runs_count": 0,
}

DEFAULT_RULES = {
    "signal_definition": "",
    "entry_rules": "",
    "exit_rules": "",
    "rebalance_rule": "",
    "position_sizing": "",
    "risk_management": "",
}

DEFAULT_REQUIREMENTS = {"universe": {}, "data": {}}

DEFAULT_SAMPLE_BACKTEST_SPEC = {
    "period_start": "",
    "period_end": "",
    "timeframe": "",
    "universe_used": "",
    "initial_cash": 0.0,
    "fee_bps": 0.0,
    "slippage_bps": 0.0,
}

DEFAULT_SAMPLE_PERFORMANCE = {"metrics": {}, "equity_curve": []}


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
    sample_metrics = {**DEFAULT_SAMPLE_METRICS, **(row.get("sample_metrics") or {})}
    sample_trade_stats = {**DEFAULT_SAMPLE_TRADE_STATS, **(row.get("sample_trade_stats") or {})}
    popularity = {**DEFAULT_POPULARITY, **(row.get("popularity") or {})}
    return {
        "public_strategy_id": row["public_strategy_id"],
        "name": row.get("name", ""),
        "one_liner": row.get("one_liner", ""),
        "one_liner_ko": row.get("one_liner_ko"),
        "category": row.get("category", ""),
        "tags": row.get("tags", []) or [],
        "risk_level": row.get("risk_level", "mid"),
        "version": row.get("version", "1.0.0"),
        "author": {
            "name": row.get("author_name", ""),
            "type": row.get("author_type", "official"),
        },
        "sample_metrics": sample_metrics,
        "sample_trade_stats": sample_trade_stats,
        "popularity": {
            "adds_count": popularity.get("adds_count", row.get("adds_count", 0)),
            "likes_count": popularity.get("likes_count", row.get("likes_count", 0)),
            "runs_count": popularity.get("runs_count", row.get("runs_count", 0)),
        },
        "supported_assets": row.get("supported_assets", []) or [],
        "supported_timeframes": row.get("supported_timeframes", []) or [],
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }


def _format_public_detail(row: dict) -> dict:
    base = _format_public_strategy(row)
    rules = {**DEFAULT_RULES, **(row.get("rules") or {})}
    requirements = row.get("requirements") or {}
    requirements_block = {
        "universe": requirements.get("universe") or {},
        "data": requirements.get("data") or {},
    }
    sample_backtest_spec = {**DEFAULT_SAMPLE_BACKTEST_SPEC, **(row.get("sample_backtest_spec") or {})}
    sample_performance = {**DEFAULT_SAMPLE_PERFORMANCE, **(row.get("sample_performance") or {})}
    base.update(
        {
            "full_description": row.get("full_description") or "",
            "full_description_ko": row.get("full_description_ko") or "",
            "thesis": row.get("thesis") or "",
            "thesis_ko": row.get("thesis_ko") or "",
            "rules": rules,
            "param_schema": row.get("param_schema", {}) or {},
            "default_params": row.get("default_params", {}) or {},
            "recommended_presets": row.get("recommended_presets", []) or [],
            "requirements": requirements_block,
            "sample_backtest_spec": sample_backtest_spec,
            "sample_performance": sample_performance,
            "known_failure_modes": row.get("known_failure_modes", []) or [],
            "risk_disclaimer": row.get("risk_disclaimer") or "",
        }
    )
    return base


def _format_my_strategy(row: dict) -> dict:
    cleaned_params, _ = extract_python_body(row.get("params", {}) or {})
    return {
        "my_strategy_id": row["strategy_id"],
        "name": row.get("name", ""),
        "source_public_strategy_id": row.get("source_public_strategy_id", ""),
        "public_version_snapshot": row.get("public_version_snapshot", ""),
        "params": cleaned_params,
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


@router.post(
    "/public-strategies/{public_strategy_id}/add",
    response_model=MyStrategy,
)
async def add_public_strategy_to_my(
    public_strategy_id: str,
    payload: AddPublicStrategyRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    settings = get_settings()
    user_id = resolve_my_user_id(settings, authorization)
    public_repo = PublicStrategiesRepository(settings)
    my_repo = MyStrategiesRepository(settings)
    public_repo.ensure_seed()

    public_row = public_repo.get(public_strategy_id)
    if not public_row:
        raise APIError("NOT_FOUND", "Public strategy not found", status_code=404)

    existing = my_repo.get_by_source(user_id, public_strategy_id)
    if existing:
        raise APIError("CONFLICT", "Strategy already added", status_code=409)

    schema = public_row.get("param_schema", {}) or {}
    params = payload.params or public_row.get("default_params", {}) or {}
    errors = _validate_params(schema, params)
    if errors:
        raise APIError(
            "VALIDATION_ERROR",
            "Invalid params",
            details=errors,
            status_code=422,
        )

    name = payload.name or f"{public_row.get('name', 'Strategy')} copy"
    my_strategy_id = f"my_{public_strategy_id}"

    row = my_repo.create(
        user_id,
        {
            "strategy_id": my_strategy_id,
            "name": name,
            "source_public_strategy_id": public_strategy_id,
            "public_version_snapshot": public_row.get("version", ""),
            "entrypoint_snapshot": public_row.get("entrypoint"),
            "code_version_snapshot": public_row.get("code_version"),
            "params": params,
            "note": payload.note,
            "state": "idle",
        },
    )

    return _format_my_strategy(row)


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

    if payload.python:
        if payload.source_public_strategy_id:
            raise APIError(
                "VALIDATION_ERROR",
                "source_public_strategy_id is not allowed for python strategies",
                status_code=422,
            )
        validate_python_strategy(payload.python.code, payload.python.entrypoint)
        my_strategy_id = f"my_{uuid.uuid4().hex}"
        params = dict(payload.params or {})
        params[PYTHON_META_KEY] = payload.python.model_dump()
        row = my_repo.create(
            user_id,
            {
                "strategy_id": my_strategy_id,
                "name": payload.name or "Python Strategy",
                "source_public_strategy_id": "",
                "public_version_snapshot": "",
                "entrypoint_snapshot": PYTHON_ENTRYPOINT,
                "code_version_snapshot": hash_code(payload.python.code),
                "params": params,
                "note": payload.note,
                "state": "idle",
            },
        )
        return _format_my_strategy(row)

    if not payload.source_public_strategy_id:
        raise APIError("VALIDATION_ERROR", "source_public_strategy_id is required", status_code=422)
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
    current_params, current_python = extract_python_body(current.get("params", {}) or {})
    is_python = current.get("entrypoint_snapshot") == PYTHON_ENTRYPOINT or current_python is not None

    if payload.name is not None:
        updates["name"] = payload.name
    if payload.note is not None:
        updates["note"] = payload.note
    if is_python:
        if payload.python is not None:
            validate_python_strategy(payload.python.code, payload.python.entrypoint)
            current_python = payload.python
        if payload.params is not None:
            current_params = payload.params
        if current_python is not None:
            updates["params"] = {
                **(current_params or {}),
                PYTHON_META_KEY: current_python.model_dump(),
            }
            updates["entrypoint_snapshot"] = PYTHON_ENTRYPOINT
            updates["code_version_snapshot"] = hash_code(current_python.code)
    elif payload.params is not None:
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
    elif payload.python is not None:
        raise APIError(
            "VALIDATION_ERROR",
            "Python code is only allowed for python strategies",
            status_code=422,
        )

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
