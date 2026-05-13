# cli/

StockFairy 퀀트 CLI. `sf` 커맨드로 전략 조회, 백테스트, 자동매매, 계좌 조회를 터미널에서 실행한다.

---

## 설치 및 환경 준비

```bash
# 프로젝트 루트 (madcamp-week4/) 에서 실행
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

설치 후 `sf` 커맨드가 venv에 등록된다.

### 환경 변수

자동매매·계좌 조회 기능은 Alpaca API 키가 필요하다.  
프로젝트 루트 `madcamp-week4/.env`에 아래 항목을 설정한다.

```ini
# madcamp-week4/.env

ALPACA_API_KEY_ID=PKxxxxxxxxxxxxxxxxxxxxxxxx
ALPACA_API_SECRET_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# paper | live  (기본값: paper)
ALPACA_MODE=paper

DEFAULT_USER_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

`sf` 커맨드 실행 시 `.env`와 `.env.local`이 자동으로 로드된다. `export`는 불필요하다.

---

## 커맨드 목록

```
sf
├── strategy
│   ├── list          등록된 전략 목록 출력
│   └── show          전략 상세 정보 출력
├── backtest
│   ├── run           백테스트 실행
│   └── compare       여러 전략 동시 비교 (v2.1)
├── run               bots.yaml 기반 다중 봇 실행 (v2.1)
├── status            봇 상태 조회 (v2.1)
├── stop              봇 중지·청산·재개 (v2.1)
├── trade
│   ├── run           단일 전략 한 사이클 실행
│   └── schedule      단일 전략 장기 반복 실행
└── account
    ├── show          계좌 요약
    └── positions     보유 포지션 목록
```

---

## sf strategy

### `sf strategy list`

등록된 모든 전략의 entrypoint와 이름을 테이블로 출력한다.

```bash
sf strategy list
```

### `sf strategy show <entrypoint>`

전략 이름과 기본 파라미터를 출력한다.

```bash
sf strategy show momentum
```

---

## sf backtest

### `sf backtest run`

#### 필수 옵션

| 옵션 | 설명 | 예시 |
|------|------|------|
| `--strategy` / `-s` | 전략 이름 | `momentum`, `low-vol` |
| `--start` | 시작일 | `2020-01-01` |
| `--end` | 종료일 | `2024-12-31` |

#### 유니버스 옵션 (우선순위 순)

| 옵션 | 설명 |
|------|------|
| `--universe AAPL,MSFT,NVDA` | 티커 직접 지정 (쉼표 구분) |
| `--sector technology` | S&P 500에서 해당 섹터만 필터 |
| (없음) | S&P 500 전체 (~430개) |

사용 가능한 섹터: `technology`, `healthcare`, `financials`, `energy`, `utilities`, `materials`, `industrials`, `discretionary`, `staples`, `realestate`, `communication`

#### 선택 옵션

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--initial-cash` | `10000.0` | 초기 자본금 (달러) |
| `--fee` | `0.0` | 거래 수수료 (bps) |
| `--slippage` | `0.0` | 슬리피지 (bps) |
| `--rebalance` | 전략 기본값 | `monthly` / `weekly` / `daily` |
| `--param key=value` | - | 전략 파라미터 (여러 번 사용 가능) |
| `--benchmark` | - | 벤치마크 티커 (알파·베타 계산용) |
| `--output` / `-o` | - | 결과 저장 경로 (`.json`) |
| `--trades` | `false` | 리밸런싱 매매 기록 테이블 출력 |
| `--top-n` | `5` | 매매 기록 상위 종목 수 (`--trades`와 함께 사용) |

#### 사용 예시

```bash
# 기본 실행
sf backtest run -s momentum --start 2020-01-01 --end 2024-12-31

# 섹터 필터 + 수수료 + 벤치마크
sf backtest run -s momentum \
  --start 2018-01-01 --end 2024-12-31 \
  --sector technology \
  --param top_n=5 --param lookback_days=126 \
  --fee 5 --slippage 2 \
  --benchmark SPY --rebalance monthly

