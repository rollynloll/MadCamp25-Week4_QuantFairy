# test/

`engine/`과 `cli/` 기능 테스트 모음. pytest 기반, 외부 네트워크·DB 의존 없음.

---

## 실행

```bash
# 프로젝트 루트에서
source .venv/bin/activate
pytest test/ -v
```

특정 파일 또는 클래스만 실행:

```bash
pytest test/engine/test_executor.py -v
pytest test/engine/test_scheduler.py::TestRunLive -v
pytest test/cli/ -v
```

---

## 테스트 구조

```
test/
├── conftest.py          # 공통 픽스처 (equity curve, 가격 데이터, 브로커 목)
├── engine/
│   ├── test_metrics.py      # 성과 지표 계산 (CAGR, Sharpe, MDD, alpha/beta)
│   ├── test_executor.py     # 주문 계산 (sell-first 순서, min notional, 엣지케이스)
│   ├── test_scheduler.py    # should_rebalance, run_live (capital_pct, dry-run)
│   ├── test_market_hours.py # 미국 장 시간 체크, MarketClosedError
│   ├── test_universe.py     # snp500/sector_etf 프리셋, resolve_universe
│   ├── test_registry.py     # 전략 레지스트리 (단축형·전체 이름 키)
│   └── test_runner.py       # BacktestRunner 통합 테스트
└── cli/
    ├── test_bots.py         # bots.yaml 파싱·검증 (capital_pct 합계, 이름 중복 등)
    └── test_state.py        # 리밸런싱 상태 영속화, 봇 중지/재개 상태
```

---

## 커버리지 요약

| 파일 | 테스트 수 | 주요 케이스 |
|------|-----------|-------------|
| `test_metrics.py` | 19 | 빈 곡선, flat 곡선, MDD 계산, alpha/beta, NaN 없음 확인 |
| `test_executor.py` | 22 | sell-first 순서 보장, min notional 임계값, zero delta 무시 |
| `test_scheduler.py` | 16 | daily/weekly/monthly 경계값, capital_pct 스케일링, dry-run |
| `test_market_hours.py` | 16 | 개장 전·후, 주말, 정각 경계, MarketClosedError 메시지 |
| `test_universe.py` | 20 | sector_etf 11개 정확성, 대소문자 무관, ValueError |
| `test_registry.py` | 16 | 단축/전체 이름 동일 타입, 매번 새 인스턴스, 빈 문자열 |
| `test_runner.py` | 16 | 정상 실행, 수수료, 벤치마크, 데이터 없음 에러 |
| `test_bots.py` | 26 | capital_pct 합계>1.0, 중복 이름, 알 수 없는 전략·유니버스 |
| `test_state.py` | 18 | 상태 파일 격리, 봇 stop/resume, 파일 손상 복원 |
| **합계** | **199** | |

---

## 픽스처

`conftest.py`에서 테스트 전반에 걸쳐 공유되는 픽스처를 정의한다.

| 픽스처 | 설명 |
|--------|------|
| `rising_curve` | $10k → $11k 상승 자산 곡선 |
| `flat_curve` | 변동 없는 자산 곡선 |
| `declining_curve` | $10k → $5k 하락 자산 곡선 |
| `recovery_curve` | 하락 후 완전 회복 곡선 |
| `sample_prices` | AAPL·MSFT·GOOG 2년치 종가 (결정론적 seed=42) |
| `mock_data_provider` | `sample_prices`를 반환하는 DataProvider 목 |
| `mock_broker` | Alpaca API 없이 동작하는 BrokerProvider 목 |
| `positions_with_holdings` | AAPL $40k + MSFT $30k 포지션 |
| `equal_weight_strategy` | 상위 2종목 균등 배분 전략 목 |
| `ctx` | 기본 StrategyContext |

---

## 설계 원칙

- **외부 의존 없음**: 모든 테스트는 yfinance, Alpaca API, Supabase 호출 없이 실행된다. 네트워크 I/O가 필요한 부분은 `unittest.mock.MagicMock`으로 대체한다.
- **격리**: `test_state.py`는 `tmp_path` + `patch`로 `~/.sf/state.json`을 격리해 테스트 간 상태 오염을 방지한다.
- **엣지케이스 포함**: 빈 데이터, 경계값(16:00 정각, capital_pct=1.0, delta=min_notional), 파일 손상 등 비정상 입력을 별도로 검증한다.
- **engine 순수성**: `engine/` 테스트에 fastapi, asyncpg, supabase import가 없음을 verify한다.
