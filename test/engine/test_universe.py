"""engine/data/universe.py 테스트 — resolve_universe, resolve_universe_preset."""
from __future__ import annotations

import pytest

from engine.data.universe import (
    SECTOR_ETF_TICKERS,
    list_sectors,
    resolve_universe,
    resolve_universe_preset,
    sector_display_name,
)

_EXPECTED_SECTOR_ETFS = {
    "XLK", "XLF", "XLE", "XLV", "XLI",
    "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC",
}


# ── resolve_universe_preset ──────────────────────────────────────────

class TestResolveUniversePreset:
    def test_snp500_returns_nonempty_list(self):
        tickers = resolve_universe_preset("snp500")
        assert isinstance(tickers, list)
        assert len(tickers) > 0

    def test_snp500_all_uppercase(self):
        tickers = resolve_universe_preset("snp500")
        for t in tickers:
            assert t == t.upper(), f"티커 {t!r}가 대문자가 아님"

    def test_snp500_contains_known_stocks(self):
        tickers = set(resolve_universe_preset("snp500"))
        assert "AAPL" in tickers
        assert "MSFT" in tickers

    def test_sector_etf_exactly_11(self):
        tickers = resolve_universe_preset("sector_etf")
        assert len(tickers) == 11

    def test_sector_etf_contains_all_expected(self):
        tickers = set(resolve_universe_preset("sector_etf"))
        assert tickers == _EXPECTED_SECTOR_ETFS

    def test_sector_etf_all_uppercase(self):
        for t in resolve_universe_preset("sector_etf"):
            assert t == t.upper()

    def test_case_insensitive_snp500(self):
        assert resolve_universe_preset("SNP500") == resolve_universe_preset("snp500")

    def test_case_insensitive_sector_etf(self):
        assert resolve_universe_preset("SECTOR_ETF") == resolve_universe_preset("sector_etf")

    def test_unknown_preset_raises_value_error(self):
        with pytest.raises(ValueError, match="알 수 없는"):
            resolve_universe_preset("nasdaq100")

    def test_empty_string_raises_value_error(self):
        with pytest.raises(ValueError):
            resolve_universe_preset("")

    def test_returns_copy_not_reference(self):
        a = resolve_universe_preset("sector_etf")
        b = resolve_universe_preset("sector_etf")
        a.append("EXTRA")
        assert "EXTRA" not in resolve_universe_preset("sector_etf")


# ── resolve_universe (기존 함수) ─────────────────────────────────────

class TestResolveUniverse:
    def test_direct_tickers_returned_uppercase(self):
        result = resolve_universe(universe=["aapl", "msft", "goog"])
        assert result == ["AAPL", "MSFT", "GOOG"]

    def test_direct_tickers_take_priority_over_sector(self):
        result = resolve_universe(universe=["AAPL"], sector="technology")
        assert result == ["AAPL"]

    def test_no_args_returns_full_snp500(self):
        result = resolve_universe()
        assert len(result) > 100  # S&P 500은 충분히 많아야 함

    def test_valid_sector_returns_subset(self):
        full = resolve_universe()
        tech = resolve_universe(sector="technology")
        assert len(tech) > 0
        assert len(tech) < len(full)

    def test_invalid_sector_raises_value_error(self):
        with pytest.raises(ValueError, match="알 수 없는"):
            resolve_universe(sector="invalid_sector_xyz")

    def test_sector_result_all_uppercase(self):
        for t in resolve_universe(sector="technology"):
            assert t == t.upper()

    def test_empty_universe_list_falls_through_to_sp500(self):
        # 빈 리스트 → falsy → 섹터/전체로 폴백
        result = resolve_universe(universe=[])
        assert len(result) > 100


# ── list_sectors ─────────────────────────────────────────────────────

class TestListSectors:
    def test_returns_list(self):
        assert isinstance(list_sectors(), list)

    def test_contains_technology(self):
        assert "technology" in list_sectors()

    def test_all_lowercase(self):
        for s in list_sectors():
            assert s == s.lower()


# ── sector_display_name ──────────────────────────────────────────────

class TestSectorDisplayName:
    def test_technology_display_name(self):
        name = sector_display_name("technology")
        assert "Technology" in name or "Information" in name

    def test_unknown_returns_input(self):
        assert sector_display_name("unknown_xyz") == "unknown_xyz"


# ── SECTOR_ETF_TICKERS 상수 ──────────────────────────────────────────

class TestSectorEtfConstant:
    def test_length(self):
        assert len(SECTOR_ETF_TICKERS) == 11

    def test_no_duplicates(self):
        assert len(set(SECTOR_ETF_TICKERS)) == len(SECTOR_ETF_TICKERS)

    def test_expected_tickers_present(self):
        assert set(SECTOR_ETF_TICKERS) == _EXPECTED_SECTOR_ETFS
