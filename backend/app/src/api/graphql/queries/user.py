# backend/app/src/api/graphql/queries/user.py
# -*- coding: utf-8 -*-
"""
GraphQL запити (Queries), пов'язані з користувачами.
"""

import strawberry
from typing import Optional, List

# Імпорт GraphQL типів
from backend.app.src.api.graphql.types.user import UserType
# TODO: Імпорт типів для пагінації, якщо використовується Relay-стиль (Connection, Edge)
# from backend.app.src.api.graphql.types.base import PageInfo (якщо стандартна пагінація)

# TODO: Імпортувати сервіси
# from backend.app.src.services.auth.user_service import UserService
# from backend.app.src.core.dependencies import get_current_active_user, get_current_superuser

# TODO: Визначити схему для аргументів пагінації, якщо не Relay
@strawberry.input
class UserQueryArgs:
    page: Optional[int] = strawberry.field(default=1, description="Номер сторінки (починаючи з 1).")
    page_size: Optional[int] = strawberry.field(default=20, description="Кількість елементів на сторінці.")
    # TODO: Додати аргументи для фільтрації (наприклад, за роллю, статусом активності)
    # role_code: Optional[str] = None
    # is_active: Optional[bool] = None

@strawberry.type
class UserQueries:
    """
    Клас, що групує GraphQL запити, пов'язані з користувачами.
    """

    @strawberry.field(description="Отримати інформацію про поточного аутентифікованого користувача.")
    async def me(self, info: strawberry.Info) -> Optional[UserType]:
        """
        Повертає дані профілю поточного користувача.
        Якщо користувач не аутентифікований, повертає null.
        """
        # context = info.context
        # current_user = context.current_user # Припускаємо, що current_user є в контексті
        # if not current_user:
        #     return None
        #
        # # TODO: Перетворити модель користувача з контексту (напр. UserModel) на UserType
        # # user_service = UserService(context.db_session)
        # # user_model = await user_service.get_user_by_id(current_user.id) # Або вже є повна модель
        # # return UserType.from_orm(user_model) if user_model else None

        # Заглушка
        # from backend.app.src.api.graphql.types.user import UserRoleType # для прикладу
        # from datetime import datetime
        # if hasattr(info.context, "current_user_placeholder"): # Для тестування без реального контексту
        #     return UserType(id=strawberry.ID("VXNlcjox"), email="test@example.com", username="testuser", is_active=True, is_superuser=False, created_at=datetime.now(), updated_at=datetime.now(), avatar_url=None, role=UserRoleType(id=strawberry.ID("VXNlclJvbGU6MQ=="), name="User", code="user", description=None, created_at=datetime.now(), updated_at=datetime.now()))
        return None


    @strawberry.field(description="Отримати інформацію про користувача за його ID (потребує прав супер-адміністратора).")
    async def user_by_id(self, info: strawberry.Info, id: strawberry.ID) -> Optional[UserType]:
        """
        Повертає дані конкретного користувача за його GraphQL ID.
        Доступно тільки для супер-адміністраторів.
        """
        # context = info.context
        # TODO: Перевірка прав супер-адміністратора
        #
        # # Розкодувати strawberry.ID в реальний ID бази даних (якщо потрібно)
        # try:
        #     _type_name, db_id_str = Node.decode_id(id) # Якщо використовується Node.decode_id
        #     if _type_name != "UserType": # Або просто "User"
        #         raise ValueError("Неправильний тип ID")
        #     db_id = int(db_id_str)
        # except (ValueError, TypeError):
        #     raise Exception(f"Недійсний формат ID користувача: {id}")
        #
        # user_service = UserService(context.db_session)
        # user_model = await user_service.get_user_by_id(user_id=db_id)
        # return UserType.from_orm(user_model) if user_model else None

        # Заглушка
        # from datetime import datetime
        # if id == strawberry.ID("VXNlcjox"): # "User:1" base64
        #      return UserType(id=id, email="user1@example.com", username="user1", is_active=True, is_superuser=False, created_at=datetime.now(), updated_at=datetime.now(), avatar_url=None)
        return None

    @strawberry.field(description="Отримати список всіх користувачів системи (потребує прав супер-адміністратора).")
    async def all_users(self, info: strawberry.Info, args: Optional[UserQueryArgs] = None) -> List[UserType]: # TODO: Замінити на Connection тип для Relay
        """
        Повертає список всіх користувачів системи з пагінацією та фільтрацією.
        Доступно тільки для супер-адміністраторів.
        """
        # context = info.context
        # TODO: Перевірка прав супер-адміністратора
        #
        # page = args.page if args else 1
        # page_size = args.page_size if args else 20
        # skip = (page - 1) * page_size
        #
        # user_service = UserService(context.db_session)
        # user_models = await user_service.get_all_users(skip=skip, limit=page_size) # Сервіс має підтримувати фільтри з args
        # return [UserType.from_orm(u) for u in user_models]

        # Заглушка
        return []

# Експорт класу для агрегації в queries/__init__.py
__all__ = [
    "UserQueries",
    "UserQueryArgs",
]
