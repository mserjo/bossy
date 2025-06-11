# backend/app/src/repositories/dictionaries/calendar_provider_repository.py
"""
Репозиторій для моделі "Постачальник Календарів" (CalendarProvider).

Цей модуль визначає клас `CalendarProviderRepository`, який успадковує `BaseDictionaryRepository`
та надає методи для роботи з довідником постачальників календарів.
"""

from sqlalchemy.ext.asyncio import AsyncSession

# Абсолютний імпорт базового репозиторію для довідників
from backend.app.src.repositories.dictionaries.base_dict_repository import BaseDictionaryRepository

# Абсолютний імпорт моделі та схем для Постачальників Календарів
from backend.app.src.models.dictionaries.calendars import CalendarProvider
from backend.app.src.schemas.dictionaries.calendars import CalendarProviderCreateSchema, CalendarProviderUpdateSchema
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)


class CalendarProviderRepository(
    BaseDictionaryRepository[CalendarProvider, CalendarProviderCreateSchema, CalendarProviderUpdateSchema]):
    """
    Репозиторій для управління записами довідника "Постачальник Календарів".

    Успадковує всі базові методи CRUD та специфічні для довідників методи
    від `BaseDictionaryRepository`.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `CalendarProvider`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=CalendarProvider)

    # Тут можна додати специфічні методи для CalendarProviderRepository, якщо вони потрібні.


if __name__ == "__main__":
    # Демонстраційний блок для CalendarProviderRepository.
    logger.info("--- Репозиторій для Довідника Постачальників Календарів (CalendarProviderRepository) ---")

    logger.info("Для тестування CalendarProviderRepository потрібна асинхронна сесія SQLAlchemy.")
    logger.info(f"Він успадковує методи від BaseDictionaryRepository для моделі {CalendarProvider.__name__}.")
    logger.info(f"  Очікує схему створення: {CalendarProviderCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {CalendarProviderUpdateSchema.__name__}")
