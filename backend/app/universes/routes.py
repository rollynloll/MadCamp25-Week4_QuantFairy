from __future__ import annotations

from fastapi import APIRouter

from app.core.errors import APIError
from app.universes.presets import UNIVERSE_PRESETS


router = APIRouter()


@router.get("/universes/presets")
async def list_universe_presets():
    items = []
    for preset in UNIVERSE_PRESETS.values():
        items.append(
            {
                "preset_id": preset["preset_id"],
                "name": preset["name"],
                "description": preset["description"],
                "size": len(preset["tickers"]),
            }
        )
    return {"items": items}


@router.get("/universes/presets/{preset_id}")
async def get_universe_preset(preset_id: str):
    preset = UNIVERSE_PRESETS.get(preset_id)
    if not preset:
        raise APIError("NOT_FOUND", "Preset not found", status_code=404)
    return {"preset_id": preset_id, "tickers": preset["tickers"]}
