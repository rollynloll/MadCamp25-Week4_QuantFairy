#  MATRX

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
```

## 설치 및 실행
### 1) Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2) Frontend
```bash
cd frontend
npm install
npm run dev
```

브라우저에서 `http://localhost:5173` 접속.

## 환경 변수
Backend는 `.env`를 사용합니다. 실제 키는 레포에 커밋하지 않는 것을 권장합니다.

```bash
# backend/.env (예시)
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
```

Frontend는 필요 시 `VITE_API_BASE_URL`을 설정합니다.
```bash
# frontend/.env (예시)
VITE_API_BASE_URL=http://localhost:8000
```

## 참고
- 기본 API prefix는 `/api/v1` 입니다.
- 실시간 시세/체결 스트리밍은 WebSocket을 사용합니다.
