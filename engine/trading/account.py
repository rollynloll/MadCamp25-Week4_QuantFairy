from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Account:
    equity: float          # 총 자산 (현금 + 포지션 시장가치)
    cash: float            # 사용 가능 현금
    buying_power: float    # 실제 매수 가능 금액 (레버리지 포함 시 equity × 2 등)
    portfolio_value: float # 포지션 시장가치 합계 (equity - cash)
    currency: str = field(default="USD")
