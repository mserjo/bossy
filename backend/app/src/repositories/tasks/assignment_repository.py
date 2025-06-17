# backend/app/src/repositories/tasks/assignment_repository.py
"""
Репозиторій для моделі "Призначення Завдання" (TaskAssignment).

Цей модуль визначає клас `TaskAssignmentRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з призначеннями завдань користувачам.
"""

from typing import List, Optional, Tuple, Any, Dict

from sqlalchemy import select, func # join видалено
from sqlalchemy.ext.asyncio import AsyncSession

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
from backend.app.src.config.logging import get_logger
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

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `TaskAssignment`.
        """
        super().__init__(model=TaskAssignment)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_by_task_and_user(
            self, session: AsyncSession, task_id: int, user_id: int
    ) -> Optional[TaskAssignment]:
        """
        Отримує запис про призначення за ID завдання та ID користувача.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            task_id (int): ID завдання.
            user_id (int): ID користувача.

        Returns:
            Optional[TaskAssignment]: Екземпляр моделі `TaskAssignment`, якщо знайдено, інакше None.
        """
        logger.debug(f"Отримання TaskAssignment для task_id {task_id}, user_id {user_id}")
        stmt = select(self.model).where(
            self.model.task_id == task_id,
            self.model.user_id == user_id
        )
        try:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Помилка при отриманні TaskAssignment для task_id {task_id}, user_id {user_id}: {e}",
                exc_info=True
            )
            return None

    async def get_assignments_for_task(
            self, session: AsyncSession, task_id: int, skip: int = 0, limit: int = 100
    ) -> Tuple[List[TaskAssignment], int]:
        """
        Отримує список призначень для вказаного завдання з пагінацією.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            task_id (int): ID завдання.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[TaskAssignment], int]: Кортеж зі списком призначень та їх загальною кількістю.
        """
        logger.debug(f"Отримання призначень для task_id: {task_id}, skip: {skip}, limit: {limit}")
        filters_dict: Dict[str, Any] = {"task_id": task_id}
        # Можна додати сортування, наприклад, за часом призначення
        # sort_by_field = "created_at"
        # sort_order_str = "desc"
        # Або жадібне завантаження користувача:
        # options = [selectinload(self.model.user)] # Потребує імпорту selectinload
        try:
            items = await super().get_multi(
                session=session, skip=skip, limit=limit, filters=filters_dict
                # sort_by=sort_by_field, sort_order=sort_order_str, options=options
            )
            total_count = await super().count(session=session, filters=filters_dict)
            logger.debug(f"Знайдено {total_count} призначень для task_id: {task_id}")
            return items, total_count
        except Exception as e:
            logger.error(f"Помилка при отриманні призначень для task_id {task_id}: {e}", exc_info=True)
            return [], 0

    async def get_assignments_for_user(
            self,
            session: AsyncSession,
            user_id: int,
            group_id: Optional[int] = None,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[TaskAssignment], int]:
        """
        Отримує список призначень для вказаного користувача, опціонально фільтруючи за групою, з пагінацією.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            user_id (int): ID користувача.
            group_id (Optional[int]): ID групи для фільтрації призначень (завдання в цій групі).
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[TaskAssignment], int]: Кортеж зі списком призначень та їх загальною кількістю.
        """
        logger.debug(
            f"Отримання призначень для user_id {user_id}, group_id: {group_id}, "
            f"skip: {skip}, limit: {limit}"
        )

        conditions = [self.model.user_id == user_id]

        base_query = select(self.model)
        count_base_query = select(func.count(self.model.task_id)).select_from(self.model)

        if group_id is not None:
            base_query = base_query.join(Task, Task.id == self.model.task_id)
            count_base_query = count_base_query.join(Task, Task.id == self.model.task_id)
            conditions.append(Task.group_id == group_id)

        stmt = base_query.where(*conditions).offset(skip).limit(limit).order_by(self.model.created_at.desc())
        count_stmt = count_base_query.where(*conditions)

        # options = [selectinload(self.model.task).selectinload(Task.group)] # Приклад складного жадібного завантаження
        try:
            total_result = await session.execute(count_stmt)
            total = total_result.scalar_one()

            items_result = await session.execute(stmt) #.options(*options if options else []))
            items = list(items_result.scalars().all())

            logger.debug(f"Знайдено {total} призначень для user_id {user_id} (фільтр group_id: {group_id})")
            return items, total
        except Exception as e:
            logger.error(
                f"Помилка при отриманні призначень для user_id {user_id}, group_id {group_id}: {e}",
                exc_info=True
            )
            return [], 0


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
