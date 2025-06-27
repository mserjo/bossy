# backend/app/src/repositories/gamification/level.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `LevelModel`.
Надає методи для управління налаштуваннями рівнів гейміфікації.
"""

from typing import Optional, List
import uuid
from sqlalchemy import select, and_ # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload # type: ignore

from backend.app.src.models.gamification.level import LevelModel
from backend.app.src.schemas.gamification.level import LevelCreateSchema, LevelUpdateSchema
from backend.app.src.repositories.base import BaseRepository

class LevelRepository(BaseRepository[LevelModel, LevelCreateSchema, LevelUpdateSchema]):
    """
    Репозиторій для роботи з моделлю налаштувань рівнів (`LevelModel`).
    """

    async def get_by_level_number(self, db: AsyncSession, *, group_id: uuid.UUID, level_number: int) -> Optional[LevelModel]:
        """
        Отримує налаштування рівня за його номером в межах групи.
        """
        statement = select(self.model).where(
            and_(self.model.group_id == group_id, self.model.level_number == level_number)
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_levels_for_group(
        self, db: AsyncSession, *, group_id: uuid.UUID,
        skip: int = 0, limit: int = 100,
        only_active: bool = False
    ) -> List[LevelModel]:
        """
        Отримує список налаштувань рівнів для вказаної групи.
        """
        from backend.app.src.models.dictionaries.status import StatusModel # Для фільтрації за статусом
        from backend.app.src.core.constants import STATUS_ACTIVE_CODE

        statement = select(self.model).where(self.model.group_id == group_id)
        if only_active:
            # Припускаємо, що активність визначається статусом або is_deleted
            statement = statement.where(self.model.is_deleted == False) # type: ignore
            # Або через state_id:
            # statement = statement.join(StatusModel, self.model.state_id == StatusModel.id)\
            #                      .where(StatusModel.code == STATUS_ACTIVE_CODE)

        statement = statement.order_by(self.model.level_number.asc()).offset(skip).limit(limit) # type: ignore
        statement = statement.options(selectinload(self.model.icon_file)) # Завантажуємо іконку

        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    # `create` успадкований. `LevelCreateSchema` має містити необхідні поля.
    # `group_id` встановлюється сервісом.
    async def create_level_for_group(
        self, db: AsyncSession, *, obj_in_data: Dict[str, Any], group_id: uuid.UUID, creator_id: Optional[uuid.UUID] = None
    ) -> LevelModel:
        # obj_in_data - це вже словник зі схеми
        db_obj = self.model(group_id=group_id, created_by_user_id=creator_id, **obj_in_data) # Додано creator_id
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # `update` та `delete` (включаючи soft_delete) успадковані.

level_repository = LevelRepository(LevelModel)

# TODO: Переконатися, що `LevelCreateSchema` не містить `group_id`.
#       (Схема `LevelCreateSchema` не має `group_id`, це правильно).
# TODO: Перевірити обмеження `UniqueConstraint('group_id', 'level_number')` та
#       `UniqueConstraint('group_id', 'name')` в `LevelModel` (додано раніше).
#       Також `CheckConstraint('group_id IS NOT NULL')` (додано раніше).
#
# Все виглядає добре. Надано методи для роботи з налаштуваннями рівнів.
