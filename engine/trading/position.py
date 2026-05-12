from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Position:
    symbol: str
    qty: float            # 보유 수량 (소수점 가능, fractional shares)
    market_value: float   # 현재 시장 가치 (달러)
    # 아래 필드는 브로커가 제공할 때만 채워진다 (executor는 사용하지 않음)
    avg_entry_price: float = field(default=0.0)   # 평균 매입 단가
    unrealized_pnl: float = field(default=0.0)    # 미실현 손익 (달러)
    unrealized_pnl_pct: float = field(default=0.0) # 미실현 손익률 (소수, 예: 0.05 = +5%)
