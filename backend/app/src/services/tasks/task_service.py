# backend/app/src/services/tasks/task_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `TaskService` для управління завданнями та подіями.
"""
from typing import List, Optional, Union, Dict, Any
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.tasks.task import TaskModel
from backend.app.src.models.auth.user import UserModel
from backend.app.src.schemas.tasks.task import TaskCreateSchema, TaskUpdateSchema, TaskSchema
from backend.app.src.repositories.tasks.task import TaskRepository, task_repository
from backend.app.src.repositories.groups.group import group_repository # Для перевірки групи
from backend.app.src.repositories.dictionaries.task_type import task_type_repository # Для перевірки типу завдання
from backend.app.src.repositories.dictionaries.status import status_repository # Для встановлення статусу
from backend.app.src.repositories.teams.team import team_repository # Для перевірки команди
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.constants import USER_TYPE_SUPERADMIN, TASK_STATUS_NEW_CODE # Дефолтний статус для нових завдань
# from backend.app.src.services.groups.group_membership_service import group_membership_service # Для перевірки прав

class TaskService(BaseService[TaskRepository]):
    """
    Сервіс для управління завданнями та подіями.
    """

    async def get_task_by_id(self, db: AsyncSession, task_id: uuid.UUID, include_details: bool = True) -> TaskModel:
        task = None
        if include_details:
            task = await self.repository.get_task_with_details(db, task_id=task_id)
        else:
            task = await self.repository.get(db, id=task_id)
        if not task:
            raise NotFoundException(f"Завдання з ID {task_id} не знайдено.")
        return task

    async def create_task(
        self, db: AsyncSession, *, obj_in: TaskCreateSchema, group_id: uuid.UUID, current_user: UserModel
    ) -> TaskModel:
        """
        Створює нове завдання/подію в групі.
        """
        # Перевірка прав: адмін групи або superuser
        from backend.app.src.services.groups.group_membership_service import group_membership_service # Відкладений імпорт
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише адміністратор групи може створювати завдання.")

        # Перевірка існування групи
        group = await group_repository.get(db, id=group_id)
        if not group:
            raise NotFoundException(f"Групу з ID {group_id} не знайдено.")

        # Перевірка існування типу завдання
        task_type = await task_type_repository.get(db, id=obj_in.task_type_id)
        if not task_type:
            raise BadRequestException(f"Тип завдання з ID {obj_in.task_type_id} не знайдено.")

        # Перевірка батьківського завдання, якщо вказано
        if obj_in.parent_task_id:
            parent_task = await self.repository.get(db, id=obj_in.parent_task_id)
            if not parent_task:
                raise BadRequestException(f"Батьківське завдання з ID {obj_in.parent_task_id} не знайдено.")
            if parent_task.group_id != group_id: # Підзадача має бути в тій самій групі
                raise BadRequestException("Батьківське завдання належить іншій групі.")
            # TODO: Перевірка, чи батьківське завдання може мати підзадачі (на основі його TaskTypeModel.can_have_subtasks).

        # Перевірка команди, якщо вказано
        if obj_in.team_id:
            team = await team_repository.get(db, id=obj_in.team_id)
            if not team:
                raise BadRequestException(f"Команду з ID {obj_in.team_id} не знайдено.")
            if team.group_id != group_id: # Команда має бути з тієї ж групи
                raise BadRequestException("Команда належить іншій групі.")

        # Встановлення початкового статусу (наприклад, "нове")
        initial_status = await status_repository.get_by_code(db, code=TASK_STATUS_NEW_CODE)
        if not initial_status:
            raise BadRequestException(f"Початковий статус завдання '{TASK_STATUS_NEW_CODE}' не знайдено.")

        # Конвертація recurring_interval_description в timedelta
        obj_in_data = obj_in.model_dump(exclude_unset=True)
        recurring_interval_description = obj_in_data.pop("recurring_interval_description", None)
        recurring_interval_timedelta: Optional[timedelta] = None
        if obj_in.is_recurring and recurring_interval_description:
            # TODO: Реалізувати парсинг recurring_interval_description (наприклад, "daily", "P1W") в timedelta.
            #       Це може бути окрема утиліта.
            #       Поки що припускаємо, що це поле не використовується або сервіс очікує `interval_seconds`.
            #       Якщо TaskCreateSchema має `interval_seconds`, то конвертація тут:
            #       interval_seconds = obj_in_data.pop("interval_seconds", None)
            #       if interval_seconds: recurring_interval_timedelta = timedelta(seconds=interval_seconds)
            pass # Залишаю для подальшої реалізації парсингу

        # Створення завдання через метод репозиторію
        # (який приймає group_id, creator_id та підготовлені дані)
        # `obj_in_data` вже не містить `recurring_interval_description`.
        # Якщо `recurring_interval_timedelta` було розраховано, його треба додати в `obj_in_data`.
        if recurring_interval_timedelta:
            obj_in_data["recurring_interval"] = recurring_interval_timedelta

        # Встановлюємо state_id, якщо він не переданий у схемі
        if "state_id" not in obj_in_data or obj_in_data["state_id"] is None:
            obj_in_data["state_id"] = initial_status.id

        return await self.repository.create_task_in_group(
            db, obj_in_data=obj_in_data, group_id=group_id, creator_id=current_user.id # type: ignore
        )


    async def update_task(
        self, db: AsyncSession, *, task_id: uuid.UUID, obj_in: TaskUpdateSchema, current_user: UserModel
    ) -> TaskModel:
        """Оновлює існуюче завдання/подію."""
        db_task = await self.get_task_by_id(db, task_id=task_id, include_details=False)

        # Перевірка прав
        from backend.app.src.services.groups.group_membership_service import group_membership_service
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=db_task.group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Ви не маєте прав оновлювати це завдання.")

        # TODO: Додати валідацію для полів, що оновлюються (аналогічно до create_task).
        # Наприклад, перевірка існування task_type_id, parent_task_id, team_id, якщо вони змінюються.
        # Обробка recurring_interval_description, якщо він передається в TaskUpdateSchema.

        update_data = obj_in.model_dump(exclude_unset=True)
        if "recurring_interval_description" in update_data:
            # Логіка конвертації з recurring_interval_description в timedelta
            # і встановлення update_data["recurring_interval"]
            # ... (аналогічно до create_task, але для оновлення) ...
            del update_data["recurring_interval_description"] # Видаляємо, бо в моделі інше поле

        return await self.repository.update(db, db_obj=db_task, obj_in=update_data)

    async def delete_task(self, db: AsyncSession, *, task_id: uuid.UUID, current_user: UserModel) -> TaskModel:
        """Видаляє завдання/подію (м'яке видалення)."""
        db_task = await self.get_task_by_id(db, task_id=task_id, include_details=False)

        # Перевірка прав
        from backend.app.src.services.groups.group_membership_service import group_membership_service
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=db_task.group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Ви не маєте прав видаляти це завдання.")

        deleted_task = await self.repository.soft_delete(db, db_obj=db_task) # type: ignore
        if not deleted_task:
            raise NotImplementedError("М'яке видалення не підтримується або не вдалося для завдань.")
        return deleted_task

    # TODO: Додати методи для зміни статусу завдання (з перевіркою переходів).
    # TODO: Додати методи для отримання списку завдань з більш складною фільтрацією та сортуванням
    #       (наприклад, завдання для поточного користувача з урахуванням призначень та статусів).

task_service = TaskService(task_repository)

# Коментарі:
# - Сервіс використовує TaskRepository та інші репозиторії для перевірок.
# - Обробка `recurring_interval_description` потребує реалізації парсера.
# - Перевірка прав реалізована для створення/оновлення/видалення.
# - Встановлення початкового статусу для нових завдань.
# - `create_task` викликає кастомний метод `create_task_in_group` з репозиторію,
#   який приймає `group_id` та `creator_id` окремо від схеми.
#   (Виправлено: `create_task_in_group` приймає `obj_in_data: dict`).
#   Важливо, щоб `TaskCreateSchema` не містила `group_id`, `creator_id`, `state_id` (якщо вони встановлюються сервісом).
#   Або ж, якщо схема їх містить, то репозиторій має їх використовувати.
#   Поточна реалізація `TaskRepository.create_task_in_group` приймає `obj_in_data` (словник зі схеми)
#   та окремо `group_id`, `creator_id`. `state_id` встановлюється в сервісі, якщо не передано.
#
# Все виглядає як хороший початок для TaskService. Багато TODO вказують на необхідність
# подальшої деталізації бізнес-логіки.
