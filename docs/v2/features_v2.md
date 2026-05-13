# StockFairy — FEATURES.md (v2)

> **상태** `[ ]` 미구현 · `[~]` 부분 구현 · `[x]` 완료 · `[-]` Out of scope
> **버전** `v2.1` 모의거래 · `v2.2` 실거래

---

## v2.1 — 모의거래 (Alpaca paper)

> 목표: 실거래와 동일한 로직으로 paper 계좌에서 충분히 검증한다.

### CLI

- `[x]` 여러 전략 동시 비교 `sf backtest compare --strategies <names>` — v2.1
- `[x]` 특정 봇 실행 `sf run --bot <name>` — v2.1
- `[x]` 전체 봇 순차 실행 `sf run --all` — v2.1
- `[x]` 전략별 포지션·잔고·실행 일정 `sf status` — v2.1
- `[x]` 특정 봇 중지 `sf stop --bot <name>` — v2.1
- `[x]` 전체 청산 후 중지 `sf stop --all --liquidate` — v2.1
- `[x]` `config/bots.yaml` 파싱 및 자본 비율 합계 검증 — v2.1

### Engine

- `[x]` OrderExecutor Protocol 정의 (`cancel_all_orders` 포함) — v2.1
- `[x]` AlpacaExecutor 구현 (`ALPACA_MODE=paper/live`, `cancel_all_orders`) — v2.1
- `[x]` 리밸런싱 주문 계산 (sell 먼저 / buy 나중, `capital_pct` 자본 배분) — v2.1
- `[x]` 미국 장 개장 시간 체크 (`engine/trading/market_hours.py`, 09:30–16:00 ET) — v2.1
- `[x]` `snp500` 유니버스 정의 (S&P 500 410개 종목) — v2.1
- `[x]` `sector_etf` 유니버스 정의 (XLK·XLF·XLE·XLV·XLI·XLY·XLP·XLU·XLB·XLRE·XLC) — v2.1

### 완료 기준 (v2.1)

- `[ ]` `sf run --all` Alpaca paper 주문 실행 성공
- `[ ]` `sf status` 전략별 포지션·잔고·다음 실행 일정 출력
- `[ ]` `sf stop --all --liquidate` paper 계좌 전체 청산 확인
- `[ ]` 리밸런싱 주기에 맞춰 클라우드 서버 crontab 자동 실행
- `[ ]` 2주 이상 paper 운용 후 실거래와 로직 차이 없음 확인

---

## v2.2 — 실거래 (Alpaca live)

> 목표: v2.1에서 검증된 로직을 그대로 live 계좌에 적용한다.
> v2.1과 코드 변경 없이 `.env`의 `ALPACA_MODE=live` 전환만으로 동작해야 한다.

### CLI

- `[ ]` 드라이런 `sf run --all --dry-run` → `--confirm` 으로 실행 — v2.2
- `[ ]` 자동 모드 `sf run --all --auto` (드라이런 스킵, crontab용) — v2.2
- `[ ]` 실행 이력 조회 `sf log --bot <name> --last <n>` — v2.2
- `[ ]` 운용 성과 리포트 `sf report --since <date>` — v2.2

### Engine

- `[ ]` AlpacaExecutor live mode 활성화 — v2.2
- `[ ]` 일일 손실 한도 (`daily_loss_limit_pct` 초과 시 당일 주문 중단) — v2.2
- `[ ]` 전략별 MDD 한도 (`max_drawdown_pct` 초과 시 해당 전략 자동 중지) — v2.2
- `[ ]` 드리프트 감지 (목표 비중 vs 현재 비중 임계값 초과 시 경고) — v2.2

### 완료 기준 (v2.2)

- `.env` `ALPACA_MODE=live` 전환만으로 실거래 전환 (코드 변경 없음)
- `sf run --all --dry-run` 주문 내역 확인 후 `--confirm` 실행
- 일일 손실 한도 도달 시 당일 주문 자동 중단
- 전략 MDD 한도 도달 시 해당 전략 자동 중지
- `sf log` · `sf report` 실거래 기준 성과 출력

---

## v1에서 이월 (변경 없음)

### Engine
- `[x]` Strategy Protocol, StrategyContext, StrategySignal
- `[x]` StrategySpec, UniverseSpec, RebalanceSpec, RiskSpec
- `[x]` 내장 전략 6개 (Momentum, TrendSMA200, RSI, LowVol, VolAdj, RiskOnOff)
- `[x]` 전략 레지스트리, 샌드박스, indicators, validation
- `[x]` DataProvider Protocol + YFinanceProvider + DBProvider
- `[x]` BacktestRunner, 성과 지표 (CAGR, Sharpe, MDD, alpha, beta)

### CLI
- `[x]` 단일 전략 백테스트 `sf backtest --strategy <name>`

---

## Out of scope (v2)

| 항목 | 이유 |
|---|---|
| 웹 UI 신규 개발 | CLI에 집중, v1 웹 유지만 |
| 전략 간 통합 주문 (방식 2) | 방식 1 안정화 후 재검토 |
| 텔레그램 알림 | v2.2 안정화 후 v3에서 |
| 전략 마켓플레이스 | v3 이후 |