# backend/app/src/api/graphql/mutations/team.py
# -*- coding: utf-8 -*-
"""
GraphQL мутації (Mutations), пов'язані з командами.
"""

import strawberry
from typing import Optional, List

# Імпорт GraphQL типів
from backend.app.src.api.graphql.types.team import (
    TeamType, TeamCreateInput, TeamUpdateInput,
    TeamMembershipType, TeamMemberAddInput, TeamMemberRemoveInput
)
from backend.app.src.api.graphql.types.base import Node

# TODO: Імпортувати сервіси
# from backend.app.src.services.team.team_service import TeamService
# from backend.app.src.services.team.team_membership_service import TeamMembershipService
# from backend.app.src.core.dependencies import get_current_group_admin_for_group_id # Для перевірки прав

@strawberry.type
class TeamMutations:
    """
    Клас, що групує GraphQL мутації, пов'язані з командами.
    Команди зазвичай створюються та керуються в контексті групи.
    """

    @strawberry.mutation(description="Створити нову команду в групі.")
    async def create_team(self, info: strawberry.Info, input: TeamCreateInput) -> Optional[TeamType]:
        """
        Створює нову команду в зазначеній групі.
        Доступно адміністратору групи.
        """
        # context = info.context
        # current_admin = context.current_user # Має бути адміном групи input.group_id
        # # Перевірка прав (напр. get_current_group_admin_for_group_id(input.group_id))
        #
        # group_db_id = Node.decode_id_to_int(input.group_id, "GroupType")
        # team_service = TeamService(context.db_session)
        # new_team_model = await team_service.create_team(
        #     team_create_data=input, # Адаптувати схему або дані
        #     group_id=group_db_id,
        #     creator_id=current_admin.id
        # )
        # return TeamType.from_orm(new_team_model) if new_team_model else None
        raise NotImplementedError("Створення команди ще не реалізовано.")

    @strawberry.mutation(description="Оновити дані існуючої команди.")
    async def update_team(self, info: strawberry.Info, id: strawberry.ID, input: TeamUpdateInput) -> Optional[TeamType]:
        """
        Оновлює дані (назву, опис) існуючої команди.
        Доступно адміністратору групи, до якої належить команда.
        """
        # context = info.context
        # # Перевірка прав
        # team_db_id = Node.decode_id_to_int(id, "TeamType")
        # team_service = TeamService(context.db_session)
        # # Сервіс має перевірити, що команда належить групі, де користувач адмін
        # updated_team_model = await team_service.update_team(
        #     team_id=team_db_id,
        #     team_update_data=input, # Адаптувати
        #     actor_id=current_user.id
        # )
        # return TeamType.from_orm(updated_team_model) if updated_team_model else None
        raise NotImplementedError("Оновлення команди ще не реалізовано.")

    @strawberry.mutation(description="Видалити команду.")
    async def delete_team(self, info: strawberry.Info, id: strawberry.ID) -> bool:
        """
        Видаляє команду.
        Доступно адміністратору групи. Повертає True у разі успіху.
        """
        # context = info.context
        # # Перевірка прав
        # team_db_id = Node.decode_id_to_int(id, "TeamType")
        # team_service = TeamService(context.db_session)
        # success = await team_service.delete_team(team_id=team_db_id, actor_id=current_user.id)
        # return success
        raise NotImplementedError("Видалення команди ще не реалізовано.")

    @strawberry.mutation(description="Додати учасника до команди.")
    async def add_team_member(self, info: strawberry.Info, team_id: strawberry.ID, input: TeamMemberAddInput) -> Optional[TeamMembershipType]:
        """
        Додає користувача до вказаної команди.
        Доступно адміністратору групи, до якої належить команда.
        """
        # context = info.context
        # # Перевірка прав (адмін групи, до якої належить team_id)
        # team_db_id = Node.decode_id_to_int(team_id, "TeamType")
        # user_to_add_db_id = Node.decode_id_to_int(input.user_id, "UserType")
        #
        # membership_service = TeamMembershipService(context.db_session)
        # # Сервіс має перевірити, чи user_to_add_db_id є членом групи
        # new_member = await membership_service.add_user_to_team(
        #     team_id=team_db_id,
        #     user_id_to_add=user_to_add_db_id,
        #     actor_id=current_user.id
        # )
        # return TeamMembershipType.from_orm(new_member) if new_member else None
        raise NotImplementedError("Додавання учасника до команди ще не реалізовано.")

    @strawberry.mutation(description="Видалити учасника з команди.")
    async def remove_team_member(self, info: strawberry.Info, team_id: strawberry.ID, input: TeamMemberRemoveInput) -> bool:
        """
        Видаляє користувача з команди.
        Доступно адміністратору групи. Повертає True у разі успіху.
        """
        # context = info.context
        # # Перевірка прав
        # team_db_id = Node.decode_id_to_int(team_id, "TeamType")
        # user_to_remove_db_id = Node.decode_id_to_int(input.user_id, "UserType")
        #
        # membership_service = TeamMembershipService(context.db_session)
        # success = await membership_service.remove_user_from_team(
        #     team_id=team_db_id,
        #     user_id_to_remove=user_to_remove_db_id,
        #     actor_id=current_user.id
        # )
        # return success
        raise NotImplementedError("Видалення учасника з команди ще не реалізовано.")

# Експорт класу для агрегації в mutations/__init__.py
__all__ = [
    "TeamMutations",
]
