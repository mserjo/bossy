# backend/app/src/services/gamification/rating_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `RatingService` для управління рейтингами користувачів.
"""
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.gamification.rating import RatingModel
from backend.app.src.models.auth.user import UserModel # Для перевірки прав, якщо потрібно
from backend.app.src.schemas.gamification.rating import RatingCreateSchema, RatingSchema # UpdateSchema не використовується
from backend.app.src.repositories.gamification.rating import RatingRepository, rating_repository
from backend.app.src.repositories.groups.group import group_repository # Для перевірки групи
from backend.app.src.repositories.auth.user import user_repository # Для перевірки користувача
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.dicts import RatingTypeEnum # Для типів рейтингів

class RatingService(BaseService[RatingRepository]):
    """
    Сервіс для управління рейтингами користувачів.
    Рейтинги зазвичай розраховуються та записуються системою (наприклад, періодично).
    """

    async def get_rating_by_id(self, db: AsyncSession, rating_id: uuid.UUID) -> RatingModel:
        rating = await self.repository.get(db, id=rating_id)
        if not rating:
            raise NotFoundException(f"Запис рейтингу з ID {rating_id} не знайдено.")
        return rating

    async def record_rating_snapshot(
        self, db: AsyncSession, *, obj_in: RatingCreateSchema
        # current_user: UserModel # Якщо запис рейтингу ініціюється користувачем (малоймовірно)
    ) -> RatingModel:
        """
        Зберігає знімок стану рейтингу.
        Зазвичай викликається системною задачею.
        """
        # Перевірка існування користувача та групи
        user = await user_repository.get(db, id=obj_in.user_id) # type: ignore # Потрібен імпорт user_repository
        if not user: raise NotFoundException(f"Користувач з ID {obj_in.user_id} не знайдений.")

        group = await group_repository.get(db, id=obj_in.group_id)
        if not group: raise NotFoundException(f"Група з ID {obj_in.group_id} не знайдена.")

        # Валідація rating_type_code (чи є він в Enum)
        try:
            RatingTypeEnum(obj_in.rating_type_code)
        except ValueError:
            raise BadRequestException(f"Невідомий тип рейтингу: {obj_in.rating_type_code}.")

        # TODO: Можлива перевірка, чи не існує вже запису для цієї user_id, group_id, rating_type_code, snapshot_date,
        #       якщо це має бути унікальним (модель має UniqueConstraint для цього).
        #       Репозиторій `create` кине помилку, якщо обмеження порушено.

        return await self.repository.create(db, obj_in=obj_in)


    async def get_user_rating_history(
        self, db: AsyncSession, *,
        user_id: uuid.UUID, group_id: uuid.UUID, rating_type_code: str,
        skip: int = 0, limit: int = 100
    ) -> List[RatingModel]:
        """Отримує історію рейтингів для користувача в групі за типом."""
        return await self.repository.get_rating_history_for_user_in_group(
            db, user_id=user_id, group_id=group_id, rating_type_code=rating_type_code,
            skip=skip, limit=limit
        )

    async def get_group_leaderboard(
        self, db: AsyncSession, *,
        group_id: uuid.UUID, rating_type_code: str,
        snapshot_date: Optional[datetime] = None,
        limit: int = 10
    ) -> List[RatingModel]:
        """Отримує лідерборд для групи."""
        # Перевірка існування групи
        group = await group_repository.get(db, id=group_id)
        if not group: raise NotFoundException(f"Група з ID {group_id} не знайдена.")

        # Валідація rating_type_code
        try:
            RatingTypeEnum(rating_type_code)
        except ValueError:
            raise BadRequestException(f"Невідомий тип рейтингу: {rating_type_code}.")

        return await self.repository.get_leaderboard_for_group(
            db, group_id=group_id, rating_type_code=rating_type_code,
            snapshot_date=snapshot_date, limit=limit
        )

    # Рейтинги зазвичай не оновлюються і не видаляються вручну,
    # а перераховуються та додаються нові зрізи.
    # Якщо потрібне очищення старих даних, це може бути окремий метод.

rating_service = RatingService(rating_repository)

# TODO: Імпортувати `user_repository` для `record_rating_snapshot`.
# TODO: Доопрацювати метод `get_leaderboard_for_group` в репозиторії для коректного
#       отримання останніх актуальних рейтингів, якщо `snapshot_date` не вказано.
#       Сервіс поки що просто викликає метод репозиторію.
#
# TODO: Розробити логіку/фонові задачі для періодичного розрахунку та запису рейтингів.
#       Цей сервіс в основному надає доступ до вже розрахованих даних.
#
# Все виглядає як хороший початок для RatingService.
# Основні методи для запису та отримання рейтингів.
# Валідація існування сутностей та типу рейтингу.
