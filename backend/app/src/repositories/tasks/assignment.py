# backend/app/src/repositories/tasks/assignment.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `TaskAssignmentModel`.
Надає методи для управління призначеннями завдань користувачам або командам.
"""

from typing import Optional, List, Union, Dict, Any
import uuid
from sqlalchemy import select, and_ # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload # type: ignore

from backend.app.src.models.tasks.assignment import TaskAssignmentModel
from backend.app.src.schemas.tasks.assignment import TaskAssignmentCreateSchema, TaskAssignmentUpdateSchema
from backend.app.src.repositories.base import BaseRepository

class TaskAssignmentRepository(BaseRepository[TaskAssignmentModel, TaskAssignmentCreateSchema, TaskAssignmentUpdateSchema]):
    """
    Репозиторій для роботи з моделлю призначень завдань (`TaskAssignmentModel`).
    """

    async def get_by_task_and_user(
        self, db: AsyncSession, *, task_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[TaskAssignmentModel]:
        """Отримує призначення завдання для конкретного користувача."""
        statement = select(self.model).where(
            self.model.task_id == task_id,
            self.model.user_id == user_id
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_task_and_team(
        self, db: AsyncSession, *, task_id: uuid.UUID, team_id: uuid.UUID
    ) -> Optional[TaskAssignmentModel]:
        """Отримує призначення завдання для конкретної команди."""
        statement = select(self.model).where(
            self.model.task_id == task_id,
            self.model.team_id == team_id
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_assignments_for_task(
        self, db: AsyncSession, *, task_id: uuid.UUID,
        skip: int = 0, limit: int = 100
    ) -> List[TaskAssignmentModel]:
        """Отримує всі призначення для конкретного завдання."""
        statement = select(self.model).where(self.model.task_id == task_id).options(
            selectinload(self.model.user),
            selectinload(self.model.team),
            selectinload(self.model.assigner),
            selectinload(self.model.status)
        ).order_by(self.model.created_at.desc()).offset(skip).limit(limit) # type: ignore
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def get_assignments_for_user(
        self, db: AsyncSession, *, user_id: uuid.UUID,
        skip: int = 0, limit: int = 100
    ) -> List[TaskAssignmentModel]:
        """Отримує всі завдання, призначені конкретному користувачеві."""
        statement = select(self.model).where(self.model.user_id == user_id).options(
            selectinload(self.model.task).selectinload(TaskModel.task_type), # type: ignore # Завантажуємо завдання та його тип
            selectinload(self.model.status)
        ).order_by(self.model.created_at.desc()).offset(skip).limit(limit) # type: ignore
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def get_assignments_for_team(
        self, db: AsyncSession, *, team_id: uuid.UUID,
        skip: int = 0, limit: int = 100
    ) -> List[TaskAssignmentModel]:
        """Отримує всі завдання, призначені конкретній команді."""
        statement = select(self.model).where(self.model.team_id == team_id).options(
            selectinload(self.model.task).selectinload(TaskModel.task_type), # type: ignore
            selectinload(self.model.status)
        ).order_by(self.model.created_at.desc()).offset(skip).limit(limit) # type: ignore
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    # `create` успадкований. `TaskAssignmentCreateSchema` має містити `task_id`
    # та або `user_id`, або `team_id`. `assigned_by_user_id` встановлюється сервісом.
    # Потрібен кастомний метод `create_assignment` або логіка в сервісі.
    async def create_assignment(
        self, db: AsyncSession, *, obj_in: TaskAssignmentCreateSchema, assigned_by_id: Optional[uuid.UUID]
    ) -> TaskAssignmentModel:
        obj_in_data = obj_in.model_dump(exclude_unset=True)
        db_obj = self.model(**obj_in_data, assigned_by_user_id=assigned_by_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # `update` успадкований. `TaskAssignmentUpdateSchema` для зміни статусу/нотаток.
    # `delete` успадкований.

task_assignment_repository = TaskAssignmentRepository(TaskAssignmentModel)

# TODO: Переконатися, що TaskAssignmentCreateSchema правильно обробляє task_id, user_id/team_id.
#       (user_id/team_id валідуються в схемі на взаємовиключність).
#       `assigned_by_user_id` та `status_id` (початковий) мають встановлюватися сервісом.
#       Метод `create_assignment` додано для цього.
#
# Все виглядає добре. Надано методи для отримання призначень за різними критеріями.
# Імпорт `TaskModel` потрібен для `selectinload`.
