# backend/app/src/repositories/tasks/completion_repository.py
"""
Репозиторій для моделі "Виконання Завдання" (TaskCompletion).

Цей модуль визначає клас `TaskCompletionRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з записами про виконання завдань.
"""

from typing import List, Optional, Tuple, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import selectinload

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.tasks.completion import TaskCompletion
from backend.app.src.schemas.tasks.completion import TaskCompletionCreateSchema, TaskCompletionUpdateSchema


# from backend.app.src.config.logging import get_logger # Якщо потрібне логування

# logger = get_logger(__name__)

class TaskCompletionRepository(BaseRepository[TaskCompletion, TaskCompletionCreateSchema, TaskCompletionUpdateSchema]):
    """
    Репозиторій для управління записами про виконання завдань (`TaskCompletion`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи для отримання виконань за парою завдання-користувач
    та списку всіх виконань для конкретного завдання.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `TaskCompletion`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=TaskCompletion)

    async def get_by_task_and_user(self, task_id: int, user_id: int) -> Optional[TaskCompletion]:
        """
        Отримує останній запис про виконання завдання конкретним користувачем.
        Якщо завдання може бути виконано кілька разів (наприклад, рекурентне),
        цей метод поверне останню за часом спробу/виконання.

        Args:
            task_id (int): ID завдання.
            user_id (int): ID користувача.

        Returns:
            Optional[TaskCompletion]: Екземпляр моделі `TaskCompletion`, якщо знайдено, інакше None.
        """
        stmt = (
            select(self.model)
            .where(self.model.task_id == task_id, self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())  # Останнє виконання/спроба першим
        )
        result = await self.db_session.execute(stmt)
        return result.scalars().first()  # Повертає перший результат або None

    async def get_all_by_task_and_user(self, task_id: int, user_id: int, skip: int = 0, limit: int = 100) -> Tuple[
        List[TaskCompletion], int]:
        """
        Отримує всі записи про виконання завдання конкретним користувачем з пагінацією.
        Корисно для рекурентних завдань.

        Args:
            task_id (int): ID завдання.
            user_id (int): ID користувача.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[TaskCompletion], int]: Кортеж зі списком виконань та їх загальною кількістю.
        """
        filters = [
            self.model.task_id == task_id,
            self.model.user_id == user_id
        ]
        order_by = [self.model.created_at.desc()]
        return await self.get_multi(skip=skip, limit=limit, filters=filters, order_by=order_by)

    async def get_completions_for_task(self, task_id: int, skip: int = 0, limit: int = 100) -> Tuple[
        List[TaskCompletion], int]:
        """
        Отримує список всіх виконань для вказаного завдання з пагінацією.

        Args:
            task_id (int): ID завдання.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[TaskCompletion], int]: Кортеж зі списком виконань та їх загальною кількістю.
        """
        filters = [self.model.task_id == task_id]
        order_by = [self.model.created_at.desc()]
        # options = [selectinload(self.model.user), selectinload(self.model.verifier)] # Приклад жадібного завантаження
        return await self.get_multi(skip=skip, limit=limit, filters=filters, order_by=order_by)  # , options=options)


if __name__ == "__main__":
    # Демонстраційний блок для TaskCompletionRepository.
    print("--- Репозиторій Виконань Завдань (TaskCompletionRepository) ---")

    print("Для тестування TaskCompletionRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    print(f"Він успадковує методи від BaseRepository для моделі {TaskCompletion.__name__}.")
    print(f"  Очікує схему створення: {TaskCompletionCreateSchema.__name__}")
    print(f"  Очікує схему оновлення: {TaskCompletionUpdateSchema.__name__}")

    print("\nСпецифічні методи:")
    print("  - get_by_task_and_user(task_id: int, user_id: int) -> Optional[TaskCompletion] (повертає останнє)")
    print(
        "  - get_all_by_task_and_user(task_id: int, user_id: int, skip: int = 0, limit: int = 100) -> Tuple[List[TaskCompletion], int]")
    print("  - get_completions_for_task(task_id: int, skip: int = 0, limit: int = 100)")

    print("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
