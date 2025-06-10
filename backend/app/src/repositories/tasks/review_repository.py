# /backend/app/src/repositories/tasks/review_repository.py
"""
Репозиторій для моделі "Відгук на Завдання" (TaskReview).

Цей модуль визначає клас `TaskReviewRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з відгуками на завдання.
"""

from typing import List, Optional, Tuple, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import selectinload

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.tasks.review import TaskReview
from backend.app.src.schemas.tasks.review import TaskReviewCreateSchema, TaskReviewUpdateSchema


# from backend.app.src.config.logging import get_logger # Якщо потрібне логування

# logger = get_logger(__name__)

class TaskReviewRepository(BaseRepository[TaskReview, TaskReviewCreateSchema, TaskReviewUpdateSchema]):
    """
    Репозиторій для управління відгуками на завдання (`TaskReview`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи для отримання відгуків за парою завдання-користувач
    (оскільки користувач зазвичай залишає один відгук на завдання)
    та списку всіх відгуків для конкретного завдання.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `TaskReview`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=TaskReview)

    async def get_by_task_and_user(self, task_id: int, user_id: int) -> Optional[TaskReview]:
        """
        Отримує відгук, залишений конкретним користувачем на конкретне завдання.
        Передбачається, що користувач може залишити лише один відгук на одне завдання
        (забезпечується UniqueConstraint в моделі).

        Args:
            task_id (int): ID завдання.
            user_id (int): ID користувача, який залишив відгук.

        Returns:
            Optional[TaskReview]: Екземпляр моделі `TaskReview`, якщо знайдено, інакше None.
        """
        stmt = select(self.model).where(
            self.model.task_id == task_id,
            self.model.user_id == user_id
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_reviews_for_task(self, task_id: int, skip: int = 0, limit: int = 100) -> Tuple[List[TaskReview], int]:
        """
        Отримує список всіх відгуків для вказаного завдання з пагінацією.

        Args:
            task_id (int): ID завдання.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[TaskReview], int]: Кортеж зі списком відгуків та їх загальною кількістю.
        """
        filters = [self.model.task_id == task_id]
        order_by = [self.model.created_at.desc()]  # Показувати новіші відгуки першими
        # options = [selectinload(self.model.user)] # Жадібне завантаження автора відгуку
        return await self.get_multi(skip=skip, limit=limit, filters=filters, order_by=order_by)  # , options=options)


if __name__ == "__main__":
    # Демонстраційний блок для TaskReviewRepository.
    print("--- Репозиторій Відгуків на Завдання (TaskReviewRepository) ---")

    print("Для тестування TaskReviewRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    print(f"Він успадковує методи від BaseRepository для моделі {TaskReview.__name__}.")
    print(f"  Очікує схему створення: {TaskReviewCreateSchema.__name__}")
    print(f"  Очікує схему оновлення: {TaskReviewUpdateSchema.__name__}")

    print("\nСпецифічні методи:")
    print("  - get_by_task_and_user(task_id: int, user_id: int) -> Optional[TaskReview]")
    print("  - get_reviews_for_task(task_id: int, skip: int = 0, limit: int = 100)")

    print("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
