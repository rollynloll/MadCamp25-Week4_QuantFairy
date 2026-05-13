# StockFairy — SCOPE.md (v2)

> v1과의 차이: 웹 UI 개발 중단, CLI + Engine에 집중, Alpaca live 실거래 추가.
> 변경이 필요하면 이유와 날짜를 남기고 수정한다.

---

## 한 줄 정의

미국 주식 퀀트 전략을 백테스트하고, CLI로 여러 전략을 동시에 자동 매매하는 실전 투자 도구.

---

## v1 → v2 변경 사항

| 항목 | v1 | v2 |
|---|---|---|
| 인터페이스 | 웹 UI + CLI + REST API | CLI 전용 |
| 매매 범위 | Alpaca paper 우선 | Alpaca paper + live |
| 전략 운용 | 단일 전략 | 여러 전략 동시 운용 |
| 자본 배분 | 없음 | 전략별 자본 비율 할당 |
| 위험 관리 | 없음 | 일일 손실 한도, 전략별 MDD 한도 |
| 실행 환경 | 로컬 또는 서버 | 클라우드 서버 (상시 실행) |

---

## In scope

### 시장
- 미국 주식 (NYSE, NASDAQ) long-only
- **기본 유니버스**: S&P 500 (500개 종목)
- **섹터 유니버스**: GICS 섹터 ETF 11개 (XLK, XLF, XLE, XLV, XLI, XLY, XLP, XLU, XLB, XLRE, XLC)

### 유니버스 선택 기준

| 유니버스 | 종목 수 | 적합한 전략 |
|---|---|---|
| S&P 500 | 500개 | Momentum, RSI, LowVol — 종목 선별형 |
| 섹터 ETF 11개 | 11개 | 섹터 로테이션, RiskOnOff — 섹터 배분형 |

### 데이터
- 주가 데이터: yfinance
- 브로커 데이터: Alpaca API (포지션, 계좌, 주문)

### 기능
- 백테스트: 여러 전략 동시 비교, 성과 지표 계산
- 자동 매매: 전략별 자본 배분 + 독립적 리밸런싱 (방식 1)
- 위험 관리: 일일 손실 한도, 전략별 MDD 한도, 드라이런
- 모니터링: 포지션·계좌 조회, 실행 이력, 성과 리포트
- 스케줄러: 클라우드 서버 crontab 기반 자동 실행

### 인터페이스
- CLI (`sf` 커맨드) 전용

### 인프라
- DB: PostgreSQL (Supabase)
- 브로커: Alpaca paper + live
- 실행 환경: 클라우드 서버 (DigitalOcean 또는 연구실 서버)

---

## 구현 목록

### CLI

| 커맨드 | 설명 | 우선순위 |
|---|---|---|
| `sf backtest --strategies <names> --start <date> --end <date>` | 여러 전략 동시 백테스트 및 비교 | P0 |
| `sf run --bot <name>` | 특정 봇 리밸런싱 실행 | P0 |
| `sf run --all` | 전체 봇 순차 실행 | P0 |
| `sf run --all --dry-run` | 주문 내역 미리보기 후 `--confirm`으로 실행 | P1 |
| `sf run --all --auto` | 드라이런 스킵, 위험 한도 도달 시 중단만 (crontab용) | P1 |
| `sf status` | 전략별 포지션·잔고·마지막 실행·다음 실행 일정 | P0 |
| `sf stop --bot <name>` | 특정 봇 중지, 포지션 유지 | P0 |
| `sf stop --all --liquidate` | 전체 포지션 청산 후 중지 | P0 |
| `sf log --bot <name> --last <n>` | 리밸런싱 실행 이력 및 주문 내역 조회 | P2 |
| `sf report --since <date>` | 운용 성과 리포트 (수익률, MDD, Sharpe) | P2 |

**config/bots.yaml 구조**
```yaml
bots:
  - name: momentum_snp
    strategy: momentum_topn_v1
    universe: snp500          # S&P 500
    capital_pct: 0.40
    rebalance: weekly

  - name: sector_rotation
    strategy: rsi_mean_reversion_v1
    universe: sector_etf      # 섹터 ETF 11개
    capital_pct: 0.30
    rebalance: monthly

  - name: low_vol_snp
    strategy: low_volatility
    universe: snp500
    capital_pct: 0.30
    rebalance: monthly

risk:
  daily_loss_limit_pct: 0.05   # 하루 -5% 초과 시 주문 중단
  max_drawdown_pct: 0.20        # 고점 대비 -20% 시 전략 자동 중지
```

