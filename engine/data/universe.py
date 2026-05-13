from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

_SP500_FILE = Path(__file__).parent / "sp500.json"

# GICS 섹터 ETF 11개 — bots.yaml universe: sector_etf
SECTOR_ETF_TICKERS: List[str] = [
    "XLK", "XLF", "XLE", "XLV", "XLI",
    "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC",
]


def _load() -> dict:
    with open(_SP500_FILE, encoding="utf-8") as f:
        return json.load(f)


def resolve_universe(
    universe: Optional[List[str]] = None,
    sector: Optional[str] = None,
) -> List[str]:
    # 우선순위: --universe 직접 지정 > --sector 필터 > 전체 S&P 500
    if universe:
        return [t.upper() for t in universe]

    data = _load()
    constituents = data["constituents"]

    if sector:
        key = sector.lower()
        if key not in data["sectors"]:
            valid = ", ".join(sorted(data["sectors"].keys()))
            raise ValueError(f"알 수 없는 섹터: '{sector}'. 사용 가능: {valid}")
        return [c["ticker"] for c in constituents if c["sector"] == key]

    return [c["ticker"] for c in constituents]


def resolve_universe_preset(name: str) -> List[str]:
    """bots.yaml의 universe 이름 → 티커 목록.

    지원 프리셋:
      snp500     — S&P 500 구성 종목 전체
      sector_etf — GICS 섹터 ETF 11개 (XLK, XLF, ...)
    """
    key = name.lower()
    if key == "sector_etf":
        return list(SECTOR_ETF_TICKERS)
    if key == "snp500":
        return resolve_universe()
    raise ValueError(
        f"알 수 없는 유니버스 프리셋: {name!r}. 사용 가능: snp500, sector_etf"
    )


def list_sectors() -> List[str]:
    # 사용 가능한 섹터 키 목록 반환 (CLI 자동완성, 도움말용)
    return sorted(_load()["sectors"].keys())


def sector_display_name(sector: str) -> str:
    # 섹터 키(예: "technology") → GICS 공식 명칭(예: "Information Technology")
    data = _load()
    return data["sectors"].get(sector.lower(), sector)
