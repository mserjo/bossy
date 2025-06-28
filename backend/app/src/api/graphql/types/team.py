# backend/app/src/api/graphql/types/team.py
# -*- coding: utf-8 -*-
"""
GraphQL типи, пов'язані з командами.

Цей модуль визначає GraphQL типи для сутності "Команда",
"Членство в команді" тощо. Команди зазвичай існують в контексті групи.
"""

import strawberry
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

from backend.app.src.api.graphql.types.base import Node, TimestampsInterface

if TYPE_CHECKING:
    from backend.app.src.api.graphql.types.user import UserType
    from backend.app.src.api.graphql.types.group import GroupType
    # from backend.app.src.api.graphql.types.task import TaskType # Якщо команда може бути прив'язана до завдання

@strawberry.type
class TeamMembershipType(Node, TimestampsInterface):
    """
    GraphQL тип, що представляє членство користувача в команді.
    """
    id: strawberry.ID
    user: "UserType" = strawberry.field(description="Користувач, що є членом команди.")
    # team: "TeamType" # Зазвичай не потрібно, бо отримується в контексті команди
    # role_in_team: Optional[str] = strawberry.field(description="Роль користувача в команді (напр. 'лідер', 'учасник').") # Якщо є
    joined_at: datetime = strawberry.field(description="Час приєднання до команди.")
    created_at: datetime
    updated_at: datetime
    # db_id: strawberry.Private[int]


@strawberry.type
class TeamType(Node, TimestampsInterface):
    """
    GraphQL тип, що представляє команду.
    """
    id: strawberry.ID
    name: str = strawberry.field(description="Назва команди.")
    description: Optional[str] = strawberry.field(description="Опис команди.")
    group: "GroupType" = strawberry.field(description="Група, до якої належить команда.")

    created_by: Optional["UserType"] = strawberry.field(description="Користувач (адмін групи), що створив команду.")
    created_at: datetime
    updated_at: datetime

    # Поля, що потребують резолверів
    @strawberry.field
    async def members(self, info: strawberry.Info) -> List[TeamMembershipType]:
        """Список учасників команди."""
        # TODO: Реалізувати резолвер
        # db_id = self.db_id
        # return await info.context.dataloaders.team_members_by_team_id.load(db_id)
        return [] # Заглушка

    @strawberry.field
    async def member_count(self, info: strawberry.Info) -> int:
        """Кількість учасників у команді."""
        # TODO: Реалізувати резолвер
        return 0 # Заглушка

    # TODO: Поле для зв'язаних командних завдань, якщо є
    # @strawberry.field
    # async def team_tasks(self, info: strawberry.Info) -> List["TaskType"]:
    #     pass

    # db_id: strawberry.Private[int]


# --- Вхідні типи (Input Types) для мутацій ---

@strawberry.input
class TeamCreateInput:
    name: str
    group_id: strawberry.ID # ID групи, в якій створюється команда
    description: Optional[str] = strawberry.UNSET
    # Можливо, список user_ids для початкового додавання учасників
    # initial_member_ids: Optional[List[strawberry.ID]] = strawberry.UNSET

@strawberry.input
class TeamUpdateInput:
    name: Optional[str] = strawberry.UNSET
    description: Optional[str] = strawberry.UNSET

@strawberry.input
class TeamMemberAddInput:
    user_id: strawberry.ID # ID користувача, якого додають до команди

@strawberry.input
class TeamMemberRemoveInput:
    user_id: strawberry.ID # ID користувача, якого видаляють з команди


__all__ = [
    "TeamMembershipType",
    "TeamType",
    "TeamCreateInput",
    "TeamUpdateInput",
    "TeamMemberAddInput",
    "TeamMemberRemoveInput",
]
