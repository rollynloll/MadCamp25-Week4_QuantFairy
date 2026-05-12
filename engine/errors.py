from __future__ import annotations


# 데이터를 찾을 수 없을 때 발생하는 예외.
# 요청한 티커 또는 기간에 해당하는 가격 데이터가 없을 경우 사용한다.
# ValueError를 상속하므로 "잘못된 입력"에 해당하는 의미를 가진다.
class DataNotFoundError(ValueError):
    """No price data found for the requested tickers or period."""


# 데이터 소스(네트워크, DB 등)에서 데이터를 가져오는 데 실패했을 때 발생하는 예외.
# yfinance 타임아웃, DB 연결 오류 등 인프라 문제를 표현한다.
# RuntimeError를 상속하므로 "실행 중 예상치 못한 문제"에 해당하는 의미를 가진다.
class DataSourceError(RuntimeError):
    """Data provider failed to return data (network, timeout, etc.)."""


# 전략이 잘못된 출력을 생성했을 때 발생하는 예외.
# 유효하지 않은 비중(universe 밖의 심볼, 음수 비중 등), 샌드박스 오류 등에 사용한다.
# ValueError를 상속하므로 "전략 로직의 입력/출력 오류"에 해당하는 의미를 가진다.
class StrategyError(ValueError):
    """Strategy produced invalid output (bad weights, sandbox error, etc.)."""


class OrderRejectedError(RuntimeError):
    """Broker rejected an order (insufficient funds, invalid symbol, etc.)."""


class InsufficientFundsError(OrderRejectedError):
    """Account has insufficient buying power to place the order."""


class BrokerConnectionError(RuntimeError):
    """Failed to connect to or communicate with the broker API."""
