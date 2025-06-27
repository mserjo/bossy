# backend/app/src/services/tasks/task_assignment_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `TaskAssignmentService` для управління призначеннями завдань.
"""
from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.tasks.assignment import TaskAssignmentModel
from backend.app.src.models.auth.user import UserModel
from backend.app.src.models.tasks.task import TaskModel # Для перевірки завдання
from backend.app.src.schemas.tasks.assignment import TaskAssignmentCreateSchema, TaskAssignmentUpdateSchema, TaskAssignmentSchema
from backend.app.src.repositories.tasks.assignment import TaskAssignmentRepository, task_assignment_repository
from backend.app.src.repositories.tasks.task import task_repository # Для отримання завдання
from backend.app.src.repositories.auth.user import user_repository # Для перевірки користувача
from backend.app.src.repositories.teams.team import team_repository # Для перевірки команди
from backend.app.src.repositories.dictionaries.status import status_repository # Для початкового статусу
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.constants import USER_TYPE_SUPERADMIN #, TASK_ASSIGNMENT_STATUS_ASSIGNED (приклад)
# from backend.app.src.services.groups.group_membership_service import group_membership_service

class TaskAssignmentService(BaseService[TaskAssignmentRepository]):
    """
    Сервіс для управління призначеннями завдань.
    """

    async def get_assignment_by_id(self, db: AsyncSession, assignment_id: uuid.UUID) -> TaskAssignmentModel:
        assignment = await self.repository.get(db, id=assignment_id)
        if not assignment:
            raise NotFoundException(f"Призначення з ID {assignment_id} не знайдено.")
        return assignment

    async def assign_task(
        self, db: AsyncSession, *,
        task_id: uuid.UUID,
        obj_in: TaskAssignmentCreateSchema, # user_id або team_id всередині
        current_user: UserModel
    ) -> TaskAssignmentModel:
        """
        Призначає завдання користувачеві або команді.
        """
        task = await task_repository.get_task_with_details(db, task_id=task_id)
        if not task:
            raise NotFoundException(f"Завдання з ID {task_id} не знайдено.")

        # Перевірка прав: адмін групи завдання або superuser
        from backend.app.src.services.groups.group_membership_service import group_membership_service # Відкладений імпорт
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=task.group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише адміністратор групи може призначати завдання.")

        # Валідація user_id/team_id вже є в TaskAssignmentCreateSchema
        if obj_in.user_id:
            assignee_user = await user_repository.get(db, id=obj_in.user_id)
            if not assignee_user:
                raise BadRequestException(f"Користувач-виконавець з ID {obj_in.user_id} не знайдений.")
            # TODO: Перевірити, чи користувач є членом групи завдання.
            if not await group_membership_service.get_membership_by_user_and_group(db, user_id=obj_in.user_id, group_id=task.group_id):
                 raise BadRequestException(f"Користувач {obj_in.user_id} не є членом групи завдання.")
            # Перевірка, чи завдання вже не призначене цьому користувачеві
            existing_assignment_user = await self.repository.get_by_task_and_user(db, task_id=task_id, user_id=obj_in.user_id)
            if existing_assignment_user:
                raise BadRequestException(f"Завдання {task_id} вже призначене користувачеві {obj_in.user_id}.")

        if obj_in.team_id:
            assignee_team = await team_repository.get(db, id=obj_in.team_id)
            if not assignee_team:
                raise BadRequestException(f"Команда-виконавець з ID {obj_in.team_id} не знайдена.")
            if assignee_team.group_id != task.group_id:
                raise BadRequestException("Команда належить іншій групі, ніж завдання.")
            # Перевірка, чи завдання вже не призначене цій команді
            existing_assignment_team = await self.repository.get_by_task_and_team(db, task_id=task_id, team_id=obj_in.team_id)
            if existing_assignment_team:
                raise BadRequestException(f"Завдання {task_id} вже призначене команді {obj_in.team_id}.")

        # Встановлення початкового статусу призначення (якщо є)
        # status_assigned = await status_repository.get_by_code(db, code=TASK_ASSIGNMENT_STATUS_ASSIGNED)
        # if not status_assigned:
        #     raise BadRequestException("Статус 'призначено' для завдання не знайдено.")
        # obj_in.status_id = status_assigned.id # Якщо схема приймає status_id

        # `task_id` вже є в `obj_in` (якщо схема так визначена) або передається окремо.
        # `TaskAssignmentCreateSchema` має `task_id`.
        # Використовуємо кастомний метод репозиторію `create_assignment`.
        return await self.repository.create_assignment(db, obj_in=obj_in, assigned_by_id=current_user.id)


    async def update_assignment_status(
        self, db: AsyncSession, *,
        assignment_id: uuid.UUID,
        obj_in: TaskAssignmentUpdateSchema, # Має містити новий status_id
        current_user: UserModel # Для перевірки прав, якщо потрібно
    ) -> TaskAssignmentModel:
        """Оновлює статус призначення (наприклад, прийнято/відхилено виконавцем)."""
        db_assignment = await self.get_assignment_by_id(db, assignment_id=assignment_id)

        # TODO: Перевірка прав: чи може `current_user` змінювати статус цього призначення?
        # (наприклад, якщо це призначений виконавець, або адмін групи).
        # if db_assignment.user_id != current_user.id and not (await group_membership_service.is_user_group_admin(...)):
        #     raise ForbiddenException("Ви не маєте прав змінювати статус цього призначення.")

        if obj_in.status_id:
            new_status = await status_repository.get(db, id=obj_in.status_id)
            if not new_status:
                raise BadRequestException(f"Статус з ID {obj_in.status_id} не знайдено.")

        return await self.repository.update(db, db_obj=db_assignment, obj_in=obj_in)

    async def unassign_task(
        self, db: AsyncSession, *,
        assignment_id: uuid.UUID,
        current_user: UserModel
    ) -> Optional[TaskAssignmentModel]:
        """Скасовує призначення завдання."""
        db_assignment = await self.get_assignment_by_id(db, assignment_id=assignment_id)
        task = await task_repository.get(db, id=db_assignment.task_id) # Потрібен group_id завдання для перевірки прав
        if not task: # Малоймовірно, якщо призначення існує
            raise NotFoundException("Пов'язане завдання не знайдено.")

        # Перевірка прав
        from backend.app.src.services.groups.group_membership_service import group_membership_service
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=task.group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише адміністратор групи може скасовувати призначення завдань.")

        return await self.repository.delete(db, id=assignment_id)

task_assignment_service = TaskAssignmentService(task_assignment_repository)

# TODO: Реалізувати перевірку прав в `update_assignment_status`.
# TODO: Додати логіку для `TASK_ASSIGNMENT_STATUS_ASSIGNED` (константа та її використання).
# TODO: Перевірити, чи користувач/команда, яким призначається завдання, є членами групи завдання. (Частково є).
#
# Все виглядає як хороший початок для сервісу призначень завдань.
