# backend/app/src/repositories/groups/group.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `GroupModel`.
Надає методи для взаємодії з таблицею груп в базі даних.
"""

from typing import Optional, List
import uuid
from sqlalchemy import select # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload, joinedload # type: ignore

from backend.app.src.models.groups.group import GroupModel
from backend.app.src.schemas.groups.group import GroupCreateSchema, GroupUpdateSchema
from backend.app.src.repositories.base import BaseRepository

class GroupRepository(BaseRepository[GroupModel, GroupCreateSchema, GroupUpdateSchema]):
    """
    Репозиторій для роботи з моделлю груп (`GroupModel`).
    """

    async def get_with_details(self, db: AsyncSession, id: uuid.UUID) -> Optional[GroupModel]:
        """
        Отримує групу з деякими розгорнутими зв'язками.
        Наприклад, з типом групи, налаштуваннями, іконкою.
        """
        statement = select(self.model).where(self.model.id == id).options(
            selectinload(self.model.group_type),
            selectinload(self.model.settings),
            selectinload(self.model.icon_file),
            selectinload(self.model.parent_group), # Для ієрархії
            # selectinload(self.model.child_groups) # Може бути багато, обережно
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_user_groups(self, db: AsyncSession, *, user_id: uuid.UUID) -> List[GroupModel]:
        """
        Отримує список груп, до яких належить користувач.
        """
        # Потрібен JOIN з GroupMembershipModel
        from backend.app.src.models.groups.membership import GroupMembershipModel # Локальний імпорт для уникнення циклів

        statement = select(self.model).join(
            GroupMembershipModel, self.model.id == GroupMembershipModel.group_id
        ).where(GroupMembershipModel.user_id == user_id)
        # TODO: Додати фільтр для активного членства, якщо потрібно
        # .where(GroupMembershipModel.status_in_group_id == ID_АКТИВНОГО_СТАТУСУ_ЧЛЕНСТВА)

        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def get_child_groups(self, db: AsyncSession, *, parent_group_id: uuid.UUID) -> List[GroupModel]:
        """
        Отримує список дочірніх груп для вказаної батьківської групи.
        """
        statement = select(self.model).where(self.model.parent_group_id == parent_group_id)
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    # TODO: Додати метод для пошуку груп за назвою (з пагінацією).
    # async def search_by_name(self, db: AsyncSession, *, name_query: str, skip: int = 0, limit: int = 100) -> List[GroupModel]:
    #     statement = select(self.model).where(self.model.name.ilike(f"%{name_query}%")).offset(skip).limit(limit)
    #     result = await db.execute(statement)
    #     return result.scalars().all()

    # TODO: Додати метод для отримання групи разом з усіма її членами (якщо потрібно).
    # async def get_group_with_members(self, db: AsyncSession, id: uuid.UUID) -> Optional[GroupModel]:
    #     statement = select(self.model).where(self.model.id == id).options(
    #         selectinload(self.model.memberships).selectinload(GroupMembershipModel.user),
    #         selectinload(self.model.memberships).selectinload(GroupMembershipModel.role)
    #     )
    #     result = await db.execute(statement)
    #     return result.scalar_one_or_none()

    # TODO: Додати метод для отримання групи разом з її адміністраторами.

group_repository = GroupRepository(GroupModel)

# Все виглядає добре.
# Додано специфічні методи:
# - `get_with_details` для отримання групи з деякими важливими зв'язками.
# - `get_user_groups` для отримання списку груп користувача.
# - `get_child_groups` для ієрархії.
# Залишено TODO для інших потенційно корисних методів.
# Використано `selectinload` для ефективного завантаження зв'язків.
# Локальний імпорт `GroupMembershipModel` в `get_user_groups` для уникнення можливих циклічних залежностей
# на рівні імпорту модулів (хоча для репозиторіїв це менш критично, ніж для моделей).
