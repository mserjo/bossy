# backend/app/src/repositories/groups/membership.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `GroupMembershipModel`.
Надає методи для управління членством користувачів у групах.
"""

from typing import Optional, List
import uuid
from sqlalchemy import select, and_ # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload # type: ignore

from backend.app.src.models.groups.membership import GroupMembershipModel
from backend.app.src.schemas.groups.membership import GroupMembershipCreateSchema, GroupMembershipUpdateSchema # Схеми для створення/оновлення
from backend.app.src.repositories.base import BaseRepository

class GroupMembershipRepository(BaseRepository[GroupMembershipModel, GroupMembershipCreateSchema, GroupMembershipUpdateSchema]):
    """
    Репозиторій для роботи з моделлю членства в групах (`GroupMembershipModel`).
    """

    async def get_by_user_and_group(
        self, db: AsyncSession, *, user_id: uuid.UUID, group_id: uuid.UUID
    ) -> Optional[GroupMembershipModel]:
        """
        Отримує запис про членство для конкретного користувача в конкретній групі.

        :param db: Асинхронна сесія бази даних.
        :param user_id: Ідентифікатор користувача.
        :param group_id: Ідентифікатор групи.
        :return: Об'єкт GroupMembershipModel або None.
        """
        statement = select(self.model).where(
            and_(self.model.user_id == user_id, self.model.group_id == group_id)
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_members_of_group(
        self, db: AsyncSession, *, group_id: uuid.UUID,
        skip: int = 0, limit: int = 100
    ) -> List[GroupMembershipModel]:
        """
        Отримує список всіх членів (записів GroupMembershipModel) для вказаної групи.
        Може включати розгорнуту інформацію про користувача та роль.
        """
        statement = select(self.model).where(self.model.group_id == group_id).options(
            selectinload(self.model.user), # Завантажуємо дані користувача
            selectinload(self.model.role)  # Завантажуємо дані ролі
        ).offset(skip).limit(limit)
        # TODO: Додати сортування, наприклад, за датою приєднання або ім'ям користувача.
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def get_groups_for_user(
        self, db: AsyncSession, *, user_id: uuid.UUID,
        skip: int = 0, limit: int = 100
    ) -> List[GroupMembershipModel]:
        """
        Отримує список всіх членств (записів GroupMembershipModel) для вказаного користувача.
        Може включати розгорнуту інформацію про групу та роль.
        """
        statement = select(self.model).where(self.model.user_id == user_id).options(
            selectinload(self.model.group), # Завантажуємо дані групи
            selectinload(self.model.role)   # Завантажуємо дані ролі
        ).offset(skip).limit(limit)
        # TODO: Додати сортування.
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def get_user_role_in_group(
        self, db: AsyncSession, *, user_id: uuid.UUID, group_id: uuid.UUID
    ) -> Optional[uuid.UUID]: # Повертає ID ролі
        """
        Отримує ID ролі користувача в конкретній групі.
        """
        membership = await self.get_by_user_and_group(db, user_id=user_id, group_id=group_id)
        return membership.user_role_id if membership else None

    # `create` та `update` успадковуються з BaseRepository.
    # `GroupMembershipCreateSchema` має містити user_id, group_id, user_role_id.
    # `GroupMembershipUpdateSchema` може оновлювати user_role_id або status_in_group_id.

    # Метод для видалення членства користувача з групи
    async def delete_membership(self, db: AsyncSession, *, user_id: uuid.UUID, group_id: uuid.UUID) -> Optional[GroupMembershipModel]:
        """
        Видаляє запис про членство користувача в групі.
        """
        membership_obj = await self.get_by_user_and_group(db, user_id=user_id, group_id=group_id)
        if membership_obj:
            return await self.delete(db, id=membership_obj.id) # Використовуємо успадкований delete
        return None


group_membership_repository = GroupMembershipRepository(GroupMembershipModel)

# TODO: Переконатися, що `GroupMembershipCreateSchema` містить всі необхідні поля
#       (user_id, group_id, user_role_id) для створення запису.
#       Сервіс буде відповідати за надання цих ID.
# TODO: Розглянути методи для отримання членів групи з певними ролями.
#
# Все виглядає добре. Репозиторій надає основні методи для роботи з членством у групах.
# Використання `selectinload` для завантаження пов'язаних даних user/role/group
# в методах `get_members_of_group` та `get_groups_for_user` є хорошою практикою.
