# backend/app/src/repositories/groups/invitation.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `GroupInvitationModel`.
Надає методи для управління запрошеннями користувачів до груп.
"""

from typing import Optional, List
import uuid
from datetime import datetime
from sqlalchemy import select, and_ # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload # type: ignore

from backend.app.src.models.groups.invitation import GroupInvitationModel
from backend.app.src.schemas.groups.invitation import GroupInvitationCreateSchema, GroupInvitationUpdateSchema
from backend.app.src.repositories.base import BaseRepository

class GroupInvitationRepository(BaseRepository[GroupInvitationModel, GroupInvitationCreateSchema, GroupInvitationUpdateSchema]):
    """
    Репозиторій для роботи з моделлю запрошень до груп (`GroupInvitationModel`).
    """

    async def get_by_invitation_code(self, db: AsyncSession, *, invitation_code: str) -> Optional[GroupInvitationModel]:
        """
        Отримує запрошення за його унікальним кодом.

        :param db: Асинхронна сесія бази даних.
        :param invitation_code: Унікальний код запрошення.
        :return: Об'єкт GroupInvitationModel або None.
        """
        statement = select(self.model).where(self.model.invitation_code == invitation_code).options(
            selectinload(self.model.group), # Завантажити інформацію про групу
            selectinload(self.model.role_to_assign) # Завантажити інформацію про роль
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_all_for_group(
        self, db: AsyncSession, *, group_id: uuid.UUID,
        skip: int = 0, limit: int = 100,
        only_active: bool = False
    ) -> List[GroupInvitationModel]:
        """
        Отримує список всіх запрошень для вказаної групи.

        :param db: Асинхронна сесія бази даних.
        :param group_id: Ідентифікатор групи.
        :param skip: Кількість записів для пропуску.
        :param limit: Максимальна кількість записів.
        :param only_active: Якщо True, повертає лише активні та не прострочені запрошення.
        :return: Список об'єктів GroupInvitationModel.
        """
        statement = select(self.model).where(self.model.group_id == group_id)
        if only_active:
            statement = statement.where(
                self.model.is_active == True,
                (self.model.expires_at > datetime.utcnow()) | (self.model.expires_at == None), # type: ignore
                (self.model.max_uses > self.model.current_uses) | (self.model.max_uses == None) # type: ignore
            )
        statement = statement.order_by(self.model.created_at.desc()).offset(skip).limit(limit) # type: ignore
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def increment_current_uses(self, db: AsyncSession, *, invitation_obj: GroupInvitationModel) -> GroupInvitationModel:
        """
        Збільшує лічильник використань запрошення.
        """
        invitation_obj.current_uses += 1
        # Перевірка, чи не перевищено max_uses, та деактивація, якщо потрібно,
        # може бути тут або в сервісі.
        if invitation_obj.max_uses is not None and invitation_obj.current_uses >= invitation_obj.max_uses:
            invitation_obj.is_active = False

        db.add(invitation_obj)
        await db.commit()
        await db.refresh(invitation_obj)
        return invitation_obj

    # `create` та `update` успадковуються.
    # `GroupInvitationCreateSchema` має містити необхідні поля (group_id, invitation_code, user_id_creator, role_to_assign_id).
    # `GroupInvitationUpdateSchema` може оновлювати status_id, is_active, expires_at, max_uses.

group_invitation_repository = GroupInvitationRepository(GroupInvitationModel)

# TODO: Переконатися, що `GroupInvitationCreateSchema` та `GroupInvitationUpdateSchema`
#       коректно визначені та містять всі необхідні/дозволені поля.
#       `invitation_code` має генеруватися сервісом.
#       `user_id_creator` встановлюється сервісом.
#
# TODO: Розглянути методи для відкликання запрошення (встановлення is_active=False або зміна status_id).
#       Це може бути частиною успадкованого `update`.
#
# Все виглядає добре. Методи `get_by_invitation_code` та `get_all_for_group` є основними.
# `increment_current_uses` - корисний допоміжний метод.
