# MATRX

주식 퀀트 트레이딩을 위한 **대시보드 + 전략 관리 + 백테스트 + 실시간 트레이딩** 통합 플랫폼입니다.  
사용자는 전략을 관리하고, 백테스트로 검증한 뒤, 포트폴리오와 실시간 주문 흐름을 한 곳에서 확인할 수 있습니다.

## 기획 배경
- 여러 툴(백테스트, 포트폴리오, 트레이딩)을 따로 쓰는 번거로움을 줄이고 싶었습니다.
- 전략 실행 상태, 포트폴리오 성과, 실시간 시세/체결을 **하나의 화면**에서 확인하는 경험을 목표로 했습니다.
- 전략을 공유/복제하고 빠르게 실험할 수 있는 작업 흐름을 만들고자 했습니다.

## 주요 기능
- 대시보드: 계좌 요약, 성과 곡선, 활성 전략, 최근 거래
- 전략 관리: 공개 전략/내 전략 관리, 파라미터 및 리스크 설정
- 백테스트: 전략 단일/앙상블 백테스트, 결과 지표/차트
- 포트폴리오: 보유 종목/전략별 비중, 리밸런싱
- 트레이딩: 주문/포지션/호가/체결 및 실시간 스트리밍
- 봇 제어: 전략 실행/중지 및 상태 모니터링

## 기술 스택
**Frontend**
- React 19, TypeScript, Vite
- Tailwind CSS
- Zustand, Axios
- Recharts (차트)

**Backend**
- FastAPI, Uvicorn
- Pydantic v2
- Supabase (Postgres), asyncpg
- Alpaca API (트레이딩/마켓 데이터)
- yfinance, pandas
- WebSocket 스트리밍

## 프로젝트 구조
```
madcamp-week4/
  frontend/   # React + Vite SPA
  backend/    # FastAPI 서버
  engine/     # 순수 계산 엔진 (백테스트, 전략, 트레이딩 로직)
  infra/      # 브로커/데이터 어댑터 (Alpaca, yfinance, DB)
  cli/        # sf 커맨드라인 도구
  .env        # 환경 변수 (프로젝트 루트 단일 관리)
```

## 설치 및 실행
### 공통: 환경 변수 설정
프로젝트 루트의 `.env.example`을 복사해 `.env`를 만들고, 키를 채웁니다.
로컬 개발 시 `.env.local`로 오버라이드할 수 있습니다.

```bash
cp .env.example .env
# .env 파일을 열어 키 입력
```

### 1) Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2) Frontend
```bash
cd frontend
npm install
npm run dev
```

브라우저에서 `http://localhost:5173` 접속.

### 3) CLI (`sf`)
백테스트, 자동매매, 계좌 조회를 터미널에서 바로 실행할 수 있습니다.

```bash
# 프로젝트 루트에서 설치 (백엔드 venv 활성화 상태)
pip install -e ".[cli]"
```

#### 주요 커맨드
```bash
# 백테스트
sf backtest run --strategy momentum_topn_v1 --start 2020-01-01 --end 2024-12-31
sf backtest run --strategy momentum_topn_v1 --start 2020-01-01 --end 2024-12-31 --trades --top-n 5

# 자동매매
sf trade run --dry-run          # 매매 시뮬레이션 (실제 주문 없음)
sf trade run --execute          # 실제 주문 실행
sf trade schedule --freq daily  # APScheduler 장기 실행 (daily / weekly / monthly)

# 계좌
sf account show       # 계좌 요약 (현금, 포트폴리오 가치)
sf account positions  # 보유 포지션 + 미실현 손익
```

## 환경 변수
모든 환경 변수는 **프로젝트 루트 `.env`** 한 곳에서 관리합니다.  
로컬 오버라이드는 `.env.local`에 작성합니다 (`.gitignore` 등록 권장).

```bash
# .env (예시)
APP_NAME=QuantFairy API
ENV=development
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/postgres
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_SERVICE_ROLE_KEY=YOUR_SUPABASE_SERVICE_ROLE_KEY
DEFAULT_USER_ID=YOUR_DEFAULT_USER_ID

ALPACA_API_KEY_ID=YOUR_ALPACA_KEY
ALPACA_API_SECRET_KEY=YOUR_ALPACA_SECRET
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ALPACA_DATA_FEED=iex

ALLOW_LIVE_TRADING=false
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Frontend (Vite)
VITE_API_BASE_URL=https://YOUR_BACKEND_URL
VITE_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY
```

```bash
# .env.local (로컬 dev 오버라이드)
VITE_API_BASE_URL=http://localhost:8000
```

## 참고
- 기본 API prefix는 `/api/v1` 입니다.
- 실시간 시세/체결 스트리밍은 WebSocket을 사용합니다.
- GitHub Actions (`trade.yml`)로 평일 장 시작 후 자동매매를 실행합니다.
