# StockFairy — FEATURES.md

> **상태** `[ ]` 미구현 · `[~]` 부분 구현(리팩토링 필요) · `[x]` 완료 · `[-]` Out of scope

---

## 기능별

### 백테스트
- `[x]` 백테스트 실행 (runner)
- `[x]` 성과 지표 계산 (CAGR, Sharpe, MDD, alpha, beta)
- `[~]` 백테스트 결과 저장 및 조회 (CLI → JSON 저장 완료 / 웹 DB 저장 미완)
- `[x]` CLI `sf backtest` 커맨드

### 자동 매매
- `[x]` 봇 시작 / 중지 (`sf trade run` / `sf trade schedule`)
- `[x]` 포지션 · 계좌 조회 (`sf account show` / `sf account positions`)
- `[x]` 리밸런싱 주문 계산 (`executor.py` — compute_orders 순수 함수)
- `[x]` Alpaca paper 주문 실행 (`infra/broker/alpaca.py`)
- `[x]` 봇 스케줄러 (daily / weekly / monthly — APScheduler + GitHub Actions)
- `[x]` CLI `sf trade run` · `sf account positions` 커맨드

### 전략 관리
- `[x]` 전략 스펙 정의 (StrategySpec, UniverseSpec, RebalanceSpec, RiskSpec)
- `[x]` 내장 전략 6개 (Momentum, TrendSMA200, RSI, LowVol, VolAdj, RiskOnOff)
- `[x]` 사용자 Python 전략 (AST 샌드박스 실행)
- `[~]` 전략 CRUD (백엔드 API 있음 / CLI 미구현)
- `[x]` 전략 파라미터 검증
- `[x]` 전략 레지스트리 (이름 → 구현체 매핑)

---

## 레이어별

### Caller

#### `backend/app/api/` — 라우터
- `[~]` 백테스트 라우터 (`backtests/routes.py`) — P3: 비즈니스 로직 분리, 30줄 이하로
- `[~]` 자동 매매 라우터 (`trading/routes.py`, `bot/routes.py`) — P3: 동일
- `[~]` 전략 관리 라우터 (`strategies/routes.py`) — P3: 동일

#### `backend/app/services/` — 에러 변환 레이어
- `[ ]` BacktestService — P3: DataNotFoundError → 404, DataSourceError → 503
- `[ ]` TradingService — P3: OrderRejectedError → 422, BrokerConnectionError → 503
- `[ ]` StrategyService — P3: StrategyError → 422

#### `cli/` — CLI 커맨드
- `[x]` `cli/container.py` — DI 조립 (YFinanceProvider + AlpacaBroker)
- `[x]` `cli/commands/backtest.py` — `sf backtest run`
- `[x]` `cli/commands/trade.py` — `sf trade run` / `sf trade schedule`
- `[x]` `cli/commands/account.py` — `sf account show` / `sf account positions`
- `[x]` `cli/state.py` — 리밸런싱 상태 영속화 (`~/.sf/state.json`)

---

### Engine

#### `engine/backtest/`
- `[x]` `runner.py` — DataProvider 주입, DataNotFoundError·StrategyError 사용, NaN 방어
- `[x]` `metrics.py` — 순수 함수, 인프라 의존 없음

#### `engine/strategies/`
- `[x]` `base.py` — Strategy Protocol, StrategyContext, StrategySignal
- `[x]` `spec.py` — StrategySpec Pydantic 모델
- `[x]` `registry.py` — 단축 이름 (`momentum`, `low-vol` 등) → 구현체
- `[x]` `indicators.py` — RSI, 수익률, 변동성 계산
- `[x]` `validation.py` — target_weights 6단계 검증
- `[x]` `sandbox.py` — AST 화이트리스트 + 격리 프로세스 실행
- `[x]` 내장 전략 6개 — `engine/strategies/catalog/` 아래 flat `.py`

#### `engine/trading/`
- `[x]` `order.py` — Order 데이터클래스 (symbol, side, notional)
- `[x]` `position.py` — Position 데이터클래스 (qty, market_value, unrealized_pnl 등)
- `[x]` `account.py` — Account 데이터클래스 (equity, cash, buying_power)
- `[x]` `broker.py` — BrokerProvider Protocol
- `[x]` `executor.py` — compute_orders() 순수 함수
- `[x]` `scheduler.py` — should_rebalance() + run_live() 한 사이클

#### `engine/errors.py`
- `[x]` DataNotFoundError, DataSourceError, StrategyError
- `[ ]` OrderRejectedError, InsufficientFundsError, BrokerConnectionError — P4

---

### Protocol

#### `engine/data/`
- `[x]` `protocol.py` — DataProvider Protocol (get_prices 인터페이스)

#### `infra/data/`
- `[x]` `yfinance.py` — YFinanceProvider
- `[x]` `db.py` — DBProvider (market_prices 테이블)

#### `engine/trading/`
- `[x]` `broker.py` — BrokerProvider Protocol (get_account, get_positions, place_orders, is_market_open)

#### `infra/broker/`
- `[x]` `alpaca.py` — AlpacaBroker (paper / live)

---

### 자동화

#### `.github/workflows/`
- `[x]` `trade.yml` — GitHub Actions 자동매매
  - 평일 매일 14:35 UTC (NYSE 개장 5분 후)
  - Alpaca Clock API로 공휴일 자동 건너뜀
  - 상태 파일 레포 커밋 영구 보존 (`.trade/state.json`)
  - 수동 실행 + dry_run 선택 지원

---

## 구현 우선순위 (Phase)

| Phase | 대상 | 완료 기준 | 상태 |
|---|---|---|---|
| **P1** | Engine 분리 | `engine/` 내 FastAPI·asyncpg import 없음. `python -c "from engine.backtest.runner import run"` 성공 | `[x]` |
| **P2** | CLI | `sf backtest run --strategy momentum --start 2020-01-01 --end 2024-12-31` 터미널 출력 성공 | `[x]` |
| **P3** | 웹 레이어 정리 | 라우터 30줄 이하. 기존 `/api/v1/*` 스펙 100% 유지 | `[ ]` |
| **P4** | 라이브 트레이딩 | `sf trade run --strategy momentum` Alpaca paper 주문 실행 성공 | `[x]` |
