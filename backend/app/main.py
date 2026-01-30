from fastapi import FastAPI

from app.bot.routes import router as bot_router
from app.core.config import get_settings
from app.core.cors import configure_cors
from app.core.errors import add_exception_handlers
from app.dashboard.routes import router as dashboard_router
from app.storage.bootstrap import bootstrap_storage
from app.strategies.routes import router as strategies_router
from app.trading.routes import router as trading_router

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="1.0")
    configure_cors(app, settings)
    add_exception_handlers(app)

    app.include_router(dashboard_router, prefix="/api/v1")
    app.include_router(strategies_router, prefix="/api/v1")
    app.include_router(trading_router, prefix="/api/v1")
    app.include_router(bot_router, prefix="/api/v1")

    @app.get("/")
    async def root():
        return {"message": "QuantFairy API is running"}

    @app.on_event("startup")
    async def _startup() -> None:
        bootstrap_storage()

    return app


app = create_app()
