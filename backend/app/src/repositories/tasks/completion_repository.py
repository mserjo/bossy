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
from backend.app.src.config import logger  # Використання спільного логера


class TaskCompletionRepository(BaseRepository[TaskCompletion, TaskCompletionCreateSchema, TaskCompletionUpdateSchema]):
    """
    Репозиторій для управління записами про виконання завдань (`TaskCompletion`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи для отримання виконань за парою завдання-користувач
    та списку всіх виконань для конкретного завдання.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `TaskCompletion`.
        """
        super().__init__(model=TaskCompletion)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_by_task_and_user(
            self, session: AsyncSession, task_id: int, user_id: int
    ) -> Optional[TaskCompletion]:
        """
        Отримує останній запис про виконання завдання конкретним користувачем.
        Якщо завдання може бути виконано кілька разів (наприклад, рекурентне),
        цей метод поверне останню за часом спробу/виконання.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            task_id (int): ID завдання.
            user_id (int): ID користувача.

        Returns:
            Optional[TaskCompletion]: Екземпляр моделі `TaskCompletion`, якщо знайдено, інакше None.
        """
        logger.debug(f"Отримання останнього виконання для task_id {task_id}, user_id {user_id}")
        stmt = (
            select(self.model)
            .where(self.model.task_id == task_id, self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
        )
        try:
            result = await session.execute(stmt)
            return result.scalars().first()
        except Exception as e:
            logger.error(
                f"Помилка при отриманні виконання для task_id {task_id}, user_id {user_id}: {e}",
                exc_info=True
            )
            return None

    async def get_all_by_task_and_user(
            self, session: AsyncSession, task_id: int, user_id: int, skip: int = 0, limit: int = 100
    ) -> Tuple[List[TaskCompletion], int]:
        """
        Отримує всі записи про виконання завдання конкретним користувачем з пагінацією.
        Корисно для рекурентних завдань.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            task_id (int): ID завдання.
            user_id (int): ID користувача.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[TaskCompletion], int]: Кортеж зі списком виконань та їх загальною кількістю.
        """
        logger.debug(
            f"Отримання всіх виконань для task_id {task_id}, user_id {user_id}, "
            f"skip: {skip}, limit: {limit}"
        )
        filters_dict: Dict[str, Any] = {
            "task_id": task_id,
            "user_id": user_id
        }
        sort_by_field = "created_at"
        sort_order_str = "desc"

        try:
            items = await super().get_multi(
                session=session, skip=skip, limit=limit, filters=filters_dict,
                sort_by=sort_by_field, sort_order=sort_order_str
            )
            total_count = await super().count(session=session, filters=filters_dict)
            logger.debug(f"Знайдено {total_count} виконань для task_id {task_id}, user_id {user_id}")
            return items, total_count
        except Exception as e:
            logger.error(
                f"Помилка при отриманні всіх виконань для task_id {task_id}, user_id {user_id}: {e}",
                exc_info=True
            )
            return [], 0

    async def get_completions_for_task(
            self, session: AsyncSession, task_id: int, skip: int = 0, limit: int = 100
    ) -> Tuple[List[TaskCompletion], int]:
        """
        Отримує список всіх виконань для вказаного завдання з пагінацією.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            task_id (int): ID завдання.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[TaskCompletion], int]: Кортеж зі списком виконань та їх загальною кількістю.
        """
        logger.debug(f"Отримання виконань для task_id: {task_id}, skip: {skip}, limit: {limit}")
        filters_dict: Dict[str, Any] = {"task_id": task_id}
        sort_by_field = "created_at"
        sort_order_str = "desc"
        # options = [selectinload(self.model.user), selectinload(self.model.verifier)] # Приклад жадібного завантаження
        try:
            items = await super().get_multi(
                session=session, skip=skip, limit=limit, filters=filters_dict,
                sort_by=sort_by_field, sort_order=sort_order_str #, options=options
            )
            total_count = await super().count(session=session, filters=filters_dict)
            logger.debug(f"Знайдено {total_count} виконань для task_id: {task_id}")
            return items, total_count
        except Exception as e:
            logger.error(f"Помилка при отриманні виконань для task_id {task_id}: {e}", exc_info=True)
            return [], 0


if __name__ == "__main__":
    # Демонстраційний блок для TaskCompletionRepository.
    logger.info("--- Репозиторій Виконань Завдань (TaskCompletionRepository) ---")

    logger.info("Для тестування TaskCompletionRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    logger.info(f"Він успадковує методи від BaseRepository для моделі {TaskCompletion.__name__}.")
    logger.info(f"  Очікує схему створення: {TaskCompletionCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {TaskCompletionUpdateSchema.__name__}")

    logger.info("\nСпецифічні методи:")
    logger.info("  - get_by_task_and_user(task_id: int, user_id: int) -> Optional[TaskCompletion] (повертає останнє)")
    logger.info(
        "  - get_all_by_task_and_user(task_id: int, user_id: int, skip: int = 0, limit: int = 100) -> Tuple[List[TaskCompletion], int]")
    logger.info("  - get_completions_for_task(task_id: int, skip: int = 0, limit: int = 100)")

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
