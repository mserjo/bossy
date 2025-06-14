# backend/app/src/repositories/dictionaries/status_repository.py
"""
Репозиторій для моделі "Статус" (Status).

Цей модуль визначає клас `StatusRepository`, який успадковує `BaseDictionaryRepository`
та надає специфічні методи для роботи з довідником статусів, якщо такі потрібні,
окрім стандартних CRUD операцій та пошуку за кодом/назвою.
"""

from typing import List, Optional # Optional може знадобитися для кастомних методів
from sqlalchemy import select # select може знадобитися для кастомних методів
from sqlalchemy.ext.asyncio import AsyncSession # Для type hinting у кастомних методах

# Абсолютний імпорт базового репозиторію для довідників
from backend.app.src.repositories.dictionaries.base_dict_repository import BaseDictionaryRepository

# Абсолютний імпорт моделі та схем для Статусів
from backend.app.src.models.dictionaries.statuses import Status
from backend.app.src.schemas.dictionaries.statuses import StatusCreateSchema, StatusUpdateSchema
from backend.app.src.config.logging import get_logger # Стандартизований імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)


class StatusRepository(BaseDictionaryRepository[Status, StatusCreateSchema, StatusUpdateSchema]):
    """
    Репозиторій для управління записами довідника "Статус".

    Успадковує всі базові методи CRUD та специфічні для довідників методи
    (наприклад, `get_by_code`, `get_by_name`) від `BaseDictionaryRepository`.
    Може бути розширений специфічними методами для роботи зі статусами, якщо це необхідно.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `Status`.
        """
        super().__init__(model=Status)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    # Приклад специфічного методу для цього репозиторію (якщо потрібно):
    # async def get_active_statuses(self, session: AsyncSession) -> List[Status]:
    #     """Повертає список усіх активних статусів."""
    #     logger.debug(f"Отримання активних статусів для моделі {self.model.__name__}")
    #     # TODO: Перевірити назву поля для стану (напр. 'state', 'is_active') та значення для активного стану.
    #     stmt = select(self.model).where(self.model.state == "active") # Припускаючи, що є поле 'state' та значення "active"
    #     try:
    #         result = await session.execute(stmt)
    #         return list(result.scalars().all())
    #     except Exception as e:
    #         logger.error(f"Помилка при отриманні активних статусів: {e}", exc_info=True)
    #         return []


if __name__ == "__main__":
    # Демонстраційний блок для StatusRepository.
    # Для реального тестування потрібна активна сесія БД та налаштована база даних.
    logger.info("--- Репозиторій для Довідника Статусів (StatusRepository) ---")

    # Концептуальна демонстрація створення екземпляра:
    # async def demo():
    #     # Потрібна асинхронна сесія (mock або реальна)
    #     mock_session = None # Замініть на реальну або макет сесії
    #     if mock_session:
    #         repo = StatusRepository(mock_session)
    #         logger.info(f"Екземпляр StatusRepository створено: {repo}")
    #         # Тут можна було б викликати методи, якби сесія була активною
    #         # Наприклад:
    #         # active_statuses = await repo.get_active_statuses()
    #         # logger.info(f"Активні статуси: {active_statuses}")
    # import asyncio
    # asyncio.run(demo())

    logger.info("Для тестування StatusRepository потрібна асинхронна сесія SQLAlchemy.")
    logger.info(f"Він успадковує методи від BaseDictionaryRepository для моделі {Status.__name__}.")
    # Показати, які схеми він очікує (для інформації)
    logger.info(f"  Очікує схему створення: {StatusCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {StatusUpdateSchema.__name__}")
