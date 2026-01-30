from app.core.config import get_settings
from app.storage.settings_repo import SettingsRepository
from app.storage.strategies_repo import StrategiesRepository


def bootstrap_storage() -> None:
    settings = get_settings()
    SettingsRepository(settings).ensure_defaults()
    StrategiesRepository(settings).ensure_seed()
