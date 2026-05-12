# PatchNotes

---

## 2026-05-12

### 버그 수정

- **백테스트 NaN 전파 버그 수정** (`engine/backtest/runner.py`)
  - Python에서 `bool(float('nan')) == True` 이므로 `if prev_p and curr_p:` 조건이 NaN을 걸러내지 못함
  - `pd.notna()` 체크 추가 → 2014년 이전 장기 백테스트 정상 작동

---

### 백테스트 개선

- **진행률 표시 추가** (`cli/commands/backtest.py`)
  - 데이터 로드 → 신호 생성 → 시뮬레이션(0~100%) → 지표 계산 4단계 rich progress bar
  - `transient=True` 로 완료 후 자동 소멸

- **매매 기록 출력 추가** (`--trades`, `--top-n`)
  - 리밸런싱 날짜별 Equity / 포지션 수 / 턴오버 / 상위 N개 종목(비중) 테이블 출력
  - `BacktestResult.trade_log` 필드 신규 추가

---

### 자동매매 엔진 신규 구현

- **`engine/trading/` 모듈 신설**
  - `order.py` — `Order(symbol, side, notional)` 데이터클래스
  - `position.py` — `Position(symbol, qty, market_value, avg_entry_price, unrealized_pnl, unrealized_pnl_pct)`
  - `account.py` — `Account(equity, cash, buying_power, portfolio_value, currency)`
  - `broker.py` — `BrokerProvider` Protocol (브로커 교체 가능 구조)
  - `executor.py` — `compute_orders()` 순수 함수 (인프라 의존 없음)
  - `scheduler.py` — `should_rebalance()` + `run_live()` 한 사이클

- **`infra/broker/alpaca.py` 신규 구현**
  - `get_account()`, `get_positions()` (미실현 손익 포함), `place_orders()`, `is_market_open()`
  - `ALPACA_API_KEY_ID` / `ALPACA_API_SECRET_KEY` 환경 변수 사용

---

### CLI 신규 커맨드

- **`sf trade run`** — 자동매매 한 사이클 실행
  - `--dry-run` (기본) / `--execute` 로 실제 주문 제출 전환
  - 마지막 리밸런싱 날짜 `~/.sf/state.json` 자동 로드·저장

- **`sf trade schedule`** — APScheduler 장기 실행 (서버 배포용)
  - `monthly` / `weekly` / `daily` 주기에 맞춰 NYSE 개장 5분 후 자동 실행

- **`sf account show`** — 계좌 요약 (총 자산 / 현금 / 매수 가능 금액 / 시장 상태)

- **`sf account positions`** — 보유 포지션 상세 (평균 단가 / 미실현 손익 / 손익률 컬러)

---

### 환경 변수 분리

- `backend/.env` 에서 Alpaca / DEFAULT_USER_ID 항목을 프로젝트 루트 `madcamp-week4/.env` 로 이동
- `backend/.env` 에는 Supabase / DB 연결 정보만 유지
- `infra/broker/alpaca.py` 환경 변수명 수정: `ALPACA_API_KEY` → `ALPACA_API_KEY_ID`, `ALPACA_SECRET_KEY` → `ALPACA_API_SECRET_KEY`
- `cli/main.py` 에 `load_dotenv(루트/.env)` 자동 로드 추가
- `.env.example` 신규 생성 (협업용 템플릿)

---

### GitHub Actions 자동매매

- **`.github/workflows/trade.yml` 신규 생성**
  - 평일 매일 14:35 UTC (NYSE 9:35 AM ET) cron 트리거
  - Alpaca Clock API로 공휴일 자동 건너뜀 (`is_market_open` 체크)
  - 리밸런싱 상태를 `.trade/state.json` 으로 레포에 커밋 → 캐시 만료 없이 영구 보존
  - `workflow_dispatch` 수동 실행 + `dry_run` 선택 지원
  - `permissions: contents: write` + `[skip ci]` 커밋으로 재트리거 방지

---

### 기타

- `.gitignore` 에 `*.egg-info/` 추가
- `pyproject.toml` 에 `apscheduler>=3.10,<4` 의존성 추가
- `cli/container.py` 에 `get_broker()` 팩토리 추가 (브로커 교체 시 이 함수만 수정)
- `cli/state.py` 신규 생성 (`~/.sf/state.json` 읽기/쓰기)
- `features.md` 구현 상태 업데이트 (P1·P2·P4 완료, P3 미완)
- `engine/README.md`, `cli/README.md` 신규 내용 반영
