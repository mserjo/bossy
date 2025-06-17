# backend/app/src/repositories/dictionaries/calendar_provider_repository.py
"""
Репозиторій для моделі "Постачальник Календарів" (CalendarProvider).

Цей модуль визначає клас `CalendarProviderRepository`, який успадковує `BaseDictionaryRepository`
та надає методи для роботи з довідником постачальників календарів.
"""

# Абсолютний імпорт базового репозиторію для довідників
from backend.app.src.repositories.dictionaries.base_dict_repository import BaseDictionaryRepository

# Абсолютний імпорт моделі та схем для Постачальників Календарів
from backend.app.src.models.dictionaries.calendars import CalendarProvider
from backend.app.src.schemas.dictionaries.calendars import CalendarProviderCreateSchema, CalendarProviderUpdateSchema
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


class CalendarProviderRepository(
    BaseDictionaryRepository[CalendarProvider, CalendarProviderCreateSchema, CalendarProviderUpdateSchema]):
    """
    Репозиторій для управління записами довідника "Постачальник Календарів".

    Успадковує всі базові методи CRUD та специфічні для довідників методи
    від `BaseDictionaryRepository`.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `CalendarProvider`.
        """
        super().__init__(model=CalendarProvider)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    # Тут можна додати специфічні методи для CalendarProviderRepository, якщо вони потрібні.
    # Наприклад:
    # async def get_provider_by_integration_type(self, session: AsyncSession, integration_type: str) -> Optional[CalendarProvider]:
    #     # логіка методу...
    #     pass


if __name__ == "__main__":
    # Демонстраційний блок для CalendarProviderRepository.
    logger.info("--- Репозиторій для Довідника Постачальників Календарів (CalendarProviderRepository) ---")

    logger.info("Для тестування CalendarProviderRepository потрібна асинхронна сесія SQLAlchemy.")
    logger.info(f"Він успадковує методи від BaseDictionaryRepository для моделі {CalendarProvider.__name__}.")
    logger.info(f"  Очікує схему створення: {CalendarProviderCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {CalendarProviderUpdateSchema.__name__}")
