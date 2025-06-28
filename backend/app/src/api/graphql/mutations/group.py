# backend/app/src/api/graphql/mutations/group.py
# -*- coding: utf-8 -*-
"""
GraphQL мутації (Mutations), пов'язані з групами.
"""

import strawberry
from typing import Optional, List

# Імпорт GraphQL типів
from backend.app.src.api.graphql.types.group import (
    GroupType, GroupCreateInput, GroupUpdateInput,
    GroupSettingsType, GroupSettingsUpdateInput,
    GroupMembershipType, GroupMemberAddInput, GroupMemberUpdateRoleInput,
    # GroupInviteInput # Якщо запрошення тут
)
from backend.app.src.api.graphql.types.user import UserType # Для полів типу UserType
from backend.app.src.api.graphql.types.base import Node # Для ID

# TODO: Імпортувати сервіси
# from backend.app.src.services.group.group_service import GroupService
# from backend.app.src.services.group.group_settings_service import GroupSettingsService
# from backend.app.src.services.group.membership_service import MembershipService
# from backend.app.src.services.group.invitation_service import InvitationService
# from backend.app.src.core.dependencies import get_current_active_user # Для перевірки прав

@strawberry.type
class GroupMutations:
    """
    Клас, що групує GraphQL мутації, пов'язані з групами.
    """

    @strawberry.mutation(description="Створити нову групу.")
    async def create_group(self, info: strawberry.Info, input: GroupCreateInput) -> Optional[GroupType]:
        """
        Створює нову групу. Поточний користувач стає її адміністратором.
        """
        # context = info.context
        # current_user = context.current_user
        # if not current_user:
        #     raise Exception("Автентифікація обов'язкова.")
        #
        # group_service = GroupService(context.db_session)
        # # Сервіс має обробити створення групи та призначення current_user.id як адміна
        # new_group_model = await group_service.create_group(group_data=input, owner_id=current_user.id)
        # return GroupType.from_orm(new_group_model) if new_group_model else None
        raise NotImplementedError("Створення групи ще не реалізовано.")

    @strawberry.mutation(description="Оновити дані існуючої групи.")
    async def update_group(self, info: strawberry.Info, id: strawberry.ID, input: GroupUpdateInput) -> Optional[GroupType]:
        """
        Оновлює дані групи (назву, опис тощо).
        Доступно адміністратору групи або супер-адміністратору.
        """
        # context = info.context
        # current_user = context.current_user
        # if not current_user:
        #     raise Exception("Автентифікація обов'язкова.")
        #
        # group_db_id = Node.decode_id_to_int(id, "GroupType")
        # group_service = GroupService(context.db_session)
        # # Сервіс має перевірити права (чи є current_user адміном цієї групи)
        # updated_group_model = await group_service.update_group(
        #     group_id=group_db_id,
        #     group_data=input,
        #     user_id=current_user.id # Для перевірки прав
        # )
        # return GroupType.from_orm(updated_group_model) if updated_group_model else None
        raise NotImplementedError("Оновлення групи ще не реалізовано.")

    @strawberry.mutation(description="Видалити групу.")
    async def delete_group(self, info: strawberry.Info, id: strawberry.ID) -> bool:
        """
        Видаляє групу.
        Доступно адміністратору групи (за певних умов) або супер-адміністратору.
        Повертає True у разі успіху.
        """
        # context = info.context
        # current_user = context.current_user
        # # ... (перевірка прав, логіка видалення через сервіс) ...
        # success = await group_service.delete_group(group_id=group_db_id, user_id=current_user.id)
        # return success
        raise NotImplementedError("Видалення групи ще не реалізовано.")

    @strawberry.mutation(description="Оновити налаштування групи.")
    async def update_group_settings(self, info: strawberry.Info, group_id: strawberry.ID, input: GroupSettingsUpdateInput) -> Optional[GroupSettingsType]:
        """
        Оновлює налаштування для вказаної групи.
        Доступно адміністратору групи.
        """
        # context = info.context
        # # ... (перевірка прав, логіка оновлення через GroupSettingsService) ...
        # updated_settings_model = await settings_service.update_settings(
        #     group_id=group_db_id, settings_data=input, admin_id=current_user.id
        # )
        # return GroupSettingsType.from_orm(updated_settings_model) if updated_settings_model else None
        raise NotImplementedError("Оновлення налаштувань групи ще не реалізовано.")

    @strawberry.mutation(description="Додати учасника до групи.")
    async def add_group_member(self, info: strawberry.Info, group_id: strawberry.ID, input: GroupMemberAddInput) -> Optional[GroupMembershipType]:
        """
        Додає користувача до групи з вказаною роллю.
        Доступно адміністратору групи.
        """
        # context = info.context
        # # ... (перевірка прав, логіка додавання через MembershipService) ...
        # new_membership_model = await membership_service.add_member(
        #     group_id=group_db_id, user_to_add_id=user_to_add_db_id, role_code=input.role_code, admin_id=current_user.id
        # )
        # return GroupMembershipType.from_orm(new_membership_model) if new_membership_model else None
        raise NotImplementedError("Додавання учасника до групи ще не реалізовано.")

    @strawberry.mutation(description="Видалити учасника з групи.")
    async def remove_group_member(self, info: strawberry.Info, group_id: strawberry.ID, user_id: strawberry.ID) -> bool:
        """
        Видаляє користувача з групи.
        Доступно адміністратору групи.
        """
        # context = info.context
        # # ... (перевірка прав, логіка видалення) ...
        # success = await membership_service.remove_member(group_id=group_db_id, user_to_remove_id=user_to_remove_db_id, admin_id=current_user.id)
        # return success
        raise NotImplementedError("Видалення учасника з групи ще не реалізовано.")

    @strawberry.mutation(description="Оновити роль учасника в групі.")
    async def update_group_member_role(self, info: strawberry.Info, group_id: strawberry.ID, input: GroupMemberUpdateRoleInput) -> Optional[GroupMembershipType]:
        """
        Оновлює роль користувача в групі.
        Доступно адміністратору групи.
        """
        # context = info.context
        # # ... (перевірка прав, логіка оновлення ролі) ...
        # updated_membership = await membership_service.update_member_role(...)
        # return GroupMembershipType.from_orm(updated_membership) if updated_membership else None
        raise NotImplementedError("Оновлення ролі учасника ще не реалізовано.")

    @strawberry.mutation(description="Покинути групу.")
    async def leave_group(self, info: strawberry.Info, group_id: strawberry.ID) -> bool:
        """
        Дозволяє поточному користувачу покинути групу.
        """
        # context = info.context
        # current_user = context.current_user
        # # ... (логіка виходу з групи через MembershipService, перевірка, чи не єдиний адмін) ...
        # success = await membership_service.leave_group(group_id=group_db_id, user_id=current_user.id)
        # return success
        raise NotImplementedError("Вихід з групи ще не реалізований.")

    # TODO: Мутації для запрошень (створення, прийняття), якщо вони тут, а не в окремому InvitationMutations.
    # @strawberry.mutation(description="Створити запрошення до групи.")
    # async def create_group_invitation(self, info: strawberry.Info, group_id: strawberry.ID, input: GroupInviteInput) -> Optional[str]: # Повертає код запрошення або URL
    #     pass

# Експорт класу для агрегації в mutations/__init__.py
__all__ = [
    "GroupMutations",
]