### Engine

| 기능 | 설명 | 우선순위 |
|---|---|---|
| OrderExecutor Protocol | `place_order`, `get_positions`, `get_account`, `cancel_all_orders` 인터페이스 정의 | P0 |
| AlpacaExecutor | OrderExecutor 구현체, paper / live mode는 .env에서 결정 | P0 |
| 리밸런싱 주문 계산 | 목표 비중 vs 현재 비중 diff, sell 먼저 / buy 나중, 수수료·슬리피지 반영 | P0 |
| 미국 장 개장 시간 체크 | 09:30~16:00 ET 외 주문 거부 | P0 |
| 유니버스 정의 | `snp500` (500개 종목 티커), `sector_etf` (11개 섹터 ETF 티커) | P0 |
| 일일 손실 한도 | 계좌 전체 당일 손실 `daily_loss_limit_pct` 초과 시 주문 중단 | P1 |
| 전략별 MDD 한도 | 전략 고점 대비 손실 `max_drawdown_pct` 초과 시 해당 전략 중지 | P1 |
| 드리프트 감지 | 목표 비중 vs 현재 비중 차이 임계값 초과 시 경고 출력 | P2 |

---

## Out of scope

| 항목 | 이유 |
|---|---|
| 웹 UI 신규 개발 | v2는 CLI에 집중. v1 웹은 유지만 함 |
| REST API 신규 개발 | CLI가 engine을 직접 호출, API 불필요 |
| 한국 주식, 암호화폐, 선물/옵션 | 미국 주식 long-only로 범위 고정 |
| 숏 포지션 | long-only로 범위 고정 |
| 전략 간 통합 주문 (방식 2) | 방식 1 안정화 후 재검토 |
| 전략 마켓플레이스 | Strategy Protocol 인터페이스로 확장 가능성만 확보, 구현은 v3 이후 |
| 실시간 체결 알림 (push/SMS) | 텔레그램 알림은 안정화 후 P3 |
| 멀티 브로커 지원 | Alpaca 단일 브로커로 범위 고정 |

---

## 기술 범위 고정

| 항목 | 결정 | 변경 조건 |
|---|---|---|
| CLI 프레임워크 | typer | 변경 없음 |
| DB | PostgreSQL (Supabase) | 변경 없음 |
| 브로커 SDK | alpaca-py | 변경 없음 |
| engine/ 의존성 | 순수 Python + pandas만 허용 | FastAPI·asyncpg·supabase import 시 설계 위반 |
| 전략 자본 배분 방식 | 전략별 독립 운용 (방식 1) | 방식 2는 방식 1 안정화 후 재검토 |
| 실행 환경 | 클라우드 서버 crontab | GitHub Actions는 보조 수단만 |

---

## 완료 기준

### CLI
1. `sf backtest --strategies momentum,rsi,low_vol` 여러 전략 동시 비교 출력 성공
2. `sf run --all` 전략별 자본 배분 후 Alpaca paper 주문 실행 성공
3. `sf run --all` Alpaca live 실거래 주문 실행 성공
4. `sf run --all --dry-run` 주문 내역 출력 후 `--confirm` 입력 시 실행
5. `sf status` 전략별 포지션·잔고·다음 실행 일정 출력
6. `sf stop --all --liquidate` 전체 포지션 청산 확인
7. 클라우드 서버 crontab `sf run --all --auto` 리밸런싱 주기 자동 실행

### Engine
1. 일일 손실 한도 도달 시 당일 주문 자동 중단
2. 전략 MDD 한도 도달 시 해당 전략 자동 중지
3. 미국 장 외 시간 주문 시도 시 거부
4. `snp500` · `sector_etf` 유니버스 정상 로드 및 가격 데이터 수신
5. sell 먼저 / buy 나중 순서로 주문 실행, 잔고 부족 에러 없음