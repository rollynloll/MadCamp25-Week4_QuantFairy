from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings


def configure_cors(app, settings: Settings) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
