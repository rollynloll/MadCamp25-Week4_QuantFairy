from __future__ import annotations

import json
from datetime import date
from pathlib import Path

_STATE_FILE = Path.home() / ".sf" / "state.json"


def _load() -> dict:
    if not _STATE_FILE.exists():
        return {}
    try:
        return json.loads(_STATE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict) -> None:
    _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _STATE_FILE.write_text(json.dumps(data, default=str, indent=2))


def get_last_rebalance(key: str) -> date | None:
    """저장된 마지막 리밸런싱 날짜를 반환한다. 없으면 None."""
    val = _load().get(key)
    return date.fromisoformat(val) if val else None


def set_last_rebalance(key: str, dt: date) -> None:
    """마지막 리밸런싱 날짜를 상태 파일에 저장한다."""
    data = _load()
    data[key] = str(dt)
    _save(data)


def make_state_key(strategy: str, universe_spec: str, rebalance: str) -> str:
    """상태 파일 키를 생성한다. 전략+유니버스+주기 조합이 고유 키가 된다."""
    return f"{strategy}|{universe_spec}|{rebalance}"


# ──────────────────────────────────────────────
# 봇 상태 (bots.yaml 기반 다중 봇 운용)
# ──────────────────────────────────────────────

def get_bot_last_rebalance(bot_name: str) -> date | None:
    """봇의 마지막 리밸런싱 날짜를 반환한다."""
    return get_last_rebalance(f"bot:{bot_name}")


def set_bot_last_rebalance(bot_name: str, dt: date) -> None:
    """봇의 마지막 리밸런싱 날짜를 저장한다."""
    set_last_rebalance(f"bot:{bot_name}", dt)


def is_bot_stopped(bot_name: str) -> bool:
    """봇이 중지 상태인지 확인한다."""
    return bool(_load().get(f"bot:{bot_name}:stopped", False))


def mark_bot_stopped(bot_name: str) -> None:
    """봇을 중지 상태로 표시한다."""
    data = _load()
    data[f"bot:{bot_name}:stopped"] = True
    _save(data)


def mark_bot_running(bot_name: str) -> None:
    """봇의 중지 상태를 해제한다."""
    data = _load()
    data.pop(f"bot:{bot_name}:stopped", None)
    _save(data)
