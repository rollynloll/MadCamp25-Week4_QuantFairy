from __future__ import annotations

from fastapi import APIRouter

from app.benchmarks.data import BENCHMARKS


router = APIRouter()


@router.get("/benchmarks")
async def list_benchmarks():
    return {"items": BENCHMARKS}
