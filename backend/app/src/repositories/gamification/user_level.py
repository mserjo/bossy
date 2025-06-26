# backend/app/src/repositories/gamification/user_level.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `UserLevelModel`.
Надає методи для управління записами про досягнення рівнів користувачами.
"""

from typing import Optional, List
import uuid
from sqlalchemy import select, and_, update # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload # type: ignore

from backend.app.src.models.gamification.user_level import UserLevelModel
from backend.app.src.models.gamification.level import LevelModel # Для сортування за level_number
from backend.app.src.schemas.gamification.user_level import UserLevelCreateSchema, UserLevelUpdateSchema
from backend.app.src.repositories.base import BaseRepository

class UserLevelRepository(BaseRepository[UserLevelModel, UserLevelCreateSchema, UserLevelUpdateSchema]):
    """
    Репозиторій для роботи з моделлю досягнень рівнів користувачами (`UserLevelModel`).
    """

    async def get_current_level_for_user_in_group(
        self, db: AsyncSession, *, user_id: uuid.UUID, group_id: uuid.UUID
    ) -> Optional[UserLevelModel]:
        """
        Отримує поточний активний рівень користувача в зазначеній групі.
        """
        statement = select(self.model).where(
            self.model.user_id == user_id,
            self.model.group_id == group_id, # group_id є в UserLevelModel
            self.model.is_current == True
        ).options(selectinload(self.model.level)) # Завантажуємо деталі рівня
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_achieved_level(
        self, db: AsyncSession, *, user_id: uuid.UUID, level_id: uuid.UUID
    ) -> Optional[UserLevelModel]:
        """
        Отримує запис про досягнення конкретного рівня конкретним користувачем.
        """
        statement = select(self.model).where(
            self.model.user_id == user_id,
            self.model.level_id == level_id
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_all_achieved_levels_for_user_in_group(
        self, db: AsyncSession, *, user_id: uuid.UUID, group_id: uuid.UUID,
        skip: int = 0, limit: int = 100
    ) -> List[UserLevelModel]:
        """
        Отримує історію всіх досягнутих рівнів користувачем у вказаній групі.
        """
        statement = select(self.model).where(
            self.model.user_id == user_id,
            self.model.group_id == group_id
        ).options(
            selectinload(self.model.level)
        ).order_by(
            self.model.created_at.desc() # type: ignore # Спочатку новіші досягнення
            # Або за номером рівня: joinedload(self.model.level).level_number.desc() - складніше
        ).offset(skip).limit(limit)
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def set_level_as_current(
        self, db: AsyncSession, *, user_id: uuid.UUID, group_id: uuid.UUID, level_id_to_set_current: uuid.UUID
    ) -> Optional[UserLevelModel]:
        """
        Встановлює вказаний досягнутий рівень як поточний для користувача в групі,
        деактивуючи інші рівні для цієї пари user_id/group_id.
        """
        # 1. Деактивувати всі поточні рівні для user_id/group_id
        update_statement = (
            update(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.group_id == group_id,
                self.model.is_current == True
            )
            .values(is_current=False)
        )
        await db.execute(update_statement)

        # 2. Встановити новий рівень як поточний
        target_user_level = await self.get_achieved_level(db, user_id=user_id, level_id=level_id_to_set_current)

        if target_user_level:
            # Переконуємося, що цей рівень належить тій самій групі
            if target_user_level.group_id != group_id:
                await db.rollback() # Відкочуємо деактивацію
                # Можна кинути помилку або повернути None
                from backend.app.src.config.logging import logger
                logger.warning(f"Спроба встановити поточним рівень {level_id_to_set_current} з іншої групи для user {user_id} в групі {group_id}")
                return None

            target_user_level.is_current = True
            db.add(target_user_level)
            await db.commit()
            await db.refresh(target_user_level)
            return target_user_level
        else:
            await db.rollback() # Відкочуємо деактивацію, якщо цільовий рівень не знайдено
            return None

    # `create` успадкований. `UserLevelCreateSchema` має містити user_id, group_id, level_id.
    # `is_current` за замовчуванням True, сервіс має обробити попередні `is_current=False`.
    # Краще мати кастомний метод `achieve_level`.
    async def achieve_level(
        self, db: AsyncSession, *, obj_in: UserLevelCreateSchema
    ) -> UserLevelModel:
        """
        Створює запис про досягнення рівня та встановлює його як поточний,
        деактивуючи попередній поточний рівень для цієї user_id/group_id пари.
        """
        # Деактивуємо попередній поточний рівень
        update_statement = (
            update(self.model)
            .where(
                self.model.user_id == obj_in.user_id,
                self.model.group_id == obj_in.group_id,
                self.model.is_current == True
            )
            .values(is_current=False)
        )
        await db.execute(update_statement)

        # Створюємо новий запис
        # UserLevelCreateSchema має is_current=True за замовчуванням
        return await super().create(db, obj_in=obj_in)


user_level_repository = UserLevelRepository(UserLevelModel)

# TODO: Переконатися, що `UserLevelCreateSchema` містить `group_id` та `is_current`.
#       (Так, вони є в схемі).
# TODO: Узгодити `back_populates` для `group` в `UserLevelModel` з `GroupModel`.
#       (В `GroupModel` додано `user_level_achievements`).
#
# Все виглядає добре. Надано методи для роботи з досягненнями рівнів.
# Метод `set_level_as_current` та `achieve_level` реалізують логіку оновлення прапорця `is_current`.
# `UniqueConstraint('user_id', 'level_id')` та
# `UniqueConstraint('user_id', 'group_id', name='uq_user_group_current_level', postgresql_where=(is_current == True))`
# в моделі `UserLevelModel` мають бути враховані.
# `achieve_level` створює новий запис, який стає поточним.
# `set_level_as_current` встановлює вже існуючий запис про досягнення рівня як поточний.
