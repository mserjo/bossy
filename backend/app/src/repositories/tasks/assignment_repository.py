# backend/app/src/repositories/tasks/assignment_repository.py
"""
Репозиторій для моделі "Призначення Завдання" (TaskAssignment).

Цей модуль визначає клас `TaskAssignmentRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з призначеннями завдань користувачам.
"""

from typing import List, Optional, Tuple, Any

from sqlalchemy import select, func, join
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import selectinload

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
from backend.app.src.config.logging import get_logger  # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

# Абсолютний імпорт моделей та схем
from backend.app.src.models.tasks.task import Task  # Для join в get_assignments_for_user_in_group
from backend.app.src.models.tasks.assignment import TaskAssignment
from backend.app.src.schemas.tasks.assignment import (
    TaskAssignmentCreateSchema,
    TaskAssignmentUpdateSchema  # Хоча оновлення призначень може бути обмеженим
)


class TaskAssignmentRepository(BaseRepository[TaskAssignment, TaskAssignmentCreateSchema, TaskAssignmentUpdateSchema]):
    """
    Репозиторій для управління записами призначень завдань (`TaskAssignment`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи для отримання призначень за парою завдання-користувач,
    а також списків призначень для конкретного завдання або користувача.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `TaskAssignment`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=TaskAssignment)

    async def get_by_task_and_user(self, task_id: int, user_id: int) -> Optional[TaskAssignment]:
        """
        Отримує запис про призначення за ID завдання та ID користувача.

        Args:
            task_id (int): ID завдання.
            user_id (int): ID користувача.

        Returns:
            Optional[TaskAssignment]: Екземпляр моделі `TaskAssignment`, якщо знайдено, інакше None.
        """
        stmt = select(self.model).where(
            self.model.task_id == task_id,
            self.model.user_id == user_id
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_assignments_for_task(self, task_id: int, skip: int = 0, limit: int = 100) -> Tuple[
        List[TaskAssignment], int]:
        """
        Отримує список призначень для вказаного завдання з пагінацією.

        Args:
            task_id (int): ID завдання.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[TaskAssignment], int]: Кортеж зі списком призначень та їх загальною кількістю.
        """
        filters = [self.model.task_id == task_id]
        # order_by = [self.model.created_at.desc()] # Можна сортувати за часом призначення
        # options = [selectinload(self.model.user)] # Жадібне завантаження користувача
        return await self.get_multi(skip=skip, limit=limit, filters=filters)  # , order_by=order_by, options=options)

    async def get_assignments_for_user(
            self,
            user_id: int,
            group_id: Optional[int] = None,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[TaskAssignment], int]:
        """
        Отримує список призначень для вказаного користувача, опціонально фільтруючи за групою, з пагінацією.

        Args:
            user_id (int): ID користувача.
            group_id (Optional[int]): ID групи для фільтрації призначень (завдання в цій групі).
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[TaskAssignment], int]: Кортеж зі списком призначень та їх загальною кількістю.
        """
        filters = [self.model.user_id == user_id]

        stmt = select(self.model)
        count_stmt = select(func.count(self.model.task_id)).select_from(
            self.model)  # Рахуємо по task_id, оскільки це частина PK

        if group_id is not None:
            # Приєднуємо таблицю Task для фільтрації за Task.group_id
            stmt = stmt.join(Task, Task.id == self.model.task_id)
            count_stmt = count_stmt.join(Task, Task.id == self.model.task_id)
            filters.append(Task.group_id == group_id)

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        total = (await self.db_session.execute(count_stmt)).scalar_one()

        stmt = stmt.offset(skip).limit(limit).order_by(self.model.created_at.desc())
        # options = [selectinload(self.model.task).selectinload(Task.group)] # Приклад складного жадібного завантаження

        items_result = await self.db_session.execute(stmt)
        items = list(items_result.scalars().all())

        return items, total


if __name__ == "__main__":
    # Демонстраційний блок для TaskAssignmentRepository.
    logger.info("--- Репозиторій Призначень Завдань (TaskAssignmentRepository) ---")

    logger.info("Для тестування TaskAssignmentRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    logger.info(f"Він успадковує методи від BaseRepository для моделі {TaskAssignment.__name__}.")
    # TaskAssignmentUpdateSchema може бути дуже простою або не використовуватися, якщо оновлюється лише статус через сервіс
    logger.info(f"  Очікує схему створення: {TaskAssignmentCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {TaskAssignmentUpdateSchema.__name__}")

    logger.info("\nСпецифічні методи:")
    logger.info("  - get_by_task_and_user(task_id: int, user_id: int)")
    logger.info("  - get_assignments_for_task(task_id: int, skip: int = 0, limit: int = 100)")
    logger.info("  - get_assignments_for_user(user_id: int, group_id: Optional[int] = None, skip: int = 0, limit: int = 100)")

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
