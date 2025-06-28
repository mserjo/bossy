# backend/app/src/api/graphql/mutations/task.py
# -*- coding: utf-8 -*-
"""
GraphQL мутації (Mutations), пов'язані із завданнями та подіями.
"""

import strawberry
from typing import Optional, List

# Імпорт GraphQL типів
from backend.app.src.api.graphql.types.task import (
    TaskType, TaskCreateInput, TaskUpdateInput,
    TaskAssignmentType, TaskAssignInput, TaskSetStatusInput,
    TaskCompletionType, TaskVerifyCompletionInput
)
from backend.app.src.api.graphql.types.base import Node # Для ID

# TODO: Імпортувати сервіси
# from backend.app.src.services.task.task_service import TaskService
# from backend.app.src.services.task.assignment_service import TaskAssignmentService
# from backend.app.src.services.task.completion_service import TaskCompletionService
# from backend.app.src.core.dependencies import get_current_active_user, get_current_group_admin_for_group_id

@strawberry.type
class TaskMutations:
    """
    Клас, що групує GraphQL мутації, пов'язані із завданнями та їх життєвим циклом.
    """

    @strawberry.mutation(description="Створити нове завдання/подію в групі.")
    async def create_task(self, info: strawberry.Info, input: TaskCreateInput) -> Optional[TaskType]:
        """
        Створює нове завдання або подію.
        Доступно адміністратору групи, до якої належить завдання.
        """
        # context = info.context
        # current_user = context.current_user # Має бути адміном групи input.group_id
        # # Перевірка прав (наприклад, за допомогою get_current_group_admin_for_group_id(input.group_id))
        #
        # group_db_id = Node.decode_id_to_int(input.group_id, "GroupType")
        # task_service = TaskService(context.db_session)
        # # Сервіс має перевірити, чи task_type_code валідний, і встановити creator_id
        # new_task_model = await task_service.create_task(
        #     task_create_data=input, # Потрібно адаптувати схему або дані
        #     group_id=group_db_id, # Передаємо group_id явно
        #     creator_id=current_user.id
        # )
        # return TaskType.from_orm(new_task_model) if new_task_model else None
        raise NotImplementedError("Створення завдання ще не реалізовано.")

    @strawberry.mutation(description="Оновити існуюче завдання/подію.")
    async def update_task(self, info: strawberry.Info, id: strawberry.ID, input: TaskUpdateInput) -> Optional[TaskType]:
        """
        Оновлює дані існуючого завдання або події.
        Доступно адміністратору групи.
        """
        # context = info.context
        # # Перевірка прав
        # task_db_id = Node.decode_id_to_int(id, "TaskType")
        # task_service = TaskService(context.db_session)
        # # Сервіс має перевірити, що завдання належить групі, де користувач є адміном
        # updated_task_model = await task_service.update_task(
        #     task_id=task_db_id,
        #     task_update_data=input, # Адаптувати
        #     actor_id=current_user.id
        # )
        # return TaskType.from_orm(updated_task_model) if updated_task_model else None
        raise NotImplementedError("Оновлення завдання ще не реалізовано.")

    @strawberry.mutation(description="Видалити завдання/подію.")
    async def delete_task(self, info: strawberry.Info, id: strawberry.ID) -> bool:
        """
        Видаляє завдання або подію.
        Доступно адміністратору групи. Повертає True у разі успіху.
        """
        # context = info.context
        # # Перевірка прав
        # task_db_id = Node.decode_id_to_int(id, "TaskType")
        # task_service = TaskService(context.db_session)
        # success = await task_service.delete_task(task_id=task_db_id, actor_id=current_user.id)
        # return success
        raise NotImplementedError("Видалення завдання ще не реалізовано.")

    @strawberry.mutation(description="Призначити завдання користувачу.")
    async def assign_task_to_user(self, info: strawberry.Info, task_id: strawberry.ID, input: TaskAssignInput) -> Optional[TaskAssignmentType]:
        """
        Призначає завдання вказаному користувачу.
        Доступно адміністратору групи.
        """
        # context = info.context
        # # Перевірка прав (адмін групи, до якої належить task_id)
        # task_db_id = Node.decode_id_to_int(task_id, "TaskType")
        # assignee_db_id = Node.decode_id_to_int(input.user_id, "UserType")
        # assignment_service = TaskAssignmentService(context.db_session)
        # new_assignment = await assignment_service.assign_task(
        #     task_id=task_db_id, assignee_id=assignee_db_id, assigner_id=current_user.id
        # )
        # return TaskAssignmentType.from_orm(new_assignment) if new_assignment else None
        raise NotImplementedError("Призначення завдання ще не реалізовано.")

    @strawberry.mutation(description="Змінити статус виконання завдання користувачем (взяти в роботу, виконано, скасовано).")
    async def set_task_execution_status(self, info: strawberry.Info, task_id: strawberry.ID, input: TaskSetStatusInput) -> Optional[TaskAssignmentType]: # Або TaskCompletionType
        """
        Дозволяє користувачу змінити статус виконання завдання, яке йому призначено.
        Наприклад, взяти в роботу, позначити як виконане (для перевірки), скасувати.
        """
        # context = info.context
        # current_user = context.current_user # Має бути виконавцем завдання
        # task_db_id = Node.decode_id_to_int(task_id, "TaskType")
        # completion_service = TaskCompletionService(context.db_session)
        # # Сервіс має знайти TaskAssignment для current_user та task_id,
        # # перевірити допустимість зміни статусу, оновити статус, можливо, створити TaskCompletion.
        # updated_assignment_or_completion = await completion_service.user_set_task_status(
        #     task_id=task_db_id, user_id=current_user.id, status_code=input.status_code, notes=input.notes
        # )
        # # Повертати оновлений TaskAssignment або новостворений TaskCompletion
        # return ...
        raise NotImplementedError("Зміна статусу виконання завдання ще не реалізована.")

    @strawberry.mutation(description="Підтвердити або відхилити виконання завдання (адміністратором).")
    async def verify_task_completion(self, info: strawberry.Info, task_completion_id: strawberry.ID, input: TaskVerifyCompletionInput) -> Optional[TaskCompletionType]:
        """
        Дозволяє адміністратору групи підтвердити або відхилити виконання завдання,
        яке користувач позначив як виконане.
        `task_completion_id` - це ID запису про спробу виконання (статус 'REVIEW').
        """
        # context = info.context
        # current_admin = context.current_user # Має бути адміном групи
        # completion_db_id = Node.decode_id_to_int(task_completion_id, "TaskCompletionType")
        # completion_service = TaskCompletionService(context.db_session)
        # # Сервіс має перевірити права адміна, знайти TaskCompletion, оновити його статус,
        # # нарахувати бонуси/штрафи, створити транзакцію.
        # verified_completion = await completion_service.admin_verify_task_completion(
        #     task_completion_id=completion_db_id, admin_id=current_admin.id,
        #     new_status_code=input.status_code, admin_notes=input.admin_notes
        # )
        # return TaskCompletionType.from_orm(verified_completion) if verified_completion else None
        raise NotImplementedError("Перевірка виконання завдання ще не реалізована.")

    # TODO: Мутації для пропозицій завдань (TaskProposal) та відгуків на завдання (TaskReview).

# Експорт класу для агрегації в mutations/__init__.py
__all__ = [
    "TaskMutations",
]
