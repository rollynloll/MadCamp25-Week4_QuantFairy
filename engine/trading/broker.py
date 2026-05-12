from __future__ import annotations

from typing import List, Protocol

from engine.trading.account import Account
from engine.trading.order import Order
from engine.trading.position import Position


class BrokerProvider(Protocol):
    """브로커 어댑터 인터페이스.

    새 브로커를 추가하려면 이 Protocol을 만족하는 클래스를 infra/broker/ 아래에 작성한다.
    별도 상속 없이 메서드 시그니처만 맞추면 된다.
    """

    def get_account(self) -> Account:
        """계좌 요약 정보를 반환한다 (자산, 현금, 매수 가능 금액 등)."""
        ...

    def get_positions(self) -> List[Position]:
        """현재 보유 포지션 목록을 반환한다. 미실현 손익 등 상세 필드도 포함한다."""
        ...

    def place_orders(self, orders: List[Order]) -> List[str]:
        """주문 목록을 실행하고 브로커가 반환한 주문 ID 목록을 반환한다."""
        ...

    def is_market_open(self) -> bool:
        """현재 시장이 열려 있는지 여부를 반환한다."""
        ...
