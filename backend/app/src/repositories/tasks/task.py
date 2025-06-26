# backend/app/src/repositories/tasks/task.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `TaskModel`.
Надає методи для управління завданнями та подіями.
"""

from typing import Optional, List, Any, Dict
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select, and_, or_, func # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload, joinedload, contains_eager # type: ignore

from backend.app.src.models.tasks.task import TaskModel
from backend.app.src.schemas.tasks.task import TaskCreateSchema, TaskUpdateSchema
from backend.app.src.repositories.base import BaseRepository
from backend.app.src.models.dictionaries.task_type import TaskTypeModel # Для фільтрації за типом
from backend.app.src.models.auth.user import UserModel # Для фільтрації за автором
from backend.app.src.models.teams.team import TeamModel # Для фільтрації за командою

class TaskRepository(BaseRepository[TaskModel, TaskCreateSchema, TaskUpdateSchema]):
    """
    Репозиторій для роботи з моделлю завдань/подій (`TaskModel`).
    """

    async def get_task_with_details(self, db: AsyncSession, task_id: uuid.UUID) -> Optional[TaskModel]:
        """
        Отримує завдання з розгорнутими основними зв'язками.
        """
        statement = select(self.model).where(self.model.id == task_id).options(
            selectinload(self.model.group),
            selectinload(self.model.task_type),
            selectinload(self.model.creator),
            selectinload(self.model.state),
            selectinload(self.model.parent_task),
            # selectinload(self.model.child_tasks), # Може бути багато
            selectinload(self.model.team),
            selectinload(self.model.streak_bonus_reference_task),
            # selectinload(self.model.assignments), # Зазвичай окремо
            # selectinload(self.model.completions), # Зазвичай окремо
            # selectinload(self.model.reviews), # Зазвичай окремо
            # selectinload(self.model.source_proposal) # Якщо потрібно
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_tasks_for_group(
        self, db: AsyncSession, *, group_id: uuid.UUID,
        task_type_code: Optional[str] = None,
        status_code: Optional[str] = None, # Код статусу завдання
        is_mandatory: Optional[bool] = None,
        assignee_user_id: Optional[uuid.UUID] = None, # Якщо завдання призначене цьому користувачу
        assignee_team_id: Optional[uuid.UUID] = None, # Якщо завдання призначене цій команді
        created_by_user_id: Optional[uuid.UUID] = None,
        due_date_before: Optional[datetime] = None,
        due_date_after: Optional[datetime] = None,
        is_recurring: Optional[bool] = None,
        skip: int = 0, limit: int = 100,
        order_by: Optional[List[str]] = None,
        include_details: bool = False # Чи завантажувати деталі (тип, автор, статус)
    ) -> List[TaskModel]:
        """
        Отримує список завдань для вказаної групи з можливістю фільтрації та сортування.
        """
        from backend.app.src.models.dictionaries.status import StatusModel # Для фільтрації за статусом
        from backend.app.src.models.tasks.assignment import TaskAssignmentModel # Для фільтрації за виконавцем

        statement = select(self.model).where(self.model.group_id == group_id)

        if task_type_code:
            # Потрібен JOIN з TaskTypeModel
            statement = statement.join(TaskTypeModel, self.model.task_type_id == TaskTypeModel.id).where(TaskTypeModel.code == task_type_code)

        if status_code:
            # Потрібен JOIN зі StatusModel
            statement = statement.join(StatusModel, self.model.state_id == StatusModel.id).where(StatusModel.code == status_code)

        if is_mandatory is not None:
            statement = statement.where(self.model.is_mandatory == is_mandatory)

        if created_by_user_id:
            statement = statement.where(self.model.created_by_user_id == created_by_user_id)

        if due_date_before:
            statement = statement.where(self.model.due_date <= due_date_before)

        if due_date_after:
            statement = statement.where(self.model.due_date >= due_date_after)

        if is_recurring is not None:
            statement = statement.where(self.model.is_recurring == is_recurring)

        if assignee_user_id or assignee_team_id:
            # Потрібен JOIN з TaskAssignmentModel
            # Це знайде завдання, які МАЮТЬ призначення вказаному користувачу/команді.
            assignment_conditions = []
            if assignee_user_id:
                assignment_conditions.append(TaskAssignmentModel.user_id == assignee_user_id)
            if assignee_team_id:
                assignment_conditions.append(TaskAssignmentModel.team_id == assignee_team_id)

            if assignment_conditions:
                statement = statement.join(TaskAssignmentModel, self.model.id == TaskAssignmentModel.task_id).where(
                    or_(*assignment_conditions)
                )

        if include_details:
            statement = statement.options(
                selectinload(self.model.task_type),
                selectinload(self.model.creator),
                selectinload(self.model.state)
            )

        statement = await self._apply_order_by(statement, order_by) # Використовуємо метод з BaseRepository
        statement = statement.offset(skip).limit(limit)

        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def get_subtasks_for_task(self, db: AsyncSession, parent_task_id: uuid.UUID) -> List[TaskModel]:
        """Отримує всі підзадачі для вказаного батьківського завдання."""
        statement = select(self.model).where(self.model.parent_task_id == parent_task_id)
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    # `create` успадкований. `TaskCreateSchema` має містити необхідні поля.
    # `group_id` та `created_by_user_id` мають бути встановлені сервісом.
    # Тому може знадобитися кастомний метод `create_task_in_group`.
    async def create_task_in_group(
        self, db: AsyncSession, *, obj_in: TaskCreateSchema, group_id: uuid.UUID, creator_id: uuid.UUID
    ) -> TaskModel:
        obj_in_data = obj_in.model_dump(exclude_unset=True)
        # Конвертація recurring_interval_description в timedelta має відбуватися в сервісі
        # перед передачею в репозиторій, або тут, якщо TaskCreateSchema має interval_seconds.
        # Поточна TaskCreateSchema має recurring_interval_description: Optional[str].
        # TaskModel має recurring_interval: Optional[timedelta].
        # Ця конвертація - відповідальність сервісу.
        # Репозиторій очікує, що obj_in_data вже містить поля, сумісні з TaskModel.
        # Якщо TaskCreateSchema містить `recurring_interval_description`,
        # то сервіс має його обробити і передати `recurring_interval` (timedelta) в `obj_in_data` для моделі.
        # Або ж, якщо TaskCreateSchema має `interval_seconds`, то тут можна конвертувати.
        # Припускаємо, що сервіс вже підготував `obj_in_data` з `recurring_interval` як `timedelta`.

        db_obj = self.model(group_id=group_id, created_by_user_id=creator_id, **obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # `update` успадкований.
    # `delete` та `soft_delete` успадковані.

task_repository = TaskRepository(TaskModel)

# TODO: Додати метод для отримання завдань, призначених конкретному користувачеві або команді,
#       з урахуванням статусу виконання, термінів тощо.
#       (Частково реалізовано в `get_tasks_for_group` через фільтри `assignee_user_id`/`assignee_team_id`).
# TODO: Додати методи для роботи з залежностями (`TaskDependencyModel`), якщо вони не будуть
#       в окремому `TaskDependencyRepository`. (Вони в окремому).
# TODO: Узгодити обробку `recurring_interval`. Якщо `TaskCreateSchema` приймає рядок/секунди,
#       а модель зберігає `timedelta`, конвертація має відбуватися на сервісному рівні.
#       Або ж репозиторій може це робити, якщо це стандартизовано.
#       Поки що припускаємо, що сервіс передає дані, готові для моделі.
#
# Все виглядає як хороший набір методів для роботи з завданнями.
# `CheckConstraint` для `group_id IS NOT NULL` в `TaskModel` вже додано.
# Фільтрація в `get_tasks_for_group` досить гнучка.
# `create_task_in_group` для зручності створення завдання в контексті групи та автора.
