from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.errors import APIError
from app.core.time import now_kst
from app.schemas.strategies import (
    StrategyDetail,
    StrategyListResponse,
    StrategyStateUpdateRequest,
    StrategyStateUpdateResponse,
)
from app.storage.strategies_repo import StrategiesRepository


router = APIRouter()


@router.get("/strategies", response_model=StrategyListResponse)
async def list_strategies():
    settings = get_settings()
    repo = StrategiesRepository(settings)
    items = []
    allowed_states = {"running", "paused", "idle", "error"}
    for strat in repo.list():
        state = strat.get("state") if strat.get("state") in allowed_states else "idle"
        updated_at = strat.get("updated_at") or now_kst()
        items.append(
            {
                "strategy_id": strat["strategy_id"],
                "name": strat["name"],
                "state": state,
                "description": strat.get("description", ""),
                "positions_count": int(strat.get("positions_count", 0)),
                "pnl_today": {
                    "value": float(strat.get("pnl_today_value", 0)),
                    "pct": float(strat.get("pnl_today_pct", 0)),
                },
                "updated_at": updated_at,
            }
        )
    return StrategyListResponse(items=items)


@router.get("/strategies/{strategy_id}", response_model=StrategyDetail)
async def get_strategy(strategy_id: str):
    settings = get_settings()
    repo = StrategiesRepository(settings)
    strat = repo.get(strategy_id)
    if not strat:
        raise APIError(
            "STRATEGY_NOT_FOUND", f"Strategy {strategy_id} not found", status_code=404
        )
    created_at = strat.get("created_at") or now_kst()
    updated_at = strat.get("updated_at") or now_kst()
    allowed_states = {"running", "paused", "idle", "error"}
    state = strat.get("state") if strat.get("state") in allowed_states else "idle"
    return StrategyDetail(
        strategy_id=strat["strategy_id"],
        name=strat["name"],
        state=state,
        description=strat.get("description", ""),
        params=strat.get("params", {}),
        risk_limits=strat.get("risk_limits", {}),
        created_at=created_at,
        updated_at=updated_at,
    )


@router.post(
    "/strategies/{strategy_id}/state", response_model=StrategyStateUpdateResponse
)
async def update_strategy_state(
    strategy_id: str, payload: StrategyStateUpdateRequest
):
    settings = get_settings()
    repo = StrategiesRepository(settings)
    updated = repo.update_state(strategy_id, payload.state)
    if not updated:
        raise APIError(
            "STRATEGY_NOT_FOUND", f"Strategy {strategy_id} not found", status_code=404
        )
    return StrategyStateUpdateResponse(strategy_id=strategy_id, state=payload.state)
