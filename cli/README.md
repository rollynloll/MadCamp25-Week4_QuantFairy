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

# Alpaca 브로커
ALPACA_API_KEY_ID=PKxxxxxxxxxxxxxxxxxxxxxxxx
ALPACA_API_SECRET_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ALAPCA_API_BASE_URL=https://paper-api.alpaca.markets   # 페이퍼 트레이딩 URL

# 페이퍼 트레이딩 여부 (true = 페이퍼, false = 실거래)
ALPACA_PAPER=true

# 기본 사용자 ID (웹 서버 연동 시 사용)
DEFAULT_USER_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

`sf` 커맨드 실행 시 이 파일이 자동으로 로드된다. `export`는 불필요하다.

---

## 커맨드 목록

```
sf
├── strategy
│   ├── list          등록된 전략 목록 출력
│   └── show          전략 상세 정보 출력
├── backtest
│   └── run           백테스트 실행
├── trade
│   └── run           자동매매 한 사이클 실행
└── account
    ├── show          계좌 요약 (자산, 현금, 매수 가능 금액)
    └── positions     보유 포지션 상세 목록
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

## sf backtest run

### 필수 옵션

| 옵션 | 설명 | 예시 |
|------|------|------|
| `--strategy` / `-s` | 전략 이름 | `momentum`, `low-vol` |
| `--start` | 시작일 | `2020-01-01` |
| `--end` | 종료일 | `2024-12-31` |

### 유니버스 옵션 (우선순위 순)

| 옵션 | 설명 |
|------|------|
| `--universe AAPL,MSFT,NVDA` | 티커 직접 지정 (쉼표 구분, 공백 없이) |
| `--sector technology` | S&P 500에서 해당 섹터만 필터 |
| (없음) | S&P 500 전체 (~430개) |

사용 가능한 섹터:

| 키 | GICS 섹터 명칭 |
|----|----------------|
| `technology` | Information Technology |
| `healthcare` | Health Care |
| `financials` | Financials |
| `energy` | Energy |
| `utilities` | Utilities |
| `materials` | Materials |
| `industrials` | Industrials |
| `discretionary` | Consumer Discretionary |
| `staples` | Consumer Staples |
| `realestate` | Real Estate |
| `communication` | Communication Services |

### 선택 옵션

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--initial-cash` | `10000.0` | 초기 자본금 (달러) |
| `--fee` | `0.0` | 거래 수수료 (bps, 1bps = 0.01%) |
| `--slippage` | `0.0` | 슬리피지 (bps) |
| `--rebalance` | 전략 기본값 | 리밸런싱 주기 (`monthly` / `weekly` / `daily`) |
| `--param key=value` | - | 전략 파라미터 (여러 번 사용 가능) |
| `--benchmark` | - | 벤치마크 티커 (알파·베타 계산용) |
| `--output` / `-o` | - | 결과 저장 경로 (`.json`) |
| `--trades` | `false` | 리밸런싱 매매 기록 테이블 출력 |
| `--top-n` | `5` | 매매 기록에서 표시할 상위 종목 수 (`--trades`와 함께 사용) |

### 사용 예시

```bash
# 기본 실행 (S&P 500 전체)
sf backtest run -s momentum --start 2020-01-01 --end 2024-12-31

# 섹터 필터
sf backtest run -s momentum --start 2020-01-01 --end 2024-12-31 --sector technology

# 티커 직접 지정
sf backtest run -s low-vol \
  --start 2019-01-01 --end 2024-12-31 \
  --universe AAPL,MSFT,NVDA,GOOGL,META,AMZN

# 전략 파라미터 + 수수료 + 벤치마크
sf backtest run -s momentum \
  --start 2018-01-01 --end 2024-12-31 \
  --sector technology \
  --param top_n=5 --param lookback_days=126 \
  --fee 5 --slippage 2 \
  --benchmark SPY --rebalance monthly

# 매매 기록 출력 (상위 10개 종목)
sf backtest run -s momentum --start 2022-01-01 --end 2024-12-31 --trades --top-n 10

# 결과를 JSON 파일로 저장
sf backtest run -s vol-momentum --start 2020-01-01 --end 2024-12-31 --output result.json
```

매매 기록 출력 예시:
```
                         매매 기록 (24건)
┌────────────┬────────────┬───────────┬────────┬──────────────────────────────┐
│ 날짜       │     Equity │ 포지션 수 │ 턴오버 │ 상위 5개 종목 (비중)         │
├────────────┼────────────┼───────────┼────────┼──────────────────────────────┤
│ 2023-02-03 │ $10,000.00 │        10 │  50.0% │ FSLR:10.0%  ENPH:10.0%  ...  │
│ 2023-03-03 │  $9,918.57 │        10 │  20.0% │ FSLR:10.0%  ON:10.0%  ...    │
└────────────┴────────────┴───────────┴────────┴──────────────────────────────┘
```

