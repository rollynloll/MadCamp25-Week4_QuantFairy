# PatchNotes

---

## v1.0.0 — 2026-05-12

### 웹 레이어 정리 (P3)

- **백엔드 라우터 슬림화** (`backend/app/backtests/routes.py` 1101줄 → 57줄, `strategies/routes.py` 597줄 → 67줄)
  - 비즈니스 로직 전체를 서비스 레이어로 분리
  - `BacktestService`, `StrategyService` 신규 생성 (`backend/app/services/`)
  - `TradingService` 에 `set_mode()` / `set_kill_switch()` 추가
  - 라우터는 서비스 위임만 담당 (30줄 이하)

- **에러 클래스 추가** (`engine/errors.py`)
  - `OrderRejectedError`, `InsufficientFundsError`, `BrokerConnectionError` 신규
  - 서비스 레이어에서 엔진 에러 → HTTP 상태코드 매핑 (`422`, `503`)

- **데드 코드 제거**
  - `backend/app/strategies/descriptions.py` 삭제 (import 없음)
  - `backend/app/schemas/backtests_run.py` 삭제 (구버전 스키마)
  - `backend/app/schemas/strategies.py` 삭제 (구버전 스키마)
  - `backend/app/storage/settings_repo.py` 삭제 (`user_settings_repo.py`로 대체됨)

---

### 엔진 분리 및 CLI (P1·P2·P4)

- **`engine/` 모듈 신설** — FastAPI·asyncpg 의존 없음
  - `engine/backtest/runner.py` — DataProvider 주입, NaN 방어, trade_log 출력
  - `engine/backtest/metrics.py` — CAGR, Sharpe, MDD, alpha, beta 순수 함수
  - `engine/strategies/` — Strategy Protocol, StrategySpec, 내장 전략 6개, AST 샌드박스
  - `engine/trading/` — Order, Position, Account 데이터클래스, BrokerProvider Protocol, executor, scheduler
  - `engine/errors.py` — DataNotFoundError, DataSourceError, StrategyError

- **`infra/` 모듈 신설**
  - `infra/broker/alpaca.py` — AlpacaBroker (paper / live), `get_account()`, `get_positions()`, `place_orders()`, `is_market_open()`
  - `infra/data/yfinance.py` — YFinanceProvider
  - `infra/data/db.py` — DBProvider (market_prices 테이블)

- **CLI `sf` 커맨드** (`cli/`)
  - `sf backtest run` — 백테스트 실행 + rich progress bar + `--trades` / `--top-n` 매매 기록 출력
  - `sf trade run` — 자동매매 한 사이클 (`--dry-run` / `--execute`)
  - `sf trade schedule` — APScheduler 장기 실행 (monthly / weekly / daily)
  - `sf account show` — 계좌 요약
  - `sf account positions` — 보유 포지션 (미실현 손익 컬러)
  - `cli/state.py` — 리밸런싱 상태 영속화 (`~/.sf/state.json`)

- **내장 전략 6개** (`engine/strategies/catalog/`)
  - Momentum Top-N, TrendSMA200, RSI Mean Reversion, Low Volatility, Vol-Adj Momentum, Risk-On/Off

---

### 온보딩 UI

- **신규 페이지** (`frontend/src/pages/`)
  - `Login.tsx`, `Signup.tsx`, `VerifyEmail.tsx` — Supabase Auth 연동
  - `OnboardingWelcome.tsx`, `OnboardingSetup.tsx`, `OnboardingConnect.tsx` — 3단계 온보딩 플로우
  - `Account.tsx` — 계정 설정 페이지

- **한/영 전환** (`LanguageContext.tsx`)
  - 전체 앱 한국어 / 영어 실시간 전환
  - 온보딩·로그인·포트폴리오·백테스트 등 전 페이지 적용

- **다크/라이트 테마** (`ThemeContext.tsx`)

---

### Alpaca OAuth API

- **브로커 연결 엔드포인트** (`backend/app/brokers/routes.py`)
  - Alpaca OAuth 인가 플로우 (`/brokers/alpaca/oauth/authorize`, `/callback`)
  - 토큰 저장 / 조회 / 삭제 (`broker_tokens` 테이블)
  - `backend/app/storage/broker_tokens_repo.py` 신규

---

### 포트폴리오 · 트레이딩 UI

- **Portfolio 페이지** — Alpaca paper 계좌 연동, KPI 카드, 포지션 테이블, 전략별 수익 귀속, Activity 피드
- **Trading 페이지** — 실시간 WebSocket 가격 차트, 주문장, 오픈 오더, 포지션 테이블
- **Dashboard** — Active Strategies 실행 상태, 포트폴리오 요약, Recent Trades
- **Backtest UI** — 전략·날짜·유니버스 설정, Equity Curve, Monthly Returns, Portfolio Change 차트

---

### GitHub Actions 자동매매

