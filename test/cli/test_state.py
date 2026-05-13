"""cli/state.py 테스트 — 리밸런싱 상태 영속화."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

import cli.state as state_module
from cli.state import (
    get_bot_last_rebalance,
    get_last_rebalance,
    is_bot_stopped,
    make_state_key,
    mark_bot_running,
    mark_bot_stopped,
    set_bot_last_rebalance,
    set_last_rebalance,
)


@pytest.fixture(autouse=True)
def isolated_state(tmp_path):
    """각 테스트마다 독립된 임시 상태 파일 경로를 사용한다."""
    state_file = tmp_path / ".sf" / "state.json"
    with patch.object(state_module, "_STATE_FILE", state_file):
        yield state_file


# ── get_last_rebalance / set_last_rebalance ──────────────────────────

class TestLastRebalance:
    def test_returns_none_when_no_state(self):
        assert get_last_rebalance("some_key") is None

    def test_roundtrip(self):
        dt = date(2024, 5, 1)
        set_last_rebalance("key1", dt)
        assert get_last_rebalance("key1") == dt

    def test_overwrites_existing(self):
        set_last_rebalance("key1", date(2024, 1, 1))
        set_last_rebalance("key1", date(2024, 6, 15))
        assert get_last_rebalance("key1") == date(2024, 6, 15)

    def test_multiple_keys_independent(self):
        set_last_rebalance("key_a", date(2024, 1, 1))
        set_last_rebalance("key_b", date(2024, 6, 1))
        assert get_last_rebalance("key_a") == date(2024, 1, 1)
        assert get_last_rebalance("key_b") == date(2024, 6, 1)

    def test_state_persists_in_file(self, isolated_state):
        set_last_rebalance("persist_key", date(2024, 3, 15))
        raw = json.loads(isolated_state.read_text())
        assert "persist_key" in raw

    def test_year_boundary_date(self):
        dt = date(2025, 1, 1)
        set_last_rebalance("year_end", dt)
        assert get_last_rebalance("year_end") == dt


# ── make_state_key ───────────────────────────────────────────────────

class TestMakeStateKey:
    def test_produces_unique_keys_for_different_inputs(self):
        k1 = make_state_key("momentum", "snp500", "monthly")
        k2 = make_state_key("momentum", "sector_etf", "monthly")
        k3 = make_state_key("low-vol", "snp500", "monthly")
        assert len({k1, k2, k3}) == 3

    def test_same_inputs_same_key(self):
        k1 = make_state_key("momentum", "snp500", "monthly")
        k2 = make_state_key("momentum", "snp500", "monthly")
        assert k1 == k2

    def test_key_is_string(self):
        assert isinstance(make_state_key("a", "b", "c"), str)


# ── 봇 상태 ──────────────────────────────────────────────────────────

class TestBotLastRebalance:
    def test_returns_none_initially(self):
        assert get_bot_last_rebalance("my_bot") is None

    def test_roundtrip(self):
        dt = date(2024, 8, 5)
        set_bot_last_rebalance("my_bot", dt)
        assert get_bot_last_rebalance("my_bot") == dt

    def test_different_bots_independent(self):
        set_bot_last_rebalance("bot_a", date(2024, 1, 1))
        set_bot_last_rebalance("bot_b", date(2024, 7, 1))
        assert get_bot_last_rebalance("bot_a") == date(2024, 1, 1)
        assert get_bot_last_rebalance("bot_b") == date(2024, 7, 1)

    def test_update_overwrites(self):
        set_bot_last_rebalance("bot_a", date(2024, 1, 1))
        set_bot_last_rebalance("bot_a", date(2024, 9, 1))
        assert get_bot_last_rebalance("bot_a") == date(2024, 9, 1)


class TestBotStopped:
    def test_not_stopped_by_default(self):
        assert is_bot_stopped("bot_x") is False

    def test_mark_stopped(self):
        mark_bot_stopped("bot_x")
        assert is_bot_stopped("bot_x") is True

    def test_mark_running_clears_stopped(self):
        mark_bot_stopped("bot_x")
        mark_bot_running("bot_x")
        assert is_bot_stopped("bot_x") is False

    def test_multiple_bots_independent(self):
        mark_bot_stopped("bot_a")
        assert is_bot_stopped("bot_b") is False

    def test_stop_and_resume_twice(self):
        mark_bot_stopped("bot_x")
        mark_bot_running("bot_x")
        mark_bot_stopped("bot_x")
        assert is_bot_stopped("bot_x") is True

    def test_running_on_never_stopped_is_safe(self):
        # 한 번도 stop하지 않은 봇에 mark_running 호출해도 예외 없음
        mark_bot_running("never_stopped_bot")
        assert is_bot_stopped("never_stopped_bot") is False

    def test_bot_state_and_rebalance_coexist(self):
        set_bot_last_rebalance("combo_bot", date(2024, 5, 1))
        mark_bot_stopped("combo_bot")
        assert get_bot_last_rebalance("combo_bot") == date(2024, 5, 1)
        assert is_bot_stopped("combo_bot") is True

    def test_state_file_created_on_write(self, isolated_state):
        assert not isolated_state.exists()
        mark_bot_stopped("x")
        assert isolated_state.exists()

    def test_corrupted_state_file_returns_defaults(self, isolated_state):
        isolated_state.parent.mkdir(parents=True, exist_ok=True)
        isolated_state.write_text("not json", encoding="utf-8")
        # 파싱 실패해도 None/False 반환, 예외 없음
        assert get_last_rebalance("any") is None
        assert is_bot_stopped("any") is False