# 매매 기록 출력
sf backtest run -s momentum --start 2022-01-01 --end 2024-12-31 --trades --top-n 10

# 결과를 JSON 파일로 저장
sf backtest run -s vol-momentum --start 2020-01-01 --end 2024-12-31 --output result.json
```

#### 출력 지표

| 지표 | 설명 |
|------|------|
| 총 수익률 | 전체 기간 누적 수익률 |
| CAGR | 연평균 복합 성장률 (252거래일 = 1년) |
| 연율화 변동성 | 일간 수익률 표준편차 × √252 |
| 샤프 비율 | CAGR / 변동성 (무위험수익률 0 가정) |
| 최대 낙폭 (MDD) | 고점 대비 최대 하락폭 |
| 알파·베타·트래킹 에러·정보 비율 | `--benchmark` 지정 시 계산 |
| 평균 회전율 | 리밸런싱당 평균 포트폴리오 교체 비율 |

저장되는 JSON 구조:
```json
{
  "metrics": { "total_return_pct": 87.4, "cagr_pct": 13.5, "..." },
  "equity_curve": [{"date": "2020-01-02", "equity": 10000.0}, "..."],
  "drawdown":     [{"date": "2020-01-02", "dd_pct": 0.0}, "..."]
}
```

---

### `sf backtest compare`

여러 전략을 동시 백테스트하고 성과를 비교 테이블로 출력한다. 각 지표에서 가장 좋은 값이 **초록 굵은 글씨**로 표시된다.

```bash
sf backtest compare \
  --strategies momentum,low-vol,rsi-reversion \
  --start 2020-01-01 --end 2024-12-31

# 사용자 정의 유니버스 + 벤치마크
sf backtest compare \
  --strategies momentum,risk-on-off \
  --start 2019-01-01 --end 2024-12-31 \
  --universe XLK,XLF,XLE,XLV,XLI,XLY,XLP,XLU,XLB,XLRE,XLC \
  --benchmark SPY
```

---

## sf run

`bots.yaml`에 정의된 봇을 실행한다. 각 봇은 `capital_pct`에 비례한 자본 슬라이스로 독립 운용된다.

| 옵션 | 설명 |
|------|------|
| `--all` | 전체 봇 순차 실행 |
| `--bot <name>` | 특정 봇 하나만 실행 |
| `--dry-run` | 주문 미리보기만 (실제 제출 안 함) |
| `--config <path>` | bots.yaml 경로 (기본: `config/bots.yaml`) |

```bash
sf run --all              # 전체 봇 실행
sf run --all --dry-run    # 주문 미리보기
sf run --bot momentum_snp # 특정 봇만 실행
```

**실행 흐름**
```
1. bots.yaml 로드 및 검증 (capital_pct 합계, 전략·유니버스 유효성)
2. Alpaca API → 총 자산 조회
3. 각 봇 순차 실행:
   a. bot_equity = total_equity × capital_pct
   b. yfinance → 가격 데이터 조회
   c. 전략 → 목표 비중 계산
   d. compute_orders() → 주문 생성 (sell 먼저 / buy 나중)
   e. --dry-run 아니면 실제 주문 제출
4. 리밸런싱 날짜 ~/.sf/state.json 저장
```

리밸런싱 주기 미도달 봇과 `sf stop`으로 중지된 봇은 자동 건너뛴다.

### bots.yaml 구조

```yaml
# config/bots.yaml
bots:
  - name: momentum_snp
    strategy: momentum_topn_v1   # sf strategy list 참고
    universe: snp500             # snp500 | sector_etf
    capital_pct: 0.40            # 전체 자산의 40%
    rebalance: weekly            # daily | weekly | monthly

  - name: sector_rotation
    strategy: rsi_mean_reversion_v1
    universe: sector_etf
    capital_pct: 0.30
    rebalance: monthly

  - name: low_vol_snp
    strategy: low_volatility
    universe: snp500
    capital_pct: 0.30
    rebalance: monthly