- **턴오버**: 리밸런싱 시 포트폴리오가 교체된 비율 (단방향, 0~100%)
- **상위 N개 종목**: 비중 내림차순 정렬, `+N개`는 표시되지 않은 나머지 종목 수

저장되는 JSON 구조:
```json
{
  "metrics": { "total_return_pct": 87.4, "cagr_pct": 13.5, ... },
  "equity_curve": [{"date": "2020-01-02", "equity": 10000.0}, ...],
  "drawdown":     [{"date": "2020-01-02", "dd_pct": 0.0}, ...]
}
```

---

## sf account

계좌 요약과 보유 포지션을 조회한다. `madcamp-week4/.env`의 Alpaca API 키를 사용한다.

### `sf account show`

계좌 요약 정보를 출력한다.

```bash
sf account show
```

출력 예시:
```
          계좌 요약
┌─────────────────┬──────────────┐
│ 항목            │         금액 │
├─────────────────┼──────────────┤
│ 총 자산         │  $25,430.00  │
│ 포지션 시장가치  │  $18,200.00  │
│ 현금 잔고       │   $7,230.00  │
│ 매수 가능 금액  │   $7,230.00  │
│ 통화            │          USD │
│ 시장 상태       │         개장 │
└─────────────────┴──────────────┘
```

### `sf account positions`

보유 포지션 상세 목록(평균 단가, 미실현 손익 포함)을 출력한다.

```bash
sf account positions
```

출력 예시:
```
              보유 포지션 (5개 / 총 자산 $25,430.00)
┌──────┬────────┬──────────┬───────────┬──────┬────────────┬────────┐
│ 종목 │   수량 │ 평균단가 │  시장가치 │ 비중 │ 미실현손익 │ 손익률 │
├──────┼────────┼──────────┼───────────┼──────┼────────────┼────────┤
│ NVDA │ 3.1200 │  $892.40 │ $4,521.00 │17.8% │  +$733.20  │ +8.36% │
│ AAPL │ 8.5000 │  $172.30 │ $1,504.30 │ 5.9% │   -$19.55  │ -1.28% │
└──────┴────────┴──────────┴───────────┴──────┴────────────┴────────┘
```

---

## sf trade

자동매매 커맨드. 리밸런싱 여부를 판단하고 Alpaca API로 주문을 생성·제출한다.  
마지막 리밸런싱 날짜는 `~/.sf/state.json`에 자동 저장·로드된다.

### sf trade run

한 사이클을 즉시 실행한다. 기본값은 `--dry-run`으로 주문 계산만 하고 실제 제출은 하지 않는다.

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--strategy` / `-s` | (필수) | 전략 이름 |
| `--universe` | - | 티커 직접 지정 (쉼표 구분) |
| `--sector` | - | S&P 500 섹터 필터 |
| `--rebalance` | `monthly` | 리밸런싱 주기 (`monthly` / `weekly` / `daily`) |
| `--lookback-days` | `400` | 가격 데이터 조회 기간 (일) |
| `--min-order` | `1.0` | 최소 주문 금액 (달러, 이하 주문 생략) |
| `--param key=value` | - | 전략 파라미터 (여러 번 사용 가능) |
| `--dry-run` / `--execute` | `--dry-run` | 주문 계산만 하거나 실제 제출 |

```bash
# 주문 계산만 확인 (dry-run)
sf trade run -s momentum --sector technology

# 실제 주문 제출
sf trade run -s momentum --sector technology --execute
```

실행 흐름:
```
1. ~/.sf/state.json → 마지막 리밸런싱 날짜 로드
2. should_rebalance() → 리밸런싱 날이 아니면 현재 포지션 출력 후 종료
3. yfinance로 최근 lookback-days 가격 조회
4. 전략 → 목표 비중 계산
5. Alpaca API → 현재 포지션·자산 조회
6. compute_orders() → 주문 목록 생성
7. --execute일 때만 실제 주문 제출 + 상태 저장
```

### sf trade schedule

서버(VPS 등)에서 장기 실행. 프로세스가 살아있는 동안 주기에 맞춰 자동 반복한다.

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--strategy` / `-s` | (필수) | 전략 이름 |
| `--sector` / `--universe` | - | 유니버스 지정 |
| `--rebalance` | `monthly` | 리밸런싱 주기 |
| `--lookback-days` | `400` | 가격 데이터 조회 기간 |

