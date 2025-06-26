# backend/app/src/repositories/tasks/review.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `TaskReviewModel`.
Надає методи для управління відгуками та рейтингами на завдання/події.
"""

from typing import Optional, List
import uuid
from sqlalchemy import select, and_ # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload # type: ignore

from backend.app.src.models.tasks.review import TaskReviewModel
from backend.app.src.schemas.tasks.review import TaskReviewCreateSchema, TaskReviewUpdateSchema
from backend.app.src.repositories.base import BaseRepository

class TaskReviewRepository(BaseRepository[TaskReviewModel, TaskReviewCreateSchema, TaskReviewUpdateSchema]):
    """
    Репозиторій для роботи з моделлю відгуків на завдання (`TaskReviewModel`).
    """

    async def get_reviews_for_task(
        self, db: AsyncSession, *, task_id: uuid.UUID,
        skip: int = 0, limit: int = 100
    ) -> List[TaskReviewModel]:
        """
        Отримує список всіх відгуків для вказаного завдання/події.
        """
        statement = select(self.model).where(self.model.task_id == task_id).options(
            selectinload(self.model.user) # Завантажуємо інформацію про автора відгуку
            # Якщо буде поле status_id для модерації відгуків:
            # selectinload(self.model.status)
        ).order_by(self.model.created_at.desc()).offset(skip).limit(limit) # type: ignore
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def get_review_by_task_and_user(
        self, db: AsyncSession, *, task_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[TaskReviewModel]:
        """
        Отримує відгук, залишений конкретним користувачем для конкретного завдання.
        Корисно для перевірки, чи користувач вже залишав відгук (якщо дозволено лише один).
        """
        statement = select(self.model).where(
            and_(self.model.task_id == task_id, self.model.user_id == user_id)
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    # `create` успадкований. `TaskReviewCreateSchema` має містити `rating` та/або `comment`.
    # `task_id` та `user_id` мають встановлюватися сервісом.
    # Потрібен кастомний метод `create_review`.
    async def create_review(
        self, db: AsyncSession, *, obj_in: TaskReviewCreateSchema,
        task_id: uuid.UUID, user_id: uuid.UUID
    ) -> TaskReviewModel:
        obj_in_data = obj_in.model_dump(exclude_unset=True)
        db_obj = self.model(task_id=task_id, user_id=user_id, **obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # `update` успадкований. `TaskReviewUpdateSchema` для оновлення `rating` та/або `comment`.
    # `delete` успадкований.

task_review_repository = TaskReviewRepository(TaskReviewModel)

# TODO: Переконатися, що `TaskReviewCreateSchema` та `TaskReviewUpdateSchema` коректно визначені.
#       `TaskReviewCreateSchema` не має містити `task_id`, `user_id`.
#
# TODO: Якщо буде реалізована модерація відгуків (`status_id` в `TaskReviewModel`),
#       додати методи для отримання відгуків за статусом або оновлення статусу.
#
# Все виглядає добре. Надано основні методи для роботи з відгуками.
# Унікальне обмеження `UniqueConstraint('task_id', 'user_id')` в моделі
# забезпечує, що користувач може залишити лише один відгук на одне завдання.
# Метод `get_review_by_task_and_user` може використовуватися для перевірки цього перед створенням.
