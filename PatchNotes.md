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
