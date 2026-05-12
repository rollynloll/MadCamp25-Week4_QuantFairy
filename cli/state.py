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
