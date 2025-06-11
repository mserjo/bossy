# backend/app/src/repositories/dictionaries/bonus_type_repository.py
"""
Репозиторій для моделі "Тип Бонусу" (BonusType).

Цей модуль визначає клас `BonusTypeRepository`, який успадковує `BaseDictionaryRepository`
та надає методи для роботи з довідником типів бонусів.
"""

from sqlalchemy.ext.asyncio import AsyncSession

# Абсолютний імпорт базового репозиторію для довідників
from backend.app.src.repositories.dictionaries.base_dict_repository import BaseDictionaryRepository

# Абсолютний імпорт моделі та схем для Типів Бонусів
from backend.app.src.models.dictionaries.bonus_types import BonusType
from backend.app.src.schemas.dictionaries.bonus_types import BonusTypeCreateSchema, BonusTypeUpdateSchema
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)


class BonusTypeRepository(BaseDictionaryRepository[BonusType, BonusTypeCreateSchema, BonusTypeUpdateSchema]):
    """
    Репозиторій для управління записами довідника "Тип Бонусу".

    Успадковує всі базові методи CRUD та специфічні для довідників методи
    від `BaseDictionaryRepository`.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `BonusType`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=BonusType)

    # Тут можна додати специфічні методи для BonusTypeRepository, якщо вони потрібні.


if __name__ == "__main__":
    # Демонстраційний блок для BonusTypeRepository.
    logger.info("--- Репозиторій для Довідника Типів Бонусів (BonusTypeRepository) ---")

    logger.info("Для тестування BonusTypeRepository потрібна асинхронна сесія SQLAlchemy.")
    logger.info(f"Він успадковує методи від BaseDictionaryRepository для моделі {BonusType.__name__}.")
    logger.info(f"  Очікує схему створення: {BonusTypeCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {BonusTypeUpdateSchema.__name__}")