risk:
  daily_loss_limit_pct: 0.05   # 하루 -5% 초과 시 주문 중단 (v2.2)
  max_drawdown_pct: 0.20        # 고점 대비 -20% 시 전략 자동 중지 (v2.2)
```

**검증 규칙**
- `capital_pct` 합계 ≤ 1.0 (초과 시 실행 거부)
- `strategy`는 `sf strategy list` 출력 값 (단축형·전체 이름 모두 허용)
- `universe`는 `snp500` 또는 `sector_etf`

**유니버스 프리셋**

| 프리셋 | 종목 수 | 내용 |
|--------|---------|------|
| `snp500` | ~410개 | S&P 500 구성 종목 |
| `sector_etf` | 11개 | XLK, XLF, XLE, XLV, XLI, XLY, XLP, XLU, XLB, XLRE, XLC |

---

## sf status

각 봇의 현재 상태, 마지막 실행일, 다음 실행 예정일, 계좌 요약을 출력한다.

```bash
sf status
sf status --config ~/my-bots.yaml
```

출력 예시:
```
계좌 요약  총자산 $100,000.00  현금 $45,230.00  매수여력 $45,230.00

                         봇 상태
┌──────────────────┬────────────────────┬────────────┬─────────┬──────┬─────────────┬────────────┬────────────┬──────────┐
│ 봇               │ 전략               │ 유니버스   │ 주기    │ 자본%│ 자본($)     │ 마지막 실행 │ 다음 실행  │ 상태     │
├──────────────────┼────────────────────┼────────────┼─────────┼──────┼─────────────┼────────────┼────────────┼──────────┤
│ momentum_snp     │ momentum_topn_v1   │ snp500     │ weekly  │  40% │  $40,000    │ 2026-05-12 │ 2026-05-19 │ 실행중   │
│ sector_rotation  │ rsi_mean_reversion │ sector_etf │ monthly │  30% │  $30,000    │ 2026-05-01 │ 2026-06-01 │ 실행중   │
│ low_vol_snp      │ low_volatility     │ snp500     │ monthly │  30% │  $30,000    │     -      │ 오늘       │ 실행중   │
└──────────────────┴────────────────────┴────────────┴─────────┴──────┴─────────────┴────────────┴────────────┴──────────┘
```

다음 실행일이 오늘 이하이면 노란색으로 표시된다.

---

## sf stop

봇을 중지하거나 포지션을 청산한다. 중지된 봇은 `sf run`에서 자동으로 건너뛴다.

| 옵션 | 설명 |
|------|------|
| `--bot <name>` | 특정 봇 중지 |
| `--all` | 전체 봇 중지 |
| `--liquidate` | 미체결 주문 취소 + 전체 포지션 청산 |
| `--resume` | 중지된 봇 재개 |

```bash
sf stop --bot momentum_snp          # 포지션 유지, 봇만 중지
sf stop --all --liquidate           # 전체 중지 + 청산 (확인 프롬프트)
sf stop --bot momentum_snp --resume # 봇 재개
```

---

## sf trade

단일 전략 자동매매 (v1 호환). 리밸런싱 상태는 `~/.sf/state.json`에 저장된다.

### `sf trade run`

한 사이클을 즉시 실행한다. 기본값은 `--dry-run`으로 주문 계산만 하고 실제 제출은 하지 않는다.

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--strategy` / `-s` | (필수) | 전략 이름 |
| `--universe` | - | 티커 직접 지정 (쉼표 구분) |
| `--sector` | - | S&P 500 섹터 필터 |
| `--rebalance` | `monthly` | `monthly` / `weekly` / `daily` |
| `--lookback-days` | `400` | 가격 데이터 조회 기간 (일) |
| `--min-order` | `1.0` | 최소 주문 금액 (달러) |
| `--param key=value` | - | 전략 파라미터 |
| `--dry-run` / `--execute` | `--dry-run` | 주문 계산만 / 실제 제출 |

```bash
sf trade run -s momentum --sector technology           # dry-run
sf trade run -s momentum --sector technology --execute # 실제 주문
```

### `sf trade schedule`

프로세스가 살아있는 동안 주기에 맞춰 자동 반복한다.

