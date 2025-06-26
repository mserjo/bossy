# backend/app/src/repositories/tasks/completion.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `TaskCompletionModel`.
Надає методи для управління записами про виконання завдань.
"""

from typing import Optional, List, Union, Dict, Any
import uuid
from datetime import datetime
from sqlalchemy import select, and_ # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload # type: ignore

from backend.app.src.models.tasks.completion import TaskCompletionModel
from backend.app.src.schemas.tasks.completion import (
    TaskCompletionCreateSchema, # Це може бути непрямою схемою, поля збираються з різних етапів
    TaskCompletionUpdateSchema, # Для оновлення статусу, результатів перевірки
    TaskCompletionStartSchema, TaskCompletionSubmitSchema, TaskCompletionReviewSchema # Схеми для дій
)
from backend.app.src.repositories.base import BaseRepository

# Для TaskCompletionModel, CreateSchema та UpdateSchema можуть бути менш прямими,
# оскільки запис про виконання проходить через кілька станів/дій.
# Можливо, BaseRepository буде використовуватися лише для get/get_multi,
# а створення/оновлення - через специфічні методи.
# Або ж, мати загальну схему TaskCompletionDBInputSchema для створення/оновлення в БД.
# Поки що використовую TaskCompletionUpdateSchema як базову для оновлення.
# Для створення, BaseRepository.create не буде використовуватися напряму.

class TaskCompletionRepository(BaseRepository[TaskCompletionModel, PydanticBaseModel, TaskCompletionUpdateSchema]): # type: ignore
    """
    Репозиторій для роботи з моделлю виконань завдань (`TaskCompletionModel`).
    """

    async def get_by_task_and_user(
        self, db: AsyncSession, *, task_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[TaskCompletionModel]:
        """
        Отримує запис про виконання завдання конкретним користувачем.
        Якщо завдання може бути виконане кілька разів, цей метод може потребувати
        додаткових фільтрів (наприклад, за статусом "в роботі" або "на перевірці").
        Повертає останній запис, якщо їх декілька (що не мало б бути для не-повторюваних завдань).
        """
        statement = select(self.model).where(
            self.model.task_id == task_id,
            self.model.user_id == user_id
        ).order_by(self.model.created_at.desc()) # type: ignore
        result = await db.execute(statement)
        return result.scalars().first()

    async def get_by_task_and_team(
        self, db: AsyncSession, *, task_id: uuid.UUID, team_id: uuid.UUID
    ) -> Optional[TaskCompletionModel]:
        """Отримує запис про виконання завдання конкретною командою."""
        statement = select(self.model).where(
            self.model.task_id == task_id,
            self.model.team_id == team_id
        ).order_by(self.model.created_at.desc()) # type: ignore
        result = await db.execute(statement)
        return result.scalars().first()

    async def get_completions_for_task(
        self, db: AsyncSession, *, task_id: uuid.UUID,
        skip: int = 0, limit: int = 100
    ) -> List[TaskCompletionModel]:
        """Отримує всі записи про виконання для конкретного завдання."""
        statement = select(self.model).where(self.model.task_id == task_id).options(
            selectinload(self.model.user),
            selectinload(self.model.team),
            selectinload(self.model.status),
            selectinload(self.model.reviewer)
        ).order_by(self.model.created_at.desc()).offset(skip).limit(limit) # type: ignore
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def create_completion_entry(
        self, db: AsyncSession, *,
        task_id: uuid.UUID,
        status_id: uuid.UUID, # Початковий статус (напр., "в роботі")
        user_id: Optional[uuid.UUID] = None,
        team_id: Optional[uuid.UUID] = None,
        start_data: Optional[TaskCompletionStartSchema] = None # Дані з схеми початку виконання
    ) -> TaskCompletionModel:
        """Створює початковий запис про виконання завдання (наприклад, при взяттІ в роботу)."""
        if not user_id and not team_id:
            raise ValueError("Необхідно вказати user_id або team_id для виконання завдання.")
        if user_id and team_id:
            raise ValueError("Завдання не може бути виконане одночасно користувачем і командою в одному записі TaskCompletion.")

        create_data: Dict[str, Any] = {
            "task_id": task_id,
            "user_id": user_id,
            "team_id": team_id,
            "status_id": status_id,
        }
        if start_data:
            create_data["started_at"] = start_data.started_at
            # Можна додати інші поля з start_data, якщо вони є
        else:
            create_data["started_at"] = datetime.utcnow()

        db_obj = self.model(**create_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # Метод `update` успадковується і може використовуватися для оновлення статусу,
    # додавання результатів перевірки тощо, використовуючи `TaskCompletionUpdateSchema`.
    # Наприклад, при поданні на перевірку або при перевірці адміном.
    # Сервіс буде готувати `TaskCompletionUpdateSchema` з відповідними даними.

task_completion_repository = TaskCompletionRepository(TaskCompletionModel)

# TODO: Переконатися, що `TaskCompletionUpdateSchema` містить всі поля,
#       які можуть оновлюватися на різних етапах (подання на перевірку, результати перевірки).
#       Можливо, знадобляться більш специфічні схеми оновлення для кожного етапу,
#       або сервіс буде формувати `TaskCompletionUpdateSchema` вибірково.
#
# TODO: Розглянути логіку для повторюваних завдань: чи створюється новий запис `TaskCompletionModel`
#       для кожного повторення, чи оновлюється існуючий.
#       Поточна структура дозволяє створювати нові записи.
#
# Все виглядає добре. Надано методи для отримання та створення записів про виконання.
# Оновлення буде відбуватися через успадкований метод `update`.