- **`.github/workflows/trade.yml`**
  - 평일 매일 14:35 UTC (NYSE 개장 5분 후) cron 트리거
  - Alpaca Clock API로 공휴일 자동 건너뜀
  - 리밸런싱 상태 `.trade/state.json` 레포 커밋으로 영구 보존
  - `workflow_dispatch` 수동 실행 + `dry_run` 선택 지원

---

### 백테스트 버그 수정

- **NaN 전파 버그 수정** (`engine/backtest/runner.py`)
  - `bool(float('nan')) == True` 로 인한 NaN 필터 미작동 → `pd.notna()` 체크 추가
  - 2014년 이전 장기 백테스트 정상 작동

---

### 인프라 / 설정

- **배포**: 백엔드 Render (`https://madcamp25-week4-quantfairy.onrender.com`), 프론트엔드 Cloudflare Pages
- **DB**: Supabase PostgreSQL (asyncpg 연결 풀), Supabase Auth
- **환경 변수 분리**: Alpaca 키·DEFAULT_USER_ID → 루트 `.env`, Supabase/DB → `backend/.env`
- `.env.example` 협업 템플릿 추가
- `pyproject.toml` 의존성 정의 (apscheduler, yfinance 등)

---

## v1.1.0 — 2026-05-13

### 백엔드 로직 engine 위임 리팩토링

- **`backend/app/services/metrics.py` 삭제** — `engine/backtest/metrics.py` 완전 중복, 삭제 후 3개 호출처 import 수정
- **`backend/app/services/backtest_runner.py` 교체** — 478줄 인라인 시뮬레이션 루프 → `_DataProviderAdapter` + `engine.backtest.runner.run()` 위임 (40줄)
- **`engine/backtest/runner.py` 확장** — `benchmark_initial_cash`, `benchmark_fee_bps`, `benchmark_slippage_bps` 파라미터 추가
- **`engine/backtest/ensemble.py` 신규** — 앙상블 백테스트 로직 (`simulate_portfolio`, `run_single`, `run_ensemble`, 비중 계산 함수) engine으로 이동
  - `backend/app/services/backtest_engine.py` 287줄 → 60줄 (가격 로딩만 담당)
- **`engine/data/timeseries.py` 신규** — `dashboard/routes.py` 인라인 시계열 유틸 3개 이동
  - `sanitize_equity_curve`, `downsample_equity_to_hourly`, `ensure_latest_equity_point`
- **`engine/trading/metrics.py` 신규** — 포지션 목록 → 전략별 런타임 지표 집계 (`compute_strategy_runtime_metrics`)
- **`backend/app/strategies/` 전체 re-export화** — 9개 파일이 `engine/strategies/` 클래스를 re-export하는 얇은 래퍼로 교체
  - `base`, `spec`, `indicators`, `validation`, `sandbox`, `registry`, `low_volatility`, `vol_adj_momentum`, `risk_on_off`, subdirectory 3개
  - DB 저장된 entrypoint 키 포맷(`strategies.xxx:ClassName`) 그대로 유지
- **`portfolio/routes.py`, `dashboard/routes.py` 인라인 지표 교체** — 인라인 수익률·드로다운·KPI 계산 함수 삭제, `engine.backtest.metrics` 호출로 교체

---

### 환경 변수 통합

- **루트 `.env` 단일 관리** — `backend/.env`(Supabase), `frontend/.env`(Vite) 병합 → 루트 `.env` 하나로 통합
- **`frontend/vite.config.ts`** — `envDir: "../"` 추가, Vite가 프로젝트 루트 `.env` 참조
- **`backend/app/core/config.py`** — `load_dotenv(PROJECT_ROOT / ".env")` 명시적 경로로 수정
- **`.env.local`** — 로컬 dev 오버라이드 (`VITE_API_BASE_URL=http://localhost:8000`)

---

### 로컬 개발 환경

- **uvicorn 비치명 시작** — `init_db()` try/except 처리로 Supabase 연결 실패 시 경고만 출력하고 서버 기동
- **`_resolve_user_id` UUID 버그 수정** — `portfolio/routes.py`의 fallback이 `"demo_user"`(non-UUID)를 반환하던 문제 → `resolve_user_id_from_db()` 호출로 교체

---

### 남은 작업

- S&P 500 생존 편향 미적용 (ADR-002) — 유니버스 고정 상태
- CLI 백테스트 결과 웹 DB 저장 미구현 — CLI 실행 결과는 로컬 JSON만 저장, Supabase 저장 미지원
- 전략 CRUD CLI 미구현 — `sf strategy` 커맨드 없음, 웹 API만 존재

---

## v2.1.0 — 2026-05-13

### 다중 봇 자동매매 CLI

