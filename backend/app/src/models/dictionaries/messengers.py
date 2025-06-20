# backend/app/src/services/dictionaries/messengers.py
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.src.services.dictionaries.base_dict import BaseDictionaryService
from backend.app.src.models.dictionaries.messengers import MessengerPlatform # Модель SQLAlchemy
from backend.app.src.repositories.dictionaries.messenger_platform_repository import MessengerPlatformRepository # Імпорт репозиторію
from backend.app.src.services.cache.base_cache import BaseCacheService # Імпорт базового сервісу кешування
from backend.app.src.schemas.dictionaries.messengers import ( # Схеми Pydantic
    MessengerPlatformCreateSchema, # Виправлено
    MessengerPlatformUpdateSchema, # Виправлено
    MessengerPlatformResponseSchema, # Виправлено
)
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


class MessengerPlatformService(BaseDictionaryService[MessengerPlatform, MessengerPlatformRepository, MessengerPlatformCreateSchema, MessengerPlatformUpdateSchema, MessengerPlatformResponseSchema]):
    """
    Сервіс для управління елементами довідника "Платформи Месенджерів".
    Ці елементи представляють різні платформи обміну повідомленнями, з якими система може інтегруватися
    для надсилання сповіщень (наприклад, Telegram, Slack, Email).
    Успадковує загальні CRUD-операції від BaseDictionaryService.
    Кожна платформа може мати позначку `is_active_for_notifications`, що вказує, чи доступна
    вона для надсилання сповіщень в системі.
    """

    def __init__(self, db_session: AsyncSession, cache_service: BaseCacheService):
        """
        Ініціалізує сервіс MessengerPlatformService.

        :param db_session: Асинхронна сесія бази даних SQLAlchemy.
        :param cache_service: Екземпляр сервісу кешування.
        """
        messenger_platform_repo = MessengerPlatformRepository(model=MessengerPlatform)
        super().__init__(
            db_session,
            repository=messenger_platform_repo,
            cache_service=cache_service,
            response_schema=MessengerPlatformResponseSchema # Виправлено
        )
        # _model_name ініціалізується в BaseDictionaryService з repository.model.__name__
        logger.info(f"MessengerPlatformService ініціалізовано для моделі: {self._model_name}")

    # --- Кастомні методи для MessengerPlatformService (якщо потрібні) ---
    # Наприклад, методи для отримання нечутливих деталей конфігурації платформи.
    # Важливо: Чутливі дані, такі як токени API, ключі тощо, повинні зберігатися
    # безпечно в конфігурації системи (наприклад, settings.py або змінні середовища),
    # а не в цьому довіднику в базі даних.
    #
    # async def get_platform_public_details(self, platform_code: str) -> Optional[Dict[str, Any]]:
    #     """
    #     Отримує загальнодоступні деталі або нечутливу конфігурацію для платформи месенджера.
    #     Припускає наявність поля 'public_config_details' (наприклад, JSONB) в моделі MessengerPlatform.
    #
    #     :param platform_code: Код платформи.
    #     :return: Словник з деталями або None.
    #     """
    #     platform = await self.get_by_code(platform_code)
    #     if platform and hasattr(platform, 'public_config_details'):
    #         # Якщо public_config_details - це рядок JSON в БД, може знадобитися json.loads().
    #         # Якщо модель Pydantic вже обробляє це поле як Dict, перетворення не потрібне.
    #         config_details = getattr(platform, 'public_config_details', {})
    #         logger.debug(f"Отримано публічні деталі для платформи '{platform_code}': {config_details}")
    #         return config_details # type: ignore
    #     logger.debug(f"Публічні деталі для платформи '{platform_code}' не знайдено.")
    #     return None
    #
    # Примітка: Поля 'code', 'name', 'description', 'is_active_for_notifications' обробляються базовим сервісом,
    # якщо вони присутні в відповідних Pydantic схемах (Create, Update).

logger.debug(f"{MessengerPlatformService.__name__} (сервіс платформ месенджерів) успішно визначено.")
