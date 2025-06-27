# backend/app/src/repositories/gamification/badge.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `BadgeModel`.
Надає методи для управління налаштуваннями бейджів гейміфікації.
"""

from typing import Optional, List
import uuid
from sqlalchemy import select, and_ # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload # type: ignore

from backend.app.src.models.gamification.badge import BadgeModel
from backend.app.src.schemas.gamification.badge import BadgeCreateSchema, BadgeUpdateSchema
from backend.app.src.repositories.base import BaseRepository

class BadgeRepository(BaseRepository[BadgeModel, BadgeCreateSchema, BadgeUpdateSchema]):
    """
    Репозиторій для роботи з моделлю налаштувань бейджів (`BadgeModel`).
    """

    async def get_badges_for_group(
        self, db: AsyncSession, *, group_id: uuid.UUID,
        skip: int = 0, limit: int = 100,
        only_active: bool = False
    ) -> List[BadgeModel]:
        """
        Отримує список налаштувань бейджів для вказаної групи.
        """
        from backend.app.src.models.dictionaries.status import StatusModel # Для фільтрації за статусом
        from backend.app.src.core.constants import STATUS_ACTIVE_CODE

        statement = select(self.model).where(self.model.group_id == group_id)
        if only_active:
            statement = statement.where(self.model.is_deleted == False) # type: ignore
            # Або через state_id:
            # statement = statement.join(StatusModel, self.model.state_id == StatusModel.id)\
            #                      .where(StatusModel.code == STATUS_ACTIVE_CODE)

        statement = statement.order_by(self.model.name).options( # type: ignore
            selectinload(self.model.icon_file)
        ).offset(skip).limit(limit)

        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def get_badge_by_name_and_group(
        self, db: AsyncSession, *, name: str, group_id: uuid.UUID
    ) -> Optional[BadgeModel]:
        """
        Отримує бейдж за назвою в межах конкретної групи.
        Назва бейджа має бути унікальною в межах групи.
        """
        statement = select(self.model).where(
            self.model.group_id == group_id,
            self.model.name == name # `name` успадковано з BaseMainModel
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    # `create` успадкований. `BadgeCreateSchema` має містити необхідні поля.
    # `group_id` встановлюється сервісом.
    async def create_badge_for_group(
        self, db: AsyncSession, *, obj_in_data: Dict[str, Any], group_id: uuid.UUID, creator_id: Optional[uuid.UUID] = None
    ) -> BadgeModel:
        # obj_in_data - це вже словник зі схеми
        db_obj = self.model(group_id=group_id, created_by_user_id=creator_id, **obj_in_data) # Додано creator_id
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # `update` та `delete` (включаючи soft_delete) успадковані.

badge_repository = BadgeRepository(BadgeModel)

# TODO: Переконатися, що `BadgeCreateSchema` не містить `group_id`.
#       (Схема `BadgeCreateSchema` не має `group_id`, це правильно).
# TODO: Перевірити обмеження `UniqueConstraint('group_id', 'name')` в `BadgeModel` (додано раніше).
#       Також `CheckConstraint('group_id IS NOT NULL')` (додано раніше).
#
# Все виглядає добре. Надано методи для роботи з налаштуваннями бейджів.
# Фільтр `only_active` в `get_badges_for_group` для отримання лише активних бейджів.
