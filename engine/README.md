# engine/

퀀트 전략 백테스트 엔진. FastAPI, Supabase, yfinance 등 외부 인프라에 의존하지 않는 **순수 Python 패키지**다.  
인프라(데이터 소스, DB)는 Protocol로 추상화되어 있으며, 런타임에 CLI 또는 웹 서버가 구현체를 주입한다.

---

## 디렉토리 구조

```
engine/
├── errors.py               # 엔진 전용 예외 클래스
├── data/
│   ├── protocol.py         # DataProvider Protocol (인터페이스 정의)
│   ├── universe.py         # S&P 500 유니버스 로더 및 섹터 필터
│   └── sp500.json          # S&P 500 구성 종목 정적 스냅샷 (~430개)
├── strategies/
│   ├── base.py             # Strategy Protocol, StrategyContext, StrategySignal
│   ├── indicators.py       # 기술적 지표 계산 (RSI, 수익률, 변동성)
│   ├── spec.py             # 전략 설정 Pydantic 모델 (StrategySpec, PythonBody)
│   ├── validation.py       # target_weights 6단계 검증
│   ├── sandbox.py          # 사용자 Python 전략 AST 검증 + 격리 실행
│   ├── registry.py         # entrypoint 문자열 → 전략 인스턴스 팩토리
│   └── catalog/            # 내장 전략 구현 모음
│       ├── momentum_topn_v1.py
│       ├── trend_sma200_v1.py
│       ├── rsi_mean_reversion_v1.py
│       ├── low_volatility.py
│       ├── vol_adj_momentum.py
│       └── risk_on_off.py
├── backtest/
│   ├── runner.py           # 백테스트 실행 진입점 (run 함수)
│   └── metrics.py          # 성과 지표 계산 (CAGR, Sharpe, MDD, Alpha 등)
└── trading/
    ├── order.py            # Order 데이터클래스 (symbol, side, notional)
    ├── position.py         # Position 데이터클래스 (symbol, qty, market_value)
    ├── broker.py           # BrokerProvider Protocol (인터페이스 정의)
    ├── executor.py         # compute_orders() — 순수 함수
    └── scheduler.py        # should_rebalance() + run_live() 한 사이클 실행
```

---

## 핵심 설계 원칙

### 1. 인프라 의존성 없음

`engine/` 내부 어디에도 `fastapi`, `asyncpg`, `supabase`, `yfinance`를 import하지 않는다.  
데이터 조회는 `DataProvider` Protocol을 통해서만 이루어진다.

```python
# engine/data/protocol.py
class DataProvider(Protocol):
    def get_prices(self, tickers: list[str], start: str, end: str) -> pd.DataFrame:
        # 반환: index=DatetimeIndex, columns=티커, values=adj_close
        ...
```

CLI는 `YFinanceProvider`를, 웹 서버는 `DBProvider`를 주입한다.

### 2. 데이터 포맷 규칙

| 위치 | 포맷 | 설명 |
|------|------|------|
| `DataProvider.get_prices()` 반환 | Wide DataFrame | index=날짜, columns=티커 |
| `Strategy.compute_target_weights()` 입력 | MultiIndex DataFrame | (date, symbol) × adj_close |
| `runner.py` 내부 변환 | `prices_wide.stack()` | Wide → MultiIndex |

### 3. 전략 인터페이스

전략은 두 가지 방식 중 하나로 신호를 생성한다.

```python
# 방식 1: 리밸런싱 날짜마다 호출 (권장)
def compute_target_weights(prices, ctx, universe, dt) -> Dict[str, float]:
    # 해당 날짜의 목표 비중 딕셔너리 반환
    # 빈 딕셔너리 = 전량 현금

# 방식 2: 전체 기간 한 번에 신호 생성
def generate_signals(prices, ctx, universe) -> Iterable[StrategySignal]:
    # (date, target_weights) 신호 스트림 yield
```

`runner.py`는 `compute_target_weights`를 우선 시도하고, 없으면 `generate_signals`로 fallback한다.

---

## 모듈별 상세 설명

### `errors.py`

| 예외 | 상속 | 발생 상황 |
|------|------|-----------|
| `DataNotFoundError` | `ValueError` | 요청한 기간/티커의 데이터가 없을 때 |
| `DataSourceError` | `RuntimeError` | DB 연결 실패 등 인프라 오류 |
| `StrategyError` | `ValueError` | 전략이 잘못된 비중을 반환했을 때 |

