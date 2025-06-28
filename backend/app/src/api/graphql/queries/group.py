# backend/app/src/api/graphql/queries/group.py
# -*- coding: utf-8 -*-
"""
GraphQL запити (Queries), пов'язані з групами.
"""

import strawberry
from typing import Optional, List

# Імпорт GraphQL типів
from backend.app.src.api.graphql.types.group import GroupType, GroupMembershipType
from backend.app.src.api.graphql.types.base import Node # Для розкодування ID

# TODO: Імпортувати сервіси
# from backend.app.src.services.group.group_service import GroupService
# from backend.app.src.services.group.membership_service import MembershipService
# from backend.app.src.core.dependencies import get_current_active_user # Для отримання поточного користувача

# TODO: Аргументи для пагінації/фільтрації списку груп
@strawberry.input
class GroupQueryArgs:
    page: Optional[int] = strawberry.field(default=1)
    page_size: Optional[int] = strawberry.field(default=20)
    # user_is_member: Optional[bool] = None # Фільтр: тільки групи, де поточний користувач є учасником
    # group_type_code: Optional[str] = None # Фільтр за типом групи

@strawberry.type
class GroupQueries:
    """
    Клас, що групує GraphQL запити, пов'язані з групами.
    """

    @strawberry.field(description="Отримати інформацію про групу за її ID.")
    async def group_by_id(self, info: strawberry.Info, id: strawberry.ID) -> Optional[GroupType]:
        """
        Повертає дані конкретної групи за її GraphQL ID.
        Доступно, якщо поточний користувач є членом групи або супер-адміністратором.
        """
        # context = info.context
        # current_user = context.current_user
        # if not current_user:
        #     raise Exception("Автентифікація обов'язкова")
        #
        # try:
        #     _type_name, db_id_str = Node.decode_id(id)
        #     if _type_name != "GroupType": # Або "Group"
        #         raise ValueError("Неправильний тип ID")
        #     db_id = int(db_id_str)
        # except (ValueError, TypeError):
        #     raise Exception(f"Недійсний формат ID групи: {id}")
        #
        # group_service = GroupService(context.db_session)
        # # Сервіс має перевірити права доступу user_id=current_user.id
        # group_model = await group_service.get_group_by_id_for_user(group_id=db_id, user_id=current_user.id)
        # return GroupType.from_orm(group_model) if group_model else None

        # Заглушка
        # from datetime import datetime
        # if id == strawberry.ID("R3JvdXA6MQ=="): # "Group:1" base64
        #     return GroupType(id=id, name="Тестова Група 1", description="Опис тестової групи 1", created_at=datetime.now(), updated_at=datetime.now(), icon_url=None, owner=None)
        return None

    @strawberry.field(description="Отримати список груп, доступних поточному користувачу, або всі групи (для супер-адміна).")
    async def all_groups(self, info: strawberry.Info, args: Optional[GroupQueryArgs] = None) -> List[GroupType]: # TODO: Замінити на Connection
        """
        Повертає список груп.
        - Для звичайних користувачів: групи, де вони є учасниками.
        - Для супер-адміністраторів: всі групи в системі.
        Підтримує пагінацію та фільтрацію.
        """
        # context = info.context
        # current_user = context.current_user
        # if not current_user:
        #     raise Exception("Автентифікація обов'язкова")
        #
        # page = args.page if args else 1
        # page_size = args.page_size if args else 20
        # skip = (page - 1) * page_size
        #
        # group_service = GroupService(context.db_session)
        # if current_user.is_superuser:
        #     group_models = await group_service.get_all_groups(skip=skip, limit=page_size) # Додати фільтри з args
        # else:
        #     group_models = await group_service.get_groups_for_user(user_id=current_user.id, skip=skip, limit=page_size) # Додати фільтри
        #
        # return [GroupType.from_orm(g) for g in group_models]

        # Заглушка
        return []

    @strawberry.field(description="Отримати список членства поточного користувача в групах.")
    async def my_group_memberships(self, info: strawberry.Info) -> List[GroupMembershipType]:
        """
        Повертає список записів про членство поточного користувача в різних групах,
        включаючи його роль в кожній групі.
        """
        # context = info.context
        # current_user = context.current_user
        # if not current_user:
        #     return [] # Або кинути помилку, якщо автентифікація обов'язкова
        #
        # membership_service = MembershipService(context.db_session)
        # memberships_models = await membership_service.get_user_memberships(user_id=current_user.id)
        # return [GroupMembershipType.from_orm(m) for m in memberships_models]

        # Заглушка
        return []

# Експорт класу для агрегації в queries/__init__.py
__all__ = [
    "GroupQueries",
    "GroupQueryArgs",
]
