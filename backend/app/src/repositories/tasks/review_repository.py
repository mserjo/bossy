# backend/app/src/repositories/tasks/review_repository.py
"""
Репозиторій для моделі "Відгук на Завдання" (TaskReview).

Цей модуль визначає клас `TaskReviewRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з відгуками на завдання.
"""

from typing import List, Optional, Tuple, Any, Dict # Додано Dict

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.tasks.review import TaskReview
from backend.app.src.schemas.tasks.review import TaskReviewCreateSchema, TaskReviewUpdateSchema
from backend.app.src.config.logging import get_logger
# Отримання логера для цього модуля
logger = get_logger(__name__)


class TaskReviewRepository(BaseRepository[TaskReview, TaskReviewCreateSchema, TaskReviewUpdateSchema]):
    """
    Репозиторій для управління відгуками на завдання (`TaskReview`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи для отримання відгуків за парою завдання-користувач
    (оскільки користувач зазвичай залишає один відгук на завдання)
    та списку всіх відгуків для конкретного завдання.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `TaskReview`.
        """
        super().__init__(model=TaskReview)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_by_task_and_user(
            self, session: AsyncSession, task_id: int, user_id: int
    ) -> Optional[TaskReview]:
        """
        Отримує відгук, залишений конкретним користувачем на конкретне завдання.
        Передбачається, що користувач може залишити лише один відгук на одне завдання
        (забезпечується UniqueConstraint в моделі).

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            task_id (int): ID завдання.
            user_id (int): ID користувача, який залишив відгук.

        Returns:
            Optional[TaskReview]: Екземпляр моделі `TaskReview`, якщо знайдено, інакше None.
        """
        logger.debug(f"Отримання TaskReview для task_id {task_id}, user_id {user_id}")
        stmt = select(self.model).where(
            self.model.task_id == task_id,
            self.model.user_id == user_id
        )
        try:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Помилка при отриманні TaskReview для task_id {task_id}, user_id {user_id}: {e}",
                exc_info=True
            )
            return None

    async def get_reviews_for_task(
            self, session: AsyncSession, task_id: int, skip: int = 0, limit: int = 100
    ) -> Tuple[List[TaskReview], int]:
        """
        Отримує список всіх відгуків для вказаного завдання з пагінацією.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            task_id (int): ID завдання.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[TaskReview], int]: Кортеж зі списком відгуків та їх загальною кількістю.
        """
        logger.debug(f"Отримання відгуків для task_id: {task_id}, skip: {skip}, limit: {limit}")
        filters_dict: Dict[str, Any] = {"task_id": task_id}
        sort_by_field = "created_at"
        sort_order_str = "desc"  # Показувати новіші відгуки першими
        # options = [selectinload(self.model.user)] # Жадібне завантаження автора відгуку
        try:
            items = await super().get_multi(
                session=session, skip=skip, limit=limit, filters=filters_dict,
                sort_by=sort_by_field, sort_order=sort_order_str #, options=options
            )
            total_count = await super().count(session=session, filters=filters_dict)
            logger.debug(f"Знайдено {total_count} відгуків для task_id: {task_id}")
            return items, total_count
        except Exception as e:
            logger.error(f"Помилка при отриманні відгуків для task_id {task_id}: {e}", exc_info=True)
            return [], 0

    async def list_by_reviewer(
        self, session: AsyncSession, reviewer_user_id: int, skip: int = 0, limit: int = 100
    ) -> Tuple[List[TaskReview], int]:
        """
        Отримує список всіх відгуків, залишених конкретним користувачем.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            reviewer_user_id (int): ID користувача (рецензента).
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[TaskReview], int]: Кортеж зі списком відгуків та їх загальною кількістю.
        """
        logger.debug(f"Отримання відгуків рецензентом user_id: {reviewer_user_id}, skip: {skip}, limit: {limit}")
        filters_dict: Dict[str, Any] = {"reviewer_user_id": reviewer_user_id}
        sort_by_field = "created_at"
        sort_order_str = "desc"

        try:
            items = await super().get_multi(
                session=session, skip=skip, limit=limit, filters=filters_dict,
                sort_by=sort_by_field, sort_order=sort_order_str
            )
            total_count = await super().count(session=session, filters=filters_dict)
            logger.debug(f"Знайдено {total_count} відгуків рецензентом user_id: {reviewer_user_id}")
            return items, total_count
        except Exception as e:
            logger.error(f"Помилка при отриманні відгуків рецензентом user_id {reviewer_user_id}: {e}", exc_info=True)
            return [], 0


if __name__ == "__main__":
    # Демонстраційний блок для TaskReviewRepository.
    logger.info("--- Репозиторій Відгуків на Завдання (TaskReviewRepository) ---")

    logger.info("Для тестування TaskReviewRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    logger.info(f"Він успадковує методи від BaseRepository для моделі {TaskReview.__name__}.")
    logger.info(f"  Очікує схему створення: {TaskReviewCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {TaskReviewUpdateSchema.__name__}")

    logger.info("\nСпецифічні методи:")
    logger.info("  - get_by_task_and_user(task_id: int, user_id: int) -> Optional[TaskReview]")
    logger.info("  - get_reviews_for_task(task_id: int, skip: int = 0, limit: int = 100)")
    logger.info("  - list_by_reviewer(reviewer_user_id: int, skip: int = 0, limit: int = 100)")

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
