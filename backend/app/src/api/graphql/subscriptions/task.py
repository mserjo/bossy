# backend/app/src/api/graphql/subscriptions/task.py
# -*- coding: utf-8 -*-
"""
GraphQL підписки (Subscriptions), пов'язані із завданнями.
"""

import strawberry
from typing import AsyncGenerator, Optional

# Імпорт GraphQL типів
from backend.app.src.api.graphql.types.task import TaskType
from backend.app.src.api.graphql.types.base import Node # Для ID

# TODO: Імпортувати сервіси або механізми для роботи з Pub/Sub
# from backend.app.src.services.task.subscription_manager import TaskSubscriptionManager
# from backend.app.src.core.dependencies import get_current_active_user

@strawberry.type
class TaskSubscriptions:
    """
    Клас, що групує GraphQL підписки на оновлення завдань.
    """

    @strawberry.subscription(description="Підписатися на оновлення конкретного завдання.")
    async def task_updates(self, info: strawberry.Info, task_id: strawberry.ID) -> AsyncGenerator[TaskType, None]:
        """
        Асинхронний генератор, що надсилає оновлення для вказаного завдання
        в реальному часі (наприклад, зміна статусу, назви, опису).
        Потрібна перевірка прав доступу користувача до цього завдання.
        """
        # context = info.context
        # current_user = context.current_user
        # if not current_user:
        #     yield
        #     return
        #
        # task_db_id = Node.decode_id_to_int(task_id, "TaskType")
        #
        # # TODO: Перевірити, чи має current_user доступ до task_db_id
        # # (наприклад, чи є членом групи, до якої належить завдання).
        # # has_access = await SomeAccessCheckService.check_task_access(user_id=current_user.id, task_id=task_db_id)
        # # if not has_access:
        # #     # logger.warning(f"User {current_user.id} denied subscription to task {task_db_id} due to no access.")
        # #     yield
        # #     return
        #
        # # logger.info(f"User {current_user.id} subscribed to updates for task {task_db_id}.")
        # # manager = TaskSubscriptionManager(context.redis) # Або інший Pub/Sub
        # # async for task_data in manager.subscribe_to_task_updates(task_db_id):
        # #     yield TaskType.from_pydantic(task_data) # Або from_orm, from_dict
        #
        # # Заглушка
        # import asyncio
        # from datetime import datetime
        # from backend.app.src.api.graphql.types.group import GroupType # Для заглушки
        #
        # group_stub = GroupType(id=strawberry.ID("GroupStub:1"), name="Stub Group", created_at=datetime.utcnow(), updated_at=datetime.utcnow())
        #
        # count = 0
        # while True:
        #     await asyncio.sleep(7)
        #     count += 1
        #     yield TaskType(
        #         id=task_id, # Повертаємо ID, на який підписалися
        #         name=f"Оновлене завдання (подія {count})",
        #         description=f"Опис оновлено о {datetime.utcnow()}",
        #         group=group_stub,
        #         # ... інші поля TaskType, заповнені актуальними або зміненими даними ...
        #         created_at=datetime.utcnow(), # Це не зовсім коректно для оновлення, але для заглушки
        #         updated_at=datetime.utcnow()
        #     )
        #     if count >= 2:
        #         # logger.info(f"User {current_user.id} unsubscribed from task {task_db_id} (stub limit).")
        #         break
        if False: # Щоб зробити тип AsyncGenerator[TaskType, None] валідним
            yield # pragma: no cover
        raise NotImplementedError("Підписка на оновлення завдань ще не реалізована.")

    # TODO: Можливо, підписка на нові завдання в групі:
    # @strawberry.subscription
    # async def new_tasks_in_group(self, info: strawberry.Info, group_id: strawberry.ID) -> AsyncGenerator[TaskType, None]:
    #     pass


# Експорт класу для агрегації в subscriptions/__init__.py
__all__ = [
    "TaskSubscriptions",
]
