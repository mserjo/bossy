# backend/app/src/services/dictionaries/messengers.py
# import logging # Замінено на централізований логер
# from typing import Optional, Dict, Any # Для потенційних кастомних методів
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select # Для потенційних кастомних методів

# Повні шляхи імпорту
from backend.app.src.services.dictionaries.base_dict import BaseDictionaryService
from backend.app.src.models.dictionaries.messengers import MessengerPlatform # Модель SQLAlchemy
from backend.app.src.schemas.dictionaries.messengers import ( # Схеми Pydantic
    MessengerPlatformCreate,
    MessengerPlatformUpdate,
    MessengerPlatformResponse,
)
from backend.app.src.config.logging import logger # Централізований логер

class MessengerPlatformService(BaseDictionaryService[MessengerPlatform, MessengerPlatformCreate, MessengerPlatformUpdate, MessengerPlatformResponse]):
    """
    Сервіс для управління елементами довідника "Платформи Месенджерів".
    Ці елементи представляють різні платформи обміну повідомленнями, з якими система може інтегруватися
    для надсилання сповіщень (наприклад, Telegram, Slack, Email).
    Успадковує загальні CRUD-операції від BaseDictionaryService.
    Кожна платформа може мати позначку `is_active_for_notifications`, що вказує, чи доступна
    вона для надсилання сповіщень в системі.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує сервіс MessengerPlatformService.

        :param db_session: Асинхронна сесія бази даних SQLAlchemy.
        """
        super().__init__(db_session, model=MessengerPlatform, response_schema=MessengerPlatformResponse)
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