```bash
sf trade schedule -s momentum --sector technology --rebalance monthly
```

| 주기 | 실행 시각 |
|------|-----------|
| `monthly` | 매월 1일 9:35 AM ET |
| `weekly` | 매주 월요일 9:35 AM ET |
| `daily` | 평일 매일 9:35 AM ET |

> 다중 봇 운용은 `sf run`을 사용한다.

---

## sf account

### `sf account show`

```bash
sf account show
```

계좌 요약(총 자산, 포지션 시장가치, 현금, 매수 가능 금액)을 출력한다.

### `sf account positions`

```bash
sf account positions
```

보유 포지션 상세 목록(평균 단가, 미실현 손익)을 출력한다.

---

## 자동 실행

### crontab (서버/VPS 권장)

각 봇의 `rebalance` 주기에 따라 알아서 건너뛰므로, crontab은 daily로 설정해도 된다.

```bash
# crontab -e
# 평일 매일 09:35 ET (14:35 UTC)
35 14 * * 1-5 cd /path/to/madcamp-week4 && /path/to/.venv/bin/sf run --all >> ~/.sf/trade.log 2>&1
```

> **DST 주의**: crontab은 UTC 고정. 14:35 UTC = 9:35 ET(겨울) / 10:35 ET(여름).  
> 월간·주간 전략에서는 1시간 차이가 문제되지 않는다.

### GitHub Actions (서버 없이 사용)

`.github/workflows/trade.yml`이 이미 설정돼 있다.

**Secrets/Variables 등록** (리포 → Settings)

| 이름 | 종류 | 설명 |
|------|------|------|
| `ALPACA_API_KEY_ID` | Secret | Alpaca API Key ID |
| `ALPACA_API_SECRET_KEY` | Secret | Alpaca Secret Key |
| `DEFAULT_USER_ID` | Secret | 사용자 ID |
| `ALPACA_MODE` | Variable | `paper` 또는 `live` |

**전략 설정**: `trade.yml`의 `Execute trade` 스텝 수정

```yaml
run: |
  sf run --all   # 또는 sf trade run -s momentum --execute
```

**스케줄 설정**: `trade.yml` 상단 cron 변경

```yaml
schedule:
  - cron: "35 14 1 * *"    # 매월 1일
  # - cron: "35 14 * * 1"  # 매주 월요일
  # - cron: "35 14 * * 1-5" # 평일 매일
```

수동 실행: 리포 → Actions → **Automated Trading** → **Run workflow**

---

## 디렉토리 구조

```
madcamp-week4/
├── .env                 # Alpaca API 키, ALPACA_MODE, DEFAULT_USER_ID
├── config/
│   └── bots.yaml        # 봇 설정 (전략·유니버스·자본 배분)
├── engine/
│   ├── backtest/        # 백테스트 엔진 (runner, metrics)
│   ├── strategies/      # 전략 Protocol, 레지스트리, 내장 전략 6개
│   ├── trading/         # Order, Position, compute_orders, run_live
│   │   └── market_hours.py   # 미국 장 시간 체크 (09:30–16:00 ET)
│   ├── data/
│   │   └── universe.py  # resolve_universe_preset (snp500, sector_etf)
│   └── errors.py        # DataNotFoundError, MarketClosedError 등
├── infra/
│   └── broker/
│       └── alpaca.py    # AlpacaBroker (ALPACA_MODE=paper|live)
└── cli/
    ├── main.py          # sf 앱 진입점, .env 로드, 커맨드 등록
    ├── container.py     # DI 팩토리 — get_data_provider(), get_broker()
    ├── bots.py          # bots.yaml 파싱·검증
    ├── state.py         # 리밸런싱 상태 영속화 (~/.sf/state.json)
    └── commands/
        ├── strategy.py  # sf strategy list / show
        ├── backtest.py  # sf backtest run / compare
        ├── run.py       # sf run
        ├── status.py    # sf status
        ├── stop.py      # sf stop
        ├── trade.py     # sf trade run / schedule
        └── account.py   # sf account show / positions
```
