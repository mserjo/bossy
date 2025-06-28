# backend/app/src/api/graphql/queries/team.py
# -*- coding: utf-8 -*-
"""
GraphQL запити (Queries), пов'язані з командами.
"""

import strawberry
from typing import Optional, List

# Імпорт GraphQL типів
from backend.app.src.api.graphql.types.team import TeamType, TeamMembershipType
from backend.app.src.api.graphql.types.base import Node

# TODO: Імпортувати сервіси
# from backend.app.src.services.team.team_service import TeamService
# from backend.app.src.core.dependencies import get_current_active_user

@strawberry.input
class TeamQueryArgs:
    page: Optional[int] = strawberry.field(default=1)
    page_size: Optional[int] = strawberry.field(default=20)
    group_id: strawberry.ID # Команди завжди запитуються в контексті групи

@strawberry.type
class TeamQueries:
    """
    Клас, що групує GraphQL запити, пов'язані з командами.
    """

    @strawberry.field(description="Отримати команду за її ID в контексті групи.")
    async def team_by_id(self, info: strawberry.Info, id: strawberry.ID, group_id: strawberry.ID) -> Optional[TeamType]:
        """
        Повертає дані конкретної команди за її GraphQL ID та ID групи.
        Доступно, якщо поточний користувач є членом групи.
        """
        # context = info.context
        # current_user = context.current_user
        # if not current_user:
        #     raise Exception("Автентифікація обов'язкова")
        #
        # team_db_id = Node.decode_id_to_int(id, "TeamType")
        # group_db_id = Node.decode_id_to_int(group_id, "GroupType")
        #
        # team_service = TeamService(context.db_session)
        # # Сервіс має перевірити членство користувача в групі group_db_id
        # team_model = await team_service.get_team_by_id_and_group_id_for_user(
        #     team_id=team_db_id,
        #     group_id=group_db_id,
        #     user_id=current_user.id
        # )
        # return TeamType.from_orm(team_model) if team_model else None

        # Заглушка
        return None

    @strawberry.field(description="Отримати список команд для вказаної групи.")
    async def teams_in_group(self, info: strawberry.Info, args: TeamQueryArgs) -> List[TeamType]: # TODO: Замінити на Connection
        """
        Повертає список команд для групи з пагінацією.
        Доступно членам групи.
        """
        # context = info.context
        # current_user = context.current_user
        # if not current_user:
        #     raise Exception("Автентифікація обов'язкова")
        #
        # group_db_id = Node.decode_id_to_int(args.group_id, "GroupType")
        # skip = (args.page - 1) * args.page_size
        #
        # team_service = TeamService(context.db_session)
        # # Сервіс має перевірити членство користувача в групі group_db_id
        # team_models = await team_service.get_teams_by_group_id(
        #     group_id=group_db_id,
        #     user_id_for_access_check=current_user.id,
        #     skip=skip,
        #     limit=args.page_size
        # )
        # return [TeamType.from_orm(t) for t in team_models.get("teams", [])]

        # Заглушка
        return []

    # TODO: Додати запит для отримання команд, в яких поточний користувач є учасником,
    # можливо, з фільтром по групі.
    # @strawberry.field
    # async def my_teams(self, info: strawberry.Info, group_id: Optional[strawberry.ID] = None) -> List[TeamType]:
    #     pass

# Експорт класу для агрегації в queries/__init__.py
__all__ = [
    "TeamQueries",
    "TeamQueryArgs",
]
