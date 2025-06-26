# backend/app/src/repositories/tasks/dependency.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `TaskDependencyModel`.
Надає методи для управління залежностями між завданнями.
"""

from typing import Optional, List
import uuid
from sqlalchemy import select, and_, or_ # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload, joinedload # type: ignore

from backend.app.src.models.tasks.dependency import TaskDependencyModel
from backend.app.src.schemas.tasks.dependency import TaskDependencyCreateSchema, TaskDependencyUpdateSchema
from backend.app.src.repositories.base import BaseRepository

class TaskDependencyRepository(BaseRepository[TaskDependencyModel, TaskDependencyCreateSchema, TaskDependencyUpdateSchema]):
    """
    Репозиторій для роботи з моделлю залежностей між завданнями (`TaskDependencyModel`).
    """

    async def get_prerequisites_for_task(self, db: AsyncSession, *, dependent_task_id: uuid.UUID) -> List[TaskDependencyModel]:
        """
        Отримує список всіх завдань-передумов для вказаного залежного завдання.
        """
        statement = select(self.model).where(
            self.model.dependent_task_id == dependent_task_id
        ).options(
            selectinload(self.model.prerequisite_task) # Завантажуємо самі завдання-передумови
        )
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def get_dependent_tasks_for_task(self, db: AsyncSession, *, prerequisite_task_id: uuid.UUID) -> List[TaskDependencyModel]:
        """
        Отримує список всіх завдань, які залежать від вказаного завдання-передумови.
        """
        statement = select(self.model).where(
            self.model.prerequisite_task_id == prerequisite_task_id
        ).options(
            selectinload(self.model.dependent_task) # Завантажуємо самі залежні завдання
        )
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def find_dependency(
        self, db: AsyncSession, *, dependent_task_id: uuid.UUID, prerequisite_task_id: uuid.UUID
    ) -> Optional[TaskDependencyModel]:
        """
        Знаходить конкретну залежність між двома завданнями.
        """
        statement = select(self.model).where(
            and_(
                self.model.dependent_task_id == dependent_task_id,
                self.model.prerequisite_task_id == prerequisite_task_id
            )
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    # `create` успадкований. `TaskDependencyCreateSchema` має містити `dependent_task_id`, `prerequisite_task_id`.
    # `update` успадкований. `TaskDependencyUpdateSchema` для зміни `dependency_type`.
    # `delete` успадкований. Може знадобитися кастомний метод для видалення за ID завдань.
    async def delete_dependency(
        self, db: AsyncSession, *, dependent_task_id: uuid.UUID, prerequisite_task_id: uuid.UUID
    ) -> Optional[TaskDependencyModel]:
        """Видаляє конкретну залежність між двома завданнями."""
        dependency_obj = await self.find_dependency(db, dependent_task_id=dependent_task_id, prerequisite_task_id=prerequisite_task_id)
        if dependency_obj:
            return await self.delete(db, id=dependency_obj.id)
        return None

task_dependency_repository = TaskDependencyRepository(TaskDependencyModel)

# TODO: Перевірити, чи `TaskDependencyCreateSchema` містить `dependency_type` (опціонально).
#       (Так, схема його має).
# TODO: Сервісний шар має перевіряти відсутність циклічних залежностей при створенні.
#
# Все виглядає добре. Надано методи для роботи з залежностями.
# Унікальне обмеження `UniqueConstraint('dependent_task_id', 'prerequisite_task_id', 'dependency_type')`
# в моделі `TaskDependencyModel` забезпечує, що одна й та сама залежність з тим самим типом
# не може бути створена двічі.
# `CheckConstraint` для `dependent_task_id != prerequisite_task_id` в моделі також важливий.
