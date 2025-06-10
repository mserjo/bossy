# backend/app/src/repositories/dictionaries/task_type_repository.py
"""
Репозиторій для моделі "Тип Завдання" (TaskType).

Цей модуль визначає клас `TaskTypeRepository`, який успадковує `BaseDictionaryRepository`
та надає методи для роботи з довідником типів завдань.
"""

from sqlalchemy.ext.asyncio import AsyncSession

# Абсолютний імпорт базового репозиторію для довідників
from backend.app.src.repositories.dictionaries.base_dict_repository import BaseDictionaryRepository

# Абсолютний імпорт моделі та схем для Типів Завдань
from backend.app.src.models.dictionaries.task_types import TaskType
from backend.app.src.schemas.dictionaries.task_types import TaskTypeCreateSchema, TaskTypeUpdateSchema


class TaskTypeRepository(BaseDictionaryRepository[TaskType, TaskTypeCreateSchema, TaskTypeUpdateSchema]):
    """
    Репозиторій для управління записами довідника "Тип Завдання".

    Успадковує всі базові методи CRUD та специфічні для довідників методи
    від `BaseDictionaryRepository`.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `TaskType`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=TaskType)

    # Тут можна додати специфічні методи для TaskTypeRepository, якщо вони потрібні.


if __name__ == "__main__":
    # Демонстраційний блок для TaskTypeRepository.
    print("--- Репозиторій для Довідника Типів Завдань (TaskTypeRepository) ---")

    print("Для тестування TaskTypeRepository потрібна асинхронна сесія SQLAlchemy.")
    print(f"Він успадковує методи від BaseDictionaryRepository для моделі {TaskType.__name__}.")
    print(f"  Очікує схему створення: {TaskTypeCreateSchema.__name__}")
    print(f"  Очікує схему оновлення: {TaskTypeUpdateSchema.__name__}")
