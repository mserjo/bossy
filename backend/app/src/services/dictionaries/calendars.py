# backend/app/src/services/dictionaries/calendars.py
# import logging # Замінено на централізований логер
# from typing import Optional # Для потенційних кастомних методів
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select # Для потенційних кастомних методів

# Повні шляхи імпорту
from backend.app.src.services.dictionaries.base_dict import BaseDictionaryService
from backend.app.src.models.dictionaries.calendars import CalendarProvider # Модель SQLAlchemy
from backend.app.src.schemas.dictionaries.calendars import ( # Схеми Pydantic
    CalendarProviderCreate,
    CalendarProviderUpdate,
    CalendarProviderResponse,
)
from backend.app.src.config.logging import logger # Централізований логер

class CalendarProviderService(BaseDictionaryService[CalendarProvider, CalendarProviderCreate, CalendarProviderUpdate, CalendarProviderResponse]):
    """
    Сервіс для управління елементами довідника "Постачальники Календарів".
    Ці елементи представляють різні платформи календарів, з якими система може інтегруватися
    (наприклад, Google Calendar, Outlook Calendar).
    Успадковує загальні CRUD-операції від BaseDictionaryService.
    Кожен постачальник може мати позначку `is_enabled`, яка вказує, чи активна інтеграція
    з цим постачальником на рівні системи.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує сервіс CalendarProviderService.

        :param db_session: Асинхронна сесія бази даних SQLAlchemy.
        """
        super().__init__(db_session, model=CalendarProvider, response_schema=CalendarProviderResponse)
        logger.info(f"CalendarProviderService ініціалізовано для моделі: {self._model_name}")

    # --- Кастомні методи для CalendarProviderService (якщо потрібні) ---
    # Наприклад, методи для перевірки, чи ввімкнено провайдера, або чи він потребує специфічної конфігурації:
    # async def is_provider_enabled(self, provider_code: str) -> bool:
    #     """
    #     Перевіряє, чи ввімкнено інтеграцію з вказаним постачальником календарів.
    #     Припускає наявність поля 'is_enabled' в моделі CalendarProvider.
    #
    #     :param provider_code: Код постачальника для перевірки.
    #     :return: True, якщо постачальник активний, інакше False.
    #     """
    #     provider = await self.get_by_code(provider_code)
    #     if provider and hasattr(provider, 'is_enabled') and provider.is_enabled:
    #         logger.debug(f"Постачальник календарів з кодом '{provider_code}' активний.")
    #         return True
    #     logger.debug(f"Постачальник календарів з кодом '{provider_code}' неактивний або не знайдений.")
    #     return False
    #
    # Примітка: Поля 'code', 'name', 'description', 'is_enabled' обробляються базовим сервісом,
    # якщо вони присутні в відповідних Pydantic схемах (Create, Update).

logger.debug(f"{CalendarProviderService.__name__} (сервіс постачальників календарів) успішно визначено.")
