# backend/app/src/repositories/teams/membership.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `TeamMembershipModel`.
Надає методи для управління членством користувачів у командах.
"""

from typing import Optional, List
import uuid
from sqlalchemy import select, and_ # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload # type: ignore

from backend.app.src.models.teams.membership import TeamMembershipModel
from backend.app.src.schemas.teams.membership import TeamMembershipCreateSchema, TeamMembershipUpdateSchema
from backend.app.src.repositories.base import BaseRepository

class TeamMembershipRepository(BaseRepository[TeamMembershipModel, TeamMembershipCreateSchema, TeamMembershipUpdateSchema]):
    """
    Репозиторій для роботи з моделлю членства в командах (`TeamMembershipModel`).
    """

    async def get_by_user_and_team(
        self, db: AsyncSession, *, user_id: uuid.UUID, team_id: uuid.UUID
    ) -> Optional[TeamMembershipModel]:
        """
        Отримує запис про членство для конкретного користувача в конкретній команді.
        """
        statement = select(self.model).where(
            and_(self.model.user_id == user_id, self.model.team_id == team_id)
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_members_of_team(
        self, db: AsyncSession, *, team_id: uuid.UUID,
        skip: int = 0, limit: int = 100
    ) -> List[TeamMembershipModel]:
        """
        Отримує список всіх членів (записів TeamMembershipModel) для вказаної команди.
        Включає розгорнуту інформацію про користувача.
        """
        statement = select(self.model).where(self.model.team_id == team_id).options(
            selectinload(self.model.user) # Завантажуємо дані користувача
        ).order_by(self.model.created_at.asc()).offset(skip).limit(limit) # type: ignore # Сортуємо за датою приєднання
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def get_teams_for_user(
        self, db: AsyncSession, *, user_id: uuid.UUID,
        skip: int = 0, limit: int = 100
    ) -> List[TeamMembershipModel]:
        """
        Отримує список всіх команд, до яких належить вказаний користувач (через записи членства).
        Включає розгорнуту інформацію про команду.
        """
        statement = select(self.model).where(self.model.user_id == user_id).options(
            selectinload(self.model.team) # Завантажуємо дані команди
        ).order_by(self.model.created_at.asc()).offset(skip).limit(limit) # type: ignore
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def delete_membership(
        self, db: AsyncSession, *, user_id: uuid.UUID, team_id: uuid.UUID
    ) -> Optional[TeamMembershipModel]:
        """
        Видаляє запис про членство користувача в команді.
        """
        membership_obj = await self.get_by_user_and_team(db, user_id=user_id, team_id=team_id)
        if membership_obj:
            return await self.delete(db, id=membership_obj.id)
        return None

    # `create` успадкований. `TeamMembershipCreateSchema` має містити `user_id`.
    # `team_id` зазвичай передається окремо або береться з контексту.
    # Потрібно буде кастомний метод `create_membership(db, team_id, obj_in: TeamMembershipCreateSchema)`
    # або сервіс має готувати `TeamMembershipCreateSchema` з `team_id`.
    #
    # Якщо `TeamMembershipCreateSchema` НЕ містить `team_id`:
    async def add_member_to_team(
        self, db: AsyncSession, *, team_id: uuid.UUID, obj_in: TeamMembershipCreateSchema
    ) -> TeamMembershipModel:
        obj_in_data = obj_in.model_dump(exclude_unset=True)
        db_obj = self.model(team_id=team_id, **obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # `update` успадкований. `TeamMembershipUpdateSchema` для оновлення `role_in_team`.

team_membership_repository = TeamMembershipRepository(TeamMembershipModel)

# TODO: Переконатися, що `TeamMembershipCreateSchema` правильно обробляє `team_id`.
#       Якщо `team_id` не є частиною схеми, то метод `add_member_to_team` є коректним.
#       Якщо `team_id` є частиною схеми, то можна використовувати успадкований `create`.
#       Поточна `TeamMembershipCreateSchema` не має `team_id`.
#
# Все виглядає добре. Надано необхідні методи для роботи з членством у командах.
