# backend/app/src/repositories/dictionaries/group_type_repository.py
"""
Репозиторій для моделі "Тип Групи" (GroupType).

Цей модуль визначає клас `GroupTypeRepository`, який успадковує `BaseDictionaryRepository`
та надає методи для роботи з довідником типів груп.
"""

from sqlalchemy.ext.asyncio import AsyncSession

# Абсолютний імпорт базового репозиторію для довідників
from backend.app.src.repositories.dictionaries.base_dict_repository import BaseDictionaryRepository

# Абсолютний імпорт моделі та схем для Типів Груп
from backend.app.src.models.dictionaries.group_types import GroupType
from backend.app.src.schemas.dictionaries.group_types import GroupTypeCreateSchema, GroupTypeUpdateSchema
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)


class GroupTypeRepository(BaseDictionaryRepository[GroupType, GroupTypeCreateSchema, GroupTypeUpdateSchema]):
    """
    Репозиторій для управління записами довідника "Тип Групи".

    Успадковує всі базові методи CRUD та специфічні для довідників методи
    від `BaseDictionaryRepository`.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `GroupType`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=GroupType)

    # Тут можна додати специфічні методи для GroupTypeRepository, якщо вони потрібні.


if __name__ == "__main__":
    # Демонстраційний блок для GroupTypeRepository.
    logger.info("--- Репозиторій для Довідника Типів Груп (GroupTypeRepository) ---")

    logger.info("Для тестування GroupTypeRepository потрібна асинхронна сесія SQLAlchemy.")
    logger.info(f"Він успадковує методи від BaseDictionaryRepository для моделі {GroupType.__name__}.")
    logger.info(f"  Очікує схему створення: {GroupTypeCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {GroupTypeUpdateSchema.__name__}")
