# backend/app/src/api/graphql/queries/dictionary.py
# -*- coding: utf-8 -*-
"""
GraphQL запити (Queries), пов'язані з довідниками системи.
"""

import strawberry
from typing import Optional, List

# Імпорт GraphQL типів для довідників
from backend.app.src.api.graphql.types.dictionary import (
    DictionaryGenericType, GroupTypeType, BonusTypeType, IntegrationTypeType
)
from backend.app.src.api.graphql.types.user import UserRoleType # З user.py
from backend.app.src.api.graphql.types.task import TaskTypeType, TaskStatusType # З task.py
from backend.app.src.api.graphql.types.base import Node


# TODO: Імпортувати відповідні сервіси для кожного довідника
# from backend.app.src.services.dictionary.status_service import StatusService
# from backend.app.src.services.dictionary.user_role_service import UserRoleService
# from backend.app.src.services.dictionary.group_type_service import GroupTypeService
# ... і так далі

@strawberry.type
class DictionaryQueries:
    """
    Клас, що групує GraphQL запити для отримання даних з довідників.
    Доступ до довідників зазвичай публічний або для аутентифікованих користувачів.
    """

    @strawberry.field(description="Отримати список всіх статусів завдань/виконань.")
    async def task_statuses(self, info: strawberry.Info) -> List[TaskStatusType]:
        # context = info.context
        # service = StatusService(context.db_session) # Або TaskStatusService
        # models = await service.get_all_task_statuses() # Метод має повернути статуси, що стосуються завдань
        # return [TaskStatusType.from_orm(m) for m in models]
        return [] # Заглушка

    @strawberry.field(description="Отримати статус завдання/виконання за його кодом.")
    async def task_status_by_code(self, info: strawberry.Info, code: str) -> Optional[TaskStatusType]:
        # context = info.context
        # service = StatusService(context.db_session)
        # model = await service.get_task_status_by_code(code=code)
        # return TaskStatusType.from_orm(model) if model else None
        return None # Заглушка

    @strawberry.field(description="Отримати список всіх ролей користувачів.")
    async def user_roles(self, info: strawberry.Info) -> List[UserRoleType]:
        # context = info.context
        # service = UserRoleService(context.db_session)
        # models = await service.get_all()
        # return [UserRoleType.from_orm(m) for m in models]
        return [] # Заглушка

    @strawberry.field(description="Отримати список всіх типів груп.")
    async def group_types(self, info: strawberry.Info) -> List[GroupTypeType]:
        # context = info.context
        # service = GroupTypeService(context.db_session)
        # models = await service.get_all()
        # return [GroupTypeType.from_orm(m) for m in models]
        return [] # Заглушка

    @strawberry.field(description="Отримати список всіх типів завдань.")
    async def task_types(self, info: strawberry.Info) -> List[TaskTypeType]:
        # context = info.context
        # service = TaskTypeService(context.db_session) # Потрібен такий сервіс
        # models = await service.get_all()
        # return [TaskTypeType.from_orm(m) for m in models]
        return [] # Заглушка

    @strawberry.field(description="Отримати список всіх типів бонусів (валют).")
    async def bonus_types(self, info: strawberry.Info) -> List[BonusTypeType]:
        # context = info.context
        # service = BonusTypeService(context.db_session) # Потрібен такий сервіс
        # models = await service.get_all()
        # return [BonusTypeType.from_orm(m) for m in models]
        return [] # Заглушка

    @strawberry.field(description="Отримати список всіх типів інтеграцій.")
    async def integration_types(self, info: strawberry.Info) -> List[IntegrationTypeType]:
        # context = info.context
        # service = IntegrationTypeService(context.db_session) # Потрібен такий сервіс
        # models = await service.get_all()
        # return [IntegrationTypeType.from_orm(m) for m in models]
        return [] # Заглушка

    # TODO: Додати запити для інших довідників, якщо вони є.
    # Наприклад, якщо є загальний довідник "статусів сутностей", можна зробити
    # запит типу `dictionary_items_by_category(category_code: str) -> List[DictionaryGenericType]`

# Експорт класу для агрегації в queries/__init__.py
__all__ = [
    "DictionaryQueries",
]
