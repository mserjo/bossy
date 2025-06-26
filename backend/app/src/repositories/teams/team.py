# backend/app/src/repositories/teams/team.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `TeamModel`.
Надає методи для управління командами в групах.
"""

from typing import Optional, List
import uuid
from sqlalchemy import select # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload # type: ignore

from backend.app.src.models.teams.team import TeamModel
from backend.app.src.schemas.teams.team import TeamCreateSchema, TeamUpdateSchema
from backend.app.src.repositories.base import BaseRepository

class TeamRepository(BaseRepository[TeamModel, TeamCreateSchema, TeamUpdateSchema]):
    """
    Репозиторій для роботи з моделлю команд (`TeamModel`).
    """

    async def get_teams_by_group(
        self, db: AsyncSession, *, group_id: uuid.UUID,
        skip: int = 0, limit: int = 100
    ) -> List[TeamModel]:
        """
        Отримує список всіх команд для вказаної групи.
        """
        statement = select(self.model).where(self.model.group_id == group_id)
        statement = statement.order_by(self.model.name).offset(skip).limit(limit) # type: ignore
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def get_team_with_details(self, db: AsyncSession, team_id: uuid.UUID) -> Optional[TeamModel]:
        """
        Отримує команду разом з деталями (лідер, учасники, іконка).
        """
        from backend.app.src.models.teams.membership import TeamMembershipModel # Для selectinload
        from backend.app.src.models.auth.user import UserModel # Для selectinload

        statement = select(self.model).where(self.model.id == team_id).options(
            selectinload(self.model.leader),
            selectinload(self.model.icon_file),
            selectinload(self.model.memberships).selectinload(TeamMembershipModel.user),
            # selectinload(self.model.tasks_assigned) # Може бути багато, завантажувати окремо
            selectinload(self.model.state), # Статус команди
            selectinload(self.model.group) # Група, до якої належить команда
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_team_by_name_and_group(
        self, db: AsyncSession, *, name: str, group_id: uuid.UUID
    ) -> Optional[TeamModel]:
        """
        Отримує команду за назвою в межах конкретної групи.
        Назва команди має бути унікальною в межах групи.
        """
        statement = select(self.model).where(
            self.model.group_id == group_id,
            self.model.name == name
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    # `create` успадкований. `TeamCreateSchema` має містити `name`.
    # `group_id` встановлюється сервісом. `leader_user_id` опціонально.
    # `update` успадкований. `TeamUpdateSchema` для оновлення.

team_repository = TeamRepository(TeamModel)

# TODO: Переконатися, що `TeamCreateSchema` та `TeamUpdateSchema` коректно визначені.
#       Зокрема, що `group_id` обробляється сервісом, а не передається через схему створення.
#       (Модель `TeamModel` успадковує `group_id` від `BaseMainModel`,
#       і `CheckConstraint` гарантує, що він NOT NULL).
#
# TODO: Додати UniqueConstraint('group_id', 'name') до `TeamModel`,
#       якщо назва команди має бути унікальною в межах групи.
#       (Це логічно і рекомендовано).
#
# Все виглядає добре. Надано методи для отримання команд групи та деталей команди.
# Важливо забезпечити унікальність назв команд в межах групи.