```bash
# 서버에서 실행 (항상 --execute 모드)
sf trade schedule -s momentum --sector technology --rebalance monthly
```

실행 시각 (NYSE 기준, 장 개시 35분 후):

| 주기 | 실행 시각 |
|------|-----------|
| `monthly` | 매월 1일 9:35 AM ET |
| `weekly` | 매주 월요일 9:35 AM ET |
| `daily` | 평일 매일 9:35 AM ET |

---

## GitHub Actions 자동매매 (컴퓨터 꺼져도 동작)

서버 없이 GitHub Actions의 cron으로 자동매매를 실행한다.  
`.github/workflows/trade.yml`이 이미 설정돼 있다.

### 1단계 — GitHub Secrets 등록

리포 → Settings → Secrets and variables → **Actions** → **New repository secret**

| Secret 이름 | 설명 |
|-------------|------|
| `ALPACA_API_KEY_ID` | Alpaca API Key ID |
| `ALPACA_API_SECRET_KEY` | Alpaca Secret Key |
| `DEFAULT_USER_ID` | 사용자 ID |

리포 → Settings → Variables → **New repository variable**

| Variable 이름 | 값 |
|--------------|-----|
| `ALPACA_PAPER` | `true` (페이퍼) 또는 `false` (실거래) |

### 2단계 — 전략 설정

`.github/workflows/trade.yml`의 `Execute trade` 스텝에서 명령어를 수정한다.

```yaml
run: |
  sf trade run -s momentum --sector technology --execute
  # ↑ 원하는 전략·유니버스·파라미터로 변경
```

### 3단계 — 스케줄 설정

`trade.yml` 상단의 cron을 원하는 주기로 변경한다.

```yaml
schedule:
  - cron: "35 14 1 * *"    # 매월 1일 9:35 AM ET
  # - cron: "35 14 * * 1"  # 매주 월요일
  # - cron: "35 14 * * 1-5" # 평일 매일
```

> **DST 주의**: GitHub Actions cron은 UTC 고정. 14:35 UTC = 9:35 ET(EST 겨울) / 10:35 ET(EDT 여름).  
> 월간·주간 전략에서는 1시간 차이가 문제되지 않는다.

### 수동 실행

리포 → Actions → **Automated Trading** → **Run workflow**  
`dry_run = true`로 먼저 테스트한 뒤 `false`로 실제 주문을 제출한다.

### 상태 파일 관리

리밸런싱 날짜는 `.trade/state.json`에 저장되고 자동으로 레포에 커밋된다.

```json
{ "momentum|technology|monthly": "2025-05-01" }
```

캐시와 달리 레포에 영구 보존되므로 Actions 캐시가 만료돼도 상태가 유지된다.

---

## 출력 지표 설명 (sf backtest run)

```
백테스트 결과
┌────────────────┬───────────┐
│ 지표           │ 값        │
├────────────────┼───────────┤
│ 총 수익률      │ +87.40%   │  전체 기간 누적 수익률
│ CAGR           │ +13.50%   │  연평균 복합 성장률 (252거래일 = 1년)
│ 연율화 변동성  │ +18.20%   │  일간 수익률 표준편차 × √252
│ 샤프 비율      │  1.1200   │  CAGR / 변동성 (무위험수익률 0 가정)
│ 최대 낙폭      │ -18.30%   │  고점 대비 최대 하락폭
│ 알파           │  +3.20%   │  벤치마크 대비 초과 수익 (연율화)
│ 베타           │  0.8500   │  시장 민감도
│ 트래킹 에러    │  +8.40%   │  초과 수익률 변동성
│ 정보 비율      │  0.7600   │  알파 / 트래킹 에러
│ 평균 회전율    │  +12.50%  │  리밸런싱당 평균 포트폴리오 교체 비율
└────────────────┴───────────┘
```

알파·베타·트래킹 에러·정보 비율은 `--benchmark` 옵션을 지정해야 계산된다.

---

## 디렉토리 구조

```
madcamp-week4/
├── .env                 # Alpaca API 키, DEFAULT_USER_ID (자동 로드)
└── cli/
    ├── main.py          # sf 앱 진입점, 루트 .env 로드, 서브커맨드 등록
    ├── container.py     # DI 팩토리 — get_data_provider(), get_broker()
    └── commands/
        ├── strategy.py  # sf strategy list / show
        ├── backtest.py  # sf backtest run
        ├── trade.py     # sf trade run
        └── account.py   # sf account show / positions
```

`container.py`의 `get_broker()`가 `AlpacaBroker`를 반환한다.  
다른 브로커로 교체할 때는 이 함수만 수정한다.
