# backend/app/src/api/graphql/queries/task.py
# -*- coding: utf-8 -*-
"""
GraphQL запити (Queries), пов'язані із завданнями та подіями.
"""

import strawberry
from typing import Optional, List

# Імпорт GraphQL типів
from backend.app.src.api.graphql.types.task import TaskType, TaskAssignmentType, TaskCompletionType
from backend.app.src.api.graphql.types.base import Node

# TODO: Імпортувати сервіси
# from backend.app.src.services.task.task_service import TaskService
# from backend.app.src.services.task.assignment_service import TaskAssignmentService
# from backend.app.src.services.task.completion_service import TaskCompletionService
# from backend.app.src.core.dependencies import get_current_active_user

@strawberry.input
class TaskQueryArgs:
    page: Optional[int] = strawberry.field(default=1)
    page_size: Optional[int] = strawberry.field(default=20)
    group_id: strawberry.ID # Завдання завжди запитуються в контексті групи
    status_code: Optional[str] = None # Фільтр за кодом статусу завдання
    task_type_code: Optional[str] = None # Фільтр за кодом типу завдання
    assignee_id: Optional[strawberry.ID] = None # Фільтр за ID призначеного користувача

@strawberry.type
class TaskQueries:
    """
    Клас, що групує GraphQL запити, пов'язані із завданнями.
    """

    @strawberry.field(description="Отримати завдання/подію за його ID в контексті групи.")
    async def task_by_id(self, info: strawberry.Info, id: strawberry.ID, group_id: strawberry.ID) -> Optional[TaskType]:
        """
        Повертає дані конкретного завдання/події за його GraphQL ID та ID групи.
        Доступно, якщо поточний користувач є членом групи.
        """
        # context = info.context
        # current_user = context.current_user
        # if not current_user:
        #     raise Exception("Автентифікація обов'язкова")
        #
        # # Розкодування ID
        # task_db_id = Node.decode_id_to_int(id, "TaskType")
        # group_db_id = Node.decode_id_to_int(group_id, "GroupType")
        #
        # task_service = TaskService(context.db_session)
        # # Сервіс має перевірити членство користувача в групі group_db_id
        # task_model = await task_service.get_task_by_id_and_group_id_for_user(
        #     task_id=task_db_id,
        #     group_id=group_db_id,
        #     user_id=current_user.id
        # )
        # return TaskType.from_orm(task_model) if task_model else None

        # Заглушка
        return None

    @strawberry.field(description="Отримати список завдань/подій для вказаної групи.")
    async def tasks_in_group(self, info: strawberry.Info, args: TaskQueryArgs) -> List[TaskType]: # TODO: Замінити на Connection
        """
        Повертає список завдань/подій для групи з пагінацією та фільтрацією.
        Доступно членам групи.
        """
        # context = info.context
        # current_user = context.current_user
        # if not current_user:
        #     raise Exception("Автентифікація обов'язкова")
        #
        # group_db_id = Node.decode_id_to_int(args.group_id, "GroupType")
        # assignee_db_id = Node.decode_id_to_int(args.assignee_id, "UserType") if args.assignee_id else None
        #
        # skip = (args.page - 1) * args.page_size
        #
        # task_service = TaskService(context.db_session)
        # # Сервіс має перевірити членство користувача в групі group_db_id
        # task_models = await task_service.get_tasks_by_group_id(
        #     group_id=group_db_id,
        #     user_id_for_access_check=current_user.id,
        #     skip=skip,
        #     limit=args.page_size,
        #     status_code=args.status_code,
        #     task_type_code=args.task_type_code,
        #     assignee_id=assignee_db_id
        # )
        # return [TaskType.from_orm(t) for t in task_models.get("tasks", [])] # Якщо сервіс повертає dict

        # Заглушка
        return []

    @strawberry.field(description="Отримати список завдань, призначених поточному користувачу в конкретній групі.")
    async def my_assigned_tasks_in_group(self, info: strawberry.Info, group_id: strawberry.ID) -> List[TaskAssignmentType]:
        """
        Повертає список завдань, які наразі призначені поточному аутентифікованому користувачу
        в зазначеній групі.
        """
        # context = info.context
        # current_user = context.current_user
        # if not current_user:
        #     return []
        #
        # group_db_id = Node.decode_id_to_int(group_id, "GroupType")
        #
        # assignment_service = TaskAssignmentService(context.db_session)
        # # Сервіс має перевірити членство користувача в групі
        # assignment_models = await assignment_service.get_user_assignments_in_group(
        #     user_id=current_user.id,
        #     group_id=group_db_id
        # )
        # return [TaskAssignmentType.from_orm(a) for a in assignment_models]

        # Заглушка
        return []

    # TODO: Додати запити для TaskCompletion, TaskProposal, TaskReview, якщо потрібно
    # наприклад, історія виконань завдання, список пропозицій тощо.

# Експорт класу для агрегації в queries/__init__.py
__all__ = [
    "TaskQueries",
    "TaskQueryArgs",
]
