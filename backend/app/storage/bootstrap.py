from app.core.config import get_settings
from app.storage.strategies_repo import StrategiesRepository
from app.storage.user_settings_repo import UserSettingsRepository
from app.storage.users_repo import UsersRepository


def bootstrap_storage() -> None:
    settings = get_settings()
    if settings.default_user_id:
        UsersRepository(settings).ensure(settings.default_user_id, display_name="Default User")
        UserSettingsRepository(settings).get_or_create(settings.default_user_id)
        StrategiesRepository(settings).ensure_seed(settings.default_user_id)