---

### `data/universe.py`

S&P 500 구성 종목을 `sp500.json`에서 로드하고, CLI의 `--sector` / `--universe` 옵션에 따라 유니버스를 결정한다.

```python
resolve_universe(universe=None, sector="technology")
# → ["AAPL", "MSFT", "NVDA", ...]  (technology 섹터 티커 목록)

resolve_universe(universe=["AAPL", "MSFT"])
# → ["AAPL", "MSFT"]  (직접 지정 우선)

resolve_universe()
# → [전체 S&P 500 티커]
```

섹터 키 목록: `communication`, `discretionary`, `energy`, `financials`, `healthcare`, `industrials`, `materials`, `realestate`, `staples`, `technology`, `utilities`

---

### `strategies/base.py`

**StrategyContext**: 전략 실행 시 파라미터와 상태를 전달하는 컨테이너.

```python
ctx = StrategyContext(
    params={"top_n": 10, "lookback_days": 252},
    default_params={"top_n": 5},   # 기본값 (params가 없을 때 사용)
)
ctx.resolved_params()  # params와 default_params를 병합한 딕셔너리
ctx.state              # 전략이 자유롭게 쓸 수 있는 딕셔너리 (캐시 등)
```

**StrategySignal**: 하나의 리밸런싱 신호.

```python
StrategySignal(
    date="2024-01-15",
    target_weights={"AAPL": 0.3, "MSFT": 0.3, "NVDA": 0.4},
)
```

---

### `strategies/catalog/`

내장 전략 목록. 새 전략 추가 시 여기에 파일을 추가하고 `registry.py`에 등록한다.

| 파일 | 클래스 | 전략 설명 |
|------|--------|-----------|
| `momentum_topn_v1.py` | `MomentumTopNStrategy` | 12개월 수익률 상위 N종목 균등 투자 |
| `trend_sma200_v1.py` | `TrendSMA200Strategy` | SMA200 기준 전량 투자/현금 전환 |
| `rsi_mean_reversion_v1.py` | `RSIMeanReversionStrategy` | RSI < 30 매수, RSI > 50 매도 |
| `low_volatility.py` | `LowVolatilityStrategy` | 저변동성 상위 N종목 역변동성 비중 |
| `vol_adj_momentum.py` | `VolatilityAdjustedMomentumStrategy` | 수익률/변동성 점수 상위 N종목 |
| `risk_on_off.py` | `RiskOnOffStrategy` | SMA200 레짐 판단 + 모멘텀 종목 선택 |

---

### `strategies/registry.py`

entrypoint 문자열로 전략 인스턴스를 생성한다. 매번 새 인스턴스를 반환하여 요청 간 상태 공유를 방지한다.

```python
from engine.strategies.registry import get_strategy, list_entrypoints

strategy = get_strategy("momentum")
all_eps = list_entrypoints()  # ["momentum", "trend", "rsi-reversion", ...]
```

새 전략 등록 방법:
1. `catalog/my_strategy.py` 작성
2. `registry.py`에 import 및 `_REGISTRY` 항목 추가

---

### `strategies/sandbox.py`

사용자가 직접 작성한 Python 전략을 안전하게 실행하는 모듈.

**실행 흐름:**
1. AST 화이트리스트 검사 (허용되지 않은 문법 차단)
2. `import`, `while`, `__class__` 등 금지 식별자 차단
3. `multiprocessing.spawn`으로 격리된 자식 프로세스에서 실행
4. `timeout_s` 초과 시 프로세스 강제 종료
5. 결과를 Pipe로 부모 프로세스에 전송

---

### `backtest/runner.py`

백테스트의 핵심 진입점. 6단계로 실행된다.

```
1. 파라미터 정규화 (날짜 파싱, bps 변환 등)
2. DataProvider로 가격 데이터 로드
3. Wide DataFrame → MultiIndex 변환 (전략 입력 형식)
4. 리밸런싱 날짜 생성 (monthly / weekly / daily / 신호 기반)
5. 전략 실행 → target_weights 수집 → 검증
6. 포트폴리오 시뮬레이션 → 성과 지표 계산
```

