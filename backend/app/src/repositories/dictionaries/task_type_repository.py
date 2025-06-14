# backend/app/src/repositories/dictionaries/task_type_repository.py
"""
Репозиторій для моделі "Тип Завдання" (TaskType).

Цей модуль визначає клас `TaskTypeRepository`, який успадковує `BaseDictionaryRepository`
та надає методи для роботи з довідником типів завдань.
"""

# Абсолютний імпорт базового репозиторію для довідників
from backend.app.src.repositories.dictionaries.base_dict_repository import BaseDictionaryRepository

# Абсолютний імпорт моделі та схем для Типів Завдань
from backend.app.src.models.dictionaries.task_types import TaskType
from backend.app.src.schemas.dictionaries.task_types import TaskTypeCreateSchema, TaskTypeUpdateSchema
from backend.app.src.config.logging import get_logger # Стандартизований імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)


class TaskTypeRepository(BaseDictionaryRepository[TaskType, TaskTypeCreateSchema, TaskTypeUpdateSchema]):
    """
    Репозиторій для управління записами довідника "Тип Завдання".

    Успадковує всі базові методи CRUD та специфічні для довідників методи
    від `BaseDictionaryRepository`.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `TaskType`.
        """
        super().__init__(model=TaskType)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    # Тут можна додати специфічні методи для TaskTypeRepository, якщо вони потрібні.
    # Наприклад:
    # async def get_task_types_by_category(self, session: AsyncSession, category: str) -> List[TaskType]:
    #     # логіка методу...
    #     pass


if __name__ == "__main__":
    # Демонстраційний блок для TaskTypeRepository.
    logger.info("--- Репозиторій для Довідника Типів Завдань (TaskTypeRepository) ---")

    logger.info("Для тестування TaskTypeRepository потрібна асинхронна сесія SQLAlchemy.")
    logger.info(f"Він успадковує методи від BaseDictionaryRepository для моделі {TaskType.__name__}.")
    logger.info(f"  Очікує схему створення: {TaskTypeCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {TaskTypeUpdateSchema.__name__}")
