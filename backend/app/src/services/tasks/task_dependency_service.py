# backend/app/src/services/tasks/task_dependency_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `TaskDependencyService` для управління залежностями між завданнями.
"""
from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.tasks.dependency import TaskDependencyModel
from backend.app.src.models.auth.user import UserModel
from backend.app.src.schemas.tasks.dependency import TaskDependencyCreateSchema, TaskDependencyUpdateSchema, TaskDependencySchema
from backend.app.src.repositories.tasks.dependency import TaskDependencyRepository, task_dependency_repository
from backend.app.src.repositories.tasks.task import task_repository # Для перевірки існування завдань
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.constants import USER_TYPE_SUPERADMIN
# from backend.app.src.services.groups.group_membership_service import group_membership_service

class TaskDependencyService(BaseService[TaskDependencyRepository]):
    """
    Сервіс для управління залежностями між завданнями.
    """

    async def get_dependency_by_id(self, db: AsyncSession, dependency_id: uuid.UUID) -> TaskDependencyModel:
        dependency = await self.repository.get(db, id=dependency_id)
        if not dependency:
            raise NotFoundException(f"Залежність завдань з ID {dependency_id} не знайдено.")
        return dependency

    async def add_dependency(
        self, db: AsyncSession, *, obj_in: TaskDependencyCreateSchema, current_user: UserModel
    ) -> TaskDependencyModel:
        """
        Додає нову залежність між завданнями.
        """
        # Перевірка, чи завдання існують
        dependent_task = await task_repository.get(db, id=obj_in.dependent_task_id)
        if not dependent_task:
            raise BadRequestException(f"Залежне завдання з ID {obj_in.dependent_task_id} не знайдено.")

        prerequisite_task = await task_repository.get(db, id=obj_in.prerequisite_task_id)
        if not prerequisite_task:
            raise BadRequestException(f"Завдання-передумова з ID {obj_in.prerequisite_task_id} не знайдено.")

        # Перевірка, що завдання належать одній групі (або що користувач має права на обидва)
        if dependent_task.group_id != prerequisite_task.group_id:
            raise BadRequestException("Завдання мають належати одній групі для створення залежності.")

        # Перевірка прав: адмін групи або superuser
        from backend.app.src.services.groups.group_membership_service import group_membership_service # Відкладений імпорт
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=dependent_task.group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише адміністратор групи може додавати залежності між завданнями.")

        if obj_in.dependent_task_id == obj_in.prerequisite_task_id:
            raise BadRequestException("Завдання не може залежати саме від себе.")

        # Перевірка на існування такої ж залежності
        existing_dependency = await self.repository.find_dependency(
            db, dependent_task_id=obj_in.dependent_task_id, prerequisite_task_id=obj_in.prerequisite_task_id
        )
        if existing_dependency and existing_dependency.dependency_type == obj_in.dependency_type:
            raise BadRequestException("Така залежність між завданнями вже існує.")

        # TODO: Перевірка на циклічні залежності. Це складна логіка,
        #       яка потребує обходу графа залежностей. Може бути реалізована тут або винесена.
        #       Наприклад, перед додаванням A -> B, перевірити, чи не існує шляху B -> ... -> A.

        return await self.repository.create(db, obj_in=obj_in)

    async def update_dependency_type(
        self, db: AsyncSession, *, dependency_id: uuid.UUID, obj_in: TaskDependencyUpdateSchema, current_user: UserModel
    ) -> TaskDependencyModel:
        """Оновлює тип існуючої залежності."""
        db_dependency = await self.get_dependency_by_id(db, dependency_id=dependency_id)

        # Потрібно завантажити залежні завдання, щоб отримати group_id для перевірки прав
        # Або передавати group_id в цей метод.
        # Простіше завантажити:
        dependent_task = await task_repository.get(db, id=db_dependency.dependent_task_id)
        if not dependent_task: # Малоймовірно, якщо залежність існує
             raise NotFoundException("Залежне завдання для цієї залежності не знайдено.")

        from backend.app.src.services.groups.group_membership_service import group_membership_service
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=dependent_task.group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Ви не маєте прав оновлювати цю залежність.")

        return await self.repository.update(db, db_obj=db_dependency, obj_in=obj_in)

    async def remove_dependency(
        self, db: AsyncSession, *, dependency_id: uuid.UUID, current_user: UserModel
    ) -> Optional[TaskDependencyModel]:
        """Видаляє залежність між завданнями."""
        db_dependency = await self.get_dependency_by_id(db, dependency_id=dependency_id)
        dependent_task = await task_repository.get(db, id=db_dependency.dependent_task_id)
        if not dependent_task:
             raise NotFoundException("Залежне завдання для цієї залежності не знайдено.")

        from backend.app.src.services.groups.group_membership_service import group_membership_service
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=dependent_task.group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Ви не маєте прав видаляти цю залежність.")

        return await self.repository.delete(db, id=dependency_id)

task_dependency_service = TaskDependencyService(task_dependency_repository)

# TODO: Реалізувати перевірку на циклічні залежності в `add_dependency`.
# TODO: Переконатися, що `TaskDependencyCreateSchema` та `TaskDependencyUpdateSchema`
#       коректно визначені. `TaskDependencyCreateSchema` має містити `dependent_task_id`,
#       `prerequisite_task_id` та опціонально `dependency_type`.
#
# Все виглядає як хороший початок для сервісу управління залежностями завдань.
# Перевірки існування завдань та прав доступу додані.
# Валідація `dependency_type` та самопосилань є в схемах.
