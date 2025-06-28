# backend/app/src/api/graphql/mutations/user.py
# -*- coding: utf-8 -*-
"""
GraphQL мутації (Mutations), пов'язані з користувачами (профіль, адмін дії).
"""

import strawberry
from typing import Optional

# Імпорт GraphQL типів
from backend.app.src.api.graphql.types.user import UserType, UserProfileUpdateInput, UserAvatarUploadInput
from backend.app.src.api.graphql.types.file import FileRecordType # Для відповіді про завантажений аватар
from backend.app.src.api.graphql.types.base import Node # Для ID

# TODO: Імпортувати сервіси
# from backend.app.src.services.auth.user_service import UserService
# from backend.app.src.services.files.avatar_service import AvatarService
# from backend.app.src.core.dependencies import get_current_active_user, get_current_superuser

@strawberry.type
class UserMutations:
    """
    Клас, що групує GraphQL мутації, пов'язані з профілем користувача
    та адміністративними діями над користувачами.
    """

    @strawberry.mutation(description="Оновити профіль поточного аутентифікованого користувача.")
    async def update_my_profile(self, info: strawberry.Info, input: UserProfileUpdateInput) -> Optional[UserType]:
        """
        Дозволяє поточному користувачу оновити дані свого профілю
        (ім'я, прізвище, нікнейм тощо).
        """
        # context = info.context
        # current_user = context.current_user
        # if not current_user:
        #     raise Exception("Автентифікація обов'язкова.")
        #
        # user_service = UserService(context.db_session)
        # # Сервіс має прийняти input, відфільтрувати UNSET поля, оновити модель користувача
        # updated_user_model = await user_service.update_user_profile(
        #     user_id=current_user.id,
        #     profile_data=input
        # )
        # return UserType.from_orm(updated_user_model) if updated_user_model else None
        raise NotImplementedError("Оновлення профілю ще не реалізовано.") # Заглушка

    @strawberry.mutation(description="Завантажити або оновити аватар поточного користувача.")
    async def upload_my_avatar(self, info: strawberry.Info, file: strawberry.scalars.Upload) -> Optional[UserType]: # Або FileRecordType, або UserAvatarType
        """
        Завантажує або оновлює аватар для поточного користувача.
        Приймає файл зображення. Повертає оновленого користувача з новим URL аватара.
        """
        # context = info.context
        # current_user = context.current_user
        # if not current_user:
        #     raise Exception("Автентифікація обов'язкова.")
        #
        # # TODO: Валідація файлу (тип, розмір) - можна зробити в сервісі
        # # file_content = await file.read()
        # # filename = file.filename
        # # content_type = file.content_type
        #
        # avatar_service = AvatarService(context.db_session)
        # user_service = UserService(context.db_session) # Для отримання оновленого UserType
        #
        # # Сервіс аватара обробляє збереження та повертає, наприклад, шлях до файлу або FileRecord
        # avatar_file_record = await avatar_service.upload_or_update_avatar_graphql(
        #     user_id=current_user.id,
        #     uploaded_file=file,
        #     request_base_url=str(context.request.base_url) # Для генерації URL
        # )
        #
        # # Оновити UserModel (якщо avatar_url там) або просто повернути UserType
        # # з новим avatar_url, отриманим з avatar_file_record.url
        # updated_user_model = await user_service.get_user_by_id(current_user.id) # Перезавантажити для свіжих даних
        # return UserType.from_orm(updated_user_model) if updated_user_model else None
        raise NotImplementedError("Завантаження аватара ще не реалізовано.") # Заглушка

    @strawberry.mutation(description="Видалити аватар поточного користувача.")
    async def delete_my_avatar(self, info: strawberry.Info) -> Optional[UserType]:
        """
        Видаляє аватар поточного користувача.
        Повертає оновленого користувача (з avatar_url=None).
        """
        # context = info.context
        # current_user = context.current_user
        # if not current_user:
        #     raise Exception("Автентифікація обов'язкова.")
        #
        # avatar_service = AvatarService(context.db_session)
        # user_service = UserService(context.db_session)
        #
        # await avatar_service.delete_avatar_by_user_id(user_id=current_user.id)
        # # Оновити UserModel (якщо avatar_url там) або просто повернути UserType
        # updated_user_model = await user_service.get_user_by_id(current_user.id)
        # return UserType.from_orm(updated_user_model) if updated_user_model else None
        raise NotImplementedError("Видалення аватара ще не реалізовано.") # Заглушка

    # --- Адміністративні мутації (потребують прав супер-адміністратора) ---
    # @strawberry.mutation(description="Оновити роль користувача (тільки супер-адмін).")
    # async def admin_update_user_role(self, info: strawberry.Info, user_id: strawberry.ID, new_role_code: str) -> Optional[UserType]:
    #     # context = info.context
    #     # current_admin = context.current_user
    #     # if not current_admin or not current_admin.is_superuser:
    #     #     raise Exception("Доступ заборонено: потрібні права супер-адміністратора.")
    #     #
    #     # user_db_id = Node.decode_id_to_int(user_id, "UserType")
    #     # user_service = UserService(context.db_session)
    #     # updated_user = await user_service.admin_set_user_role(user_id=user_db_id, role_code=new_role_code)
    #     # return UserType.from_orm(updated_user) if updated_user else None
    #     pass

    # @strawberry.mutation(description="Активувати/деактивувати користувача (тільки супер-адмін).")
    # async def admin_set_user_active_status(self, info: strawberry.Info, user_id: strawberry.ID, is_active: bool) -> Optional[UserType]:
    #     # ... аналогічно ...
    #     pass

# Експорт класу для агрегації в mutations/__init__.py
__all__ = [
    "UserMutations",
]
