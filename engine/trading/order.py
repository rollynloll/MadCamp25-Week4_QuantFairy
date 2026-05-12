from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class Order:
    symbol: str
    side: Literal["buy", "sell"]
    notional: float   # 매수·매도할 달러 금액 (수량이 아닌 금액 기준)
