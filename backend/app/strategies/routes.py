from __future__ import annotations

from fastapi import APIRouter, Header, Query

from app.core.auth import resolve_my_user_id
from app.core.config import get_settings
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
from app.services.strategy_service import StrategyService

router = APIRouter()


def _svc(authorization: str | None = None) -> StrategyService:
    return StrategyService(get_settings())


def _user(authorization: str | None) -> str:
    return resolve_my_user_id(get_settings(), authorization)


@router.get("/public-strategies")
async def list_public_strategies(limit: int = Query(default=20, ge=1, le=100), cursor: str | None = Query(default=None), q: str | None = Query(default=None), tag: str | None = Query(default=None), category: str | None = Query(default=None), risk_level: str | None = Query(default=None), sort: str = Query(default="updated_at"), order: str = Query(default="desc")):
    return _svc().list_public(limit=limit, cursor=cursor, q=q, tag=tag, category=category, risk_level=risk_level, sort=sort, order=order)


@router.get("/public-strategies/{public_strategy_id}", response_model=PublicStrategyDetail)
async def get_public_strategy(public_strategy_id: str):
    return _svc().get_public(public_strategy_id)


@router.post("/public-strategies/{public_strategy_id}/add", response_model=MyStrategy)
async def add_public_strategy_to_my(public_strategy_id: str, payload: AddPublicStrategyRequest, authorization: str | None = Header(default=None, alias="Authorization")):
    return _svc().add_public_to_my(_user(authorization), public_strategy_id, payload)


@router.post("/public-strategies/{public_strategy_id}/validate", response_model=ValidateParamsResponse)
async def validate_public_strategy(public_strategy_id: str, payload: ValidateParamsRequest):
    return _svc().validate_public(public_strategy_id, payload)


@router.post("/my-strategies")
async def create_my_strategy(payload: CreateMyStrategyRequest, authorization: str | None = Header(default=None, alias="Authorization")):
    return _svc().create_my(_user(authorization), payload)


@router.get("/my-strategies")
async def list_my_strategies(limit: int = Query(default=20, ge=1, le=100), cursor: str | None = Query(default=None), q: str | None = Query(default=None), source_public_strategy_id: str | None = Query(default=None), sort: str = Query(default="updated_at"), order: str = Query(default="desc"), authorization: str | None = Header(default=None, alias="Authorization")):
    return _svc().list_my(_user(authorization), limit=limit, cursor=cursor, q=q, source_public_strategy_id=source_public_strategy_id, sort=sort, order=order)


@router.get("/my-strategies/{my_strategy_id}", response_model=MyStrategyDetailResponse)
async def get_my_strategy(my_strategy_id: str, authorization: str | None = Header(default=None, alias="Authorization")):
    return _svc().get_my(_user(authorization), my_strategy_id)


@router.patch("/my-strategies/{my_strategy_id}")
async def update_my_strategy(my_strategy_id: str, payload: UpdateMyStrategyRequest, authorization: str | None = Header(default=None, alias="Authorization")):
    return _svc().update_my(_user(authorization), my_strategy_id, payload)


@router.delete("/my-strategies/{my_strategy_id}", status_code=204)
async def delete_my_strategy(my_strategy_id: str, authorization: str | None = Header(default=None, alias="Authorization")):
    _svc().delete_my(_user(authorization), my_strategy_id)


@router.post("/my-strategies/{my_strategy_id}/clone")
async def clone_my_strategy(my_strategy_id: str, payload: CloneMyStrategyRequest, authorization: str | None = Header(default=None, alias="Authorization")):
    return _svc().clone_my(_user(authorization), my_strategy_id, payload)


@router.post("/my-strategies/{my_strategy_id}/upgrade")
async def upgrade_my_strategy(my_strategy_id: str, payload: UpgradeMyStrategyRequest, authorization: str | None = Header(default=None, alias="Authorization")):
    return _svc().upgrade_my(_user(authorization), my_strategy_id, payload)