- **`config/bots.yaml` 신규** — 봇 목록 정의 파일 (전략·유니버스·자본 비율·리밸런싱 주기)
- **`cli/bots.py` 신규** — `BotConfig` / `RiskConfig` / `BotsConfig` 데이터클래스, `load_bots_config()`, `validate_bots_config()`
  - 검증 항목: `capital_pct` 합계 ≤ 1.0, 유효한 전략·유니버스·리밸런싱 주기, 봇 이름 중복
- **`sf run`** (`cli/commands/run.py`) — bots.yaml 기반 전체/개별 봇 순차 실행
  - `--all` / `--bot <name>` / `--dry-run` / `--config <path>`
  - `bot_equity = total_equity × capital_pct` 슬라이스 기반 주문 산정
  - 중지된 봇·리밸런싱 주기 미도달 봇 자동 건너뜀
- **`sf status`** (`cli/commands/status.py`) — 계좌 요약 + 봇별 전략·유니버스·자본·마지막 실행일·다음 실행일·상태 테이블
- **`sf stop`** (`cli/commands/stop.py`) — 봇 중지 / 재개 / 청산
  - `--liquidate`: 미체결 주문 전량 취소(`cancel_all_orders`) + 전체 포지션 시장가 매도

---

### 엔진 확장

- **`engine/trading/market_hours.py` 신규** — NYSE 장중 여부 체크
  - `is_within_market_hours(dt?)` — 09:30–16:00 ET, 평일만 `True`
  - `assert_market_hours(dt?)` — 장외 시 `MarketClosedError` raise
- **`engine/errors.py`** — `MarketClosedError(RuntimeError)` 추가
- **`engine/data/universe.py`** — 유니버스 프리셋 추가
  - `SECTOR_ETF_TICKERS` — 11개 섹터 ETF (XLK·XLF·XLE·XLV·XLI·XLY·XLP·XLU·XLB·XLRE·XLC)
  - `resolve_universe_preset(name)` — `"snp500"` / `"sector_etf"` 해석, 미지원 시 `ValueError`
- **`engine/trading/executor.py`** — sell-first 순서 보장
  - `compute_orders()` 반환값 = `sells + buys` (매도 대금으로 매수 가능하도록)
- **`engine/trading/scheduler.py`** — `run_live()` `capital_pct` 파라미터 추가
  - 실효 자산 = `total_equity × capital_pct`로 주문 수량 산정
- **`engine/strategies/registry.py`** — 전략 이름 full-name alias 추가
  - 단축형(`momentum`)과 전체 이름(`momentum_topn_v1`) 모두 같은 클래스 반환
  - bots.yaml에서 전체 이름 사용 권장

---

### infra 확장

- **`infra/broker/alpaca.py`**
  - `cancel_all_orders()` 구현 — `BrokerProvider` Protocol 신규 메서드
  - `ALPACA_MODE=paper|live` 환경 변수로 브로커 모드 전환 (`ALPACA_PAPER` 대체)

---

### CLI 확장

- **`sf backtest compare`** (`cli/commands/backtest.py`) — 여러 전략 동시 백테스트 비교 테이블
  - `--strategies a,b,c` 지정, 각 지표에서 최고값 초록 굵은 글씨 표시
- **`cli/state.py`** — 봇 상태 함수 추가
  - `get/set_bot_last_rebalance(bot_name, dt)`, `is_bot_stopped()`, `mark_bot_stopped()`, `mark_bot_running()`
  - 상태 키 포맷: `bot:<name>`, `bot:<name>:stopped`
- **`cli/main.py`** — `sf run` / `sf status` / `sf stop` 직접 커맨드로 등록, `.env.local` 로드 추가

---

### 테스트

- **`test/` 신규 — 199개 테스트 (pytest, 외부 네트워크·DB 의존 없음)**

| 파일 | 테스트 수 | 커버리지 |
|------|-----------|---------|
| `test_metrics.py` | 19 | CAGR, Sharpe, MDD, alpha/beta, NaN 없음 |
| `test_executor.py` | 22 | sell-first 순서, min notional, 엣지케이스 |
| `test_scheduler.py` | 16 | daily/weekly/monthly 경계값, capital_pct 스케일링 |
| `test_market_hours.py` | 16 | 개장 전·후, 주말, 정각 경계, MarketClosedError |
| `test_universe.py` | 20 | sector_etf 11개, 대소문자 무관, ValueError |
| `test_registry.py` | 16 | 단축/전체 이름 동일 타입, 매번 새 인스턴스 |
| `test_runner.py` | 16 | 정상 실행, 수수료, 벤치마크, 데이터 없음 에러 |
| `test_bots.py` | 26 | capital_pct 합계, 중복 이름, 알 수 없는 전략·유니버스 |
| `test_state.py` | 18 | 봇 stop/resume, 상태 격리, 파일 손상 복원 |

---

### 남은 작업

- 리스크 관리 (`daily_loss_limit_pct`, `max_drawdown_pct`) 미구현 — bots.yaml 필드만 정의
- CLI 백테스트 결과 웹 DB 저장 미구현
- 전략 CRUD CLI 미구현
