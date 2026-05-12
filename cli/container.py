from __future__ import annotations

from engine.data.protocol import DataProvider
from engine.trading.broker import BrokerProvider
from infra.data.yfinance import YFinanceProvider


def get_data_provider() -> DataProvider:
    # CLI는 항상 yfinance를 데이터 소스로 사용한다.
    # 웹 서버는 별도의 DBProvider를 주입한다.
    return YFinanceProvider()


def get_broker() -> BrokerProvider:
    # 환경변수 ALPACA_API_KEY / ALPACA_SECRET_KEY 필요.
    # 다른 브로커를 쓰려면 이 함수만 교체하면 된다.
    from infra.broker.alpaca import AlpacaBroker
    return AlpacaBroker()