**함수 시그니처:**
```python
result = run(
    strategy=strategy_instance,
    data_provider=YFinanceProvider(),   # 주입
    ctx=StrategyContext(params={...}),
    universe=["AAPL", "MSFT", "NVDA"],
    start_date="2020-01-01",
    end_date="2024-12-31",
    benchmark_symbol="SPY",             # 선택
    initial_cash=10_000.0,
    fee_bps=5.0,
    slippage_bps=2.0,
    rebalance_freq="monthly",           # monthly / weekly / daily
)

result.metrics        # Dict[str, float] — 성과 지표
result.equity_curve   # List[{date, equity}]
result.drawdown       # List[{date, dd_pct}]
result.holdings       # List[{date, weights}]
```

---

---

### `trading/executor.py`

핵심 순수 함수 `compute_orders()`. 인프라 의존 없이 단독 테스트 가능하다.

```python
from engine.trading.executor import compute_orders
from engine.trading.position import Position

positions = [Position("AAPL", qty=1.0, market_value=4000.0)]
orders = compute_orders(
    target_weights={"AAPL": 0.5, "NVDA": 0.3},
    current_positions=positions,
    equity=10_000.0,
    min_order_notional=1.0,   # 1달러 미만 주문은 생략
)
# → [Order("AAPL", "buy", 1000.0), Order("NVDA", "buy", 3000.0)]
```

처리 규칙:
- 목표 비중이 없는 보유 종목 → 전량 매도
- 목표 금액 > 현재 금액 + min_order_notional → 차액 매수
- 목표 금액 < 현재 금액 − min_order_notional → 차액 매도

---

### `trading/scheduler.py`

`should_rebalance()` — 리밸런싱 날 여부 판단 (순수 함수).

```python
from engine.trading.scheduler import should_rebalance
from datetime import date

should_rebalance("monthly", date.today(), last_rebalance=date(2025, 4, 1))
# → True (월이 바뀌었으면)
```

`run_live()` — 자동매매 한 사이클 전체 실행.

```python
from engine.trading.scheduler import run_live

result = run_live(
    strategy=strategy_instance,
    data_provider=YFinanceProvider(),
    broker=AlpacaBroker(),
    ctx=StrategyContext(params={}),
    universe=["AAPL", "MSFT", "NVDA"],
    rebalance_freq="monthly",
    lookback_days=400,          # 전략 룩백 + 여유분
    last_rebalance_date=None,   # None이면 항상 리밸런싱
    min_order_notional=1.0,
    dry_run=True,               # False이면 broker.place_orders() 실행
)

result.did_rebalance      # bool
result.equity             # float
result.target_weights     # Dict[str, float]
result.orders             # List[Order]
result.current_positions  # List[Position]
```

`generate_signals`만 구현한 전략(momentum 등)은 마지막 신호를 사용하므로 모든 전략에 호환된다.

---

### `trading/broker.py`

브로커 어댑터 Protocol. `infra/broker/alpaca.py`가 이를 구현한다.

```python
class BrokerProvider(Protocol):
    def get_positions(self) -> List[Position]: ...
    def get_equity(self) -> float: ...
    def place_orders(self, orders: List[Order]) -> List[str]: ...  # 주문 ID 반환
    def is_market_open(self) -> bool: ...
```

---

### `backtest/metrics.py`

| 지표 | 계산 방법 |
|------|-----------|
| `total_return_pct` | (최종자산 / 초기자산 - 1) × 100 |
| `cagr_pct` | (최종/초기)^(252/기간일수) - 1, 연율화 |
| `volatility_pct` | 일간 수익률 표준편차 × √252 × 100 |
| `sharpe` | 연율화 수익률 / 연율화 변동성 (무위험수익률 = 0) |
| `max_drawdown_pct` | 고점 대비 최대 낙폭 (음수) |
| `alpha_pct` | (전략 수익률 - β × 벤치마크 수익률) × 252 × 100 |
| `beta` | Cov(전략, 벤치마크) / Var(벤치마크) |
| `tracking_error_pct` | 초과수익률 표준편차 × √252 × 100 |
| `information_ratio` | 연율화 초과수익률 / tracking_error |
| `turnover_pct` | 호출자가 외부에서 전달 (runner가 계산) |
