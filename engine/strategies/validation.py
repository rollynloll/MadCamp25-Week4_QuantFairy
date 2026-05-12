from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Dict, List


# 전략이 유효하지 않은 비중을 반환했을 때 발생시키는 예외.
# runner.py에서 이 예외를 잡아 StrategyError로 변환한다.
@dataclass
class StrategyValidationError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


def validate_target_weights(
    weights: Dict[str, float],
    universe: List[str],
    long_only: bool,
    cash_buffer: float,
    max_weight_per_asset: float,
) -> Dict[str, float]:
    # 전략이 반환한 목표 비중을 검증하고 정규화하여 안전한 비중 딕셔너리를 반환한다.
    # 입력 weights를 직접 수정하지 않고 새로운 딕셔너리를 반환한다.
    #
    # 처리 순서:
    #   1. None, NaN, inf 값 제거
    #   2. universe 밖의 심볼 거부 (StrategyValidationError 발생)
    #   3. long_only=True이면 음수 비중 거부
    #   4. max_weight_per_asset 상한 적용 (초과분은 상한값으로 클리핑)
    #   5. 비중 합이 (1 - cash_buffer)를 초과하면 비례 축소 (정규화)

    if weights is None:
        return {}

    # universe를 대문자로 정규화하여 비교할 허용 심볼 집합을 만든다
    allowed = {s.upper() for s in universe}
    cleaned: Dict[str, float] = {}

    for symbol, raw in weights.items():
        if symbol is None:
            continue
        symbol_norm = str(symbol).upper()

        # universe에 없는 심볼은 즉시 거부 — 전략 버그를 조기에 잡는다
        if symbol_norm not in allowed:
            raise StrategyValidationError(f"Symbol not in universe: {symbol_norm}")

        if raw is None:
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue

        # NaN, inf 등 계산 불가능한 값은 조용히 제거한다
        if not math.isfinite(value):
            continue

        # 공매도(숏) 비중은 long_only 모드에서 허용하지 않는다
        if long_only and value < 0:
            raise StrategyValidationError(f"Negative weight not allowed: {symbol_norm}")

        # 단일 자산 최대 비중 상한 적용
        if max_weight_per_asset is not None and max_weight_per_asset > 0:
            value = min(value, max_weight_per_asset)

        # 0 비중은 포지션 없음이므로 결과에서 제외한다
        if value == 0:
            continue
        cleaned[symbol_norm] = value

    total = sum(cleaned.values())
    if total <= 0:
        return {}   # 투자 가능한 비중이 없으면 전량 현금

    # cash_buffer만큼 현금을 남기고 나머지에만 투자하도록 비중 합 상한을 설정한다.
    # 예: cash_buffer=0.1이면 최대 90%만 투자하고 10%는 현금 유지
    max_total = max(0.0, 1.0 - max(cash_buffer, 0.0))
    if total > max_total:
        # 모든 비중을 비례 축소하여 합이 max_total이 되도록 한다
        scale = max_total / total
        cleaned = {k: v * scale for k, v in cleaned.items()}

    return cleaned
