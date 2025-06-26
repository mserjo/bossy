# backend/app/src/repositories/gamification/achievement.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `AchievementModel`.
Надає методи для управління записами про отримання бейджів користувачами.
"""

from typing import Optional, List, Dict, Any
import uuid
from sqlalchemy import select, and_ # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload # type: ignore

from backend.app.src.models.gamification.achievement import AchievementModel
from backend.app.src.models.gamification.badge import BadgeModel # Для перевірки is_repeatable
from backend.app.src.schemas.gamification.achievement import AchievementCreateSchema, AchievementUpdateSchema
from backend.app.src.repositories.base import BaseRepository

class AchievementRepository(BaseRepository[AchievementModel, AchievementCreateSchema, AchievementUpdateSchema]):
    """
    Репозиторій для роботи з моделлю досягнень (отриманих бейджів) (`AchievementModel`).
    """

    async def get_user_achievement_for_badge(
        self, db: AsyncSession, *, user_id: uuid.UUID, badge_id: uuid.UUID
    ) -> Optional[AchievementModel]:
        """
        Отримує запис про досягнення, якщо користувач вже має цей бейдж.
        Якщо бейдж не повторюваний, має повернути не більше одного запису.
        Якщо повторюваний, цей метод може повернути останній, або потрібна інша логіка.
        """
        statement = select(self.model).where(
            self.model.user_id == user_id,
            self.model.badge_id == badge_id
        ).order_by(self.model.created_at.desc()) # type: ignore
        result = await db.execute(statement)
        return result.scalars().first() # Повертає останнє досягнення цього бейджа

    async def get_all_achievements_for_user(
        self, db: AsyncSession, *, user_id: uuid.UUID,
        skip: int = 0, limit: int = 100
    ) -> List[AchievementModel]:
        """
        Отримує список всіх досягнень (бейджів) для вказаного користувача.
        """
        statement = select(self.model).where(self.model.user_id == user_id).options(
            selectinload(self.model.badge).selectinload(BadgeModel.icon_file), # Завантажуємо бейдж та його іконку
            selectinload(self.model.awarder) # Адміна, якщо є
        ).order_by(self.model.created_at.desc()).offset(skip).limit(limit) # type: ignore
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def get_users_for_badge(
        self, db: AsyncSession, *, badge_id: uuid.UUID,
        skip: int = 0, limit: int = 100
    ) -> List[AchievementModel]:
        """
        Отримує список всіх користувачів, які отримали вказаний бейдж.
        """
        statement = select(self.model).where(self.model.badge_id == badge_id).options(
            selectinload(self.model.user) # Завантажуємо користувача
        ).order_by(self.model.created_at.desc()).offset(skip).limit(limit) # type: ignore
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def create_achievement(
        self, db: AsyncSession, *, obj_in: AchievementCreateSchema,
        # awarded_by_user_id встановлюється з obj_in або сервісом
    ) -> AchievementModel:
        """
        Створює запис про нове досягнення.
        Сервіс має перевірити, чи можна присудити цей бейдж (is_repeatable, умови).
        """
        # `awarded_by_user_id` та `award_reason` прийдуть в `obj_in`, якщо це ручне нагородження.
        return await super().create(db, obj_in=obj_in)

    # `update` успадкований. `AchievementUpdateSchema` може оновлювати `context_details` або `award_reason`.
    # `delete` успадкований (для відкликання бейджа).

achievement_repository = AchievementRepository(AchievementModel)

# TODO: Переконатися, що `AchievementCreateSchema` та `AchievementUpdateSchema` коректно визначені.
#       `AchievementCreateSchema` має містити `user_id`, `badge_id` та опціональні поля.
#
# TODO: Логіка перевірки `BadgeModel.is_repeatable` перед створенням дубліката
#       `(user_id, badge_id)` має бути на сервісному рівні.
#       Репозиторій просто створює запис.
#
# Все виглядає добре. Надано методи для роботи з досягненнями.
