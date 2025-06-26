# backend/app/src/repositories/gamification/rating.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `RatingModel`.
Надає методи для збереження та отримання записів рейтингів користувачів.
"""

from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime
from sqlalchemy import select, and_ # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload # type: ignore

from backend.app.src.models.gamification.rating import RatingModel
from backend.app.src.schemas.gamification.rating import RatingCreateSchema # RatingUpdateSchema зазвичай не потрібна
from backend.app.src.repositories.base import BaseRepository
from pydantic import BaseModel as PydanticBaseModel # Заглушка для UpdateSchemaType

class RatingRepository(BaseRepository[RatingModel, RatingCreateSchema, PydanticBaseModel]): # UpdateSchemaType - заглушка
    """
    Репозиторій для роботи з моделлю рейтингів (`RatingModel`).
    Рейтинги зазвичай є знімками стану і не оновлюються, а створюються нові.
    """

    async def get_latest_rating_for_user_in_group(
        self, db: AsyncSession, *, user_id: uuid.UUID, group_id: uuid.UUID, rating_type_code: str
    ) -> Optional[RatingModel]:
        """
        Отримує останній актуальний запис рейтингу для користувача в групі за типом рейтингу.
        """
        statement = select(self.model).where(
            self.model.user_id == user_id,
            self.model.group_id == group_id,
            self.model.rating_type_code == rating_type_code
        ).order_by(
            self.model.snapshot_date.desc(), # type: ignore # Спочатку найновіший знімок
            self.model.created_at.desc() # type: ignore # Додатково за часом створення, якщо дати знімків однакові
        )
        result = await db.execute(statement)
        return result.scalars().first()

    async def get_rating_history_for_user_in_group(
        self, db: AsyncSession, *,
        user_id: uuid.UUID, group_id: uuid.UUID, rating_type_code: str,
        skip: int = 0, limit: int = 100
    ) -> List[RatingModel]:
        """
        Отримує історію рейтингів для користувача в групі за типом рейтингу.
        """
        statement = select(self.model).where(
            self.model.user_id == user_id,
            self.model.group_id == group_id,
            self.model.rating_type_code == rating_type_code
        ).order_by(
            self.model.snapshot_date.desc(), self.model.created_at.desc() # type: ignore
        ).offset(skip).limit(limit)
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def get_leaderboard_for_group(
        self, db: AsyncSession, *,
        group_id: uuid.UUID, rating_type_code: str,
        snapshot_date: Optional[datetime] = None, # Якщо потрібен зріз на конкретну дату
        limit: int = 10 # Кількість позицій в лідерборді
    ) -> List[RatingModel]:
        """
        Отримує лідерборд (топ користувачів) для групи за типом рейтингу
        на певну дату (або останній актуальний).
        """
        statement = select(self.model).where(
            self.model.group_id == group_id,
            self.model.rating_type_code == rating_type_code
        )
        if snapshot_date:
            # Для отримання точного зрізу на дату, потрібно знайти найближчий попередній запис
            # Це може бути складним запитом. Простіший варіант - шукати за точною snapshot_date,
            # або ж сервіс має готувати ці дані (наприклад, зберігати лише останній актуальний рейтинг на день).
            # Поки що, якщо snapshot_date вказано, шукаємо записи з цією датою.
            statement = statement.where(self.model.snapshot_date == snapshot_date)
        else:
            # Якщо дата не вказана, отримуємо останні рейтинги для кожного користувача.
            # Це потребує більш складного запиту (наприклад, з використанням window functions або subquery),
            # щоб вибрати останній запис RatingModel для кожної унікальної пари (user_id, group_id, rating_type_code).
            #
            # Спрощений варіант: сортуємо за датою та значенням, але це може повернути
            # не зовсім коректний лідерборд, якщо у користувачів різні snapshot_date.
            #
            # TODO: Реалізувати коректний запит для отримання останніх актуальних рейтингів
            #       для всіх користувачів групи за вказаним типом.
            #       Можливо, це має бути окрема таблиця "поточних рейтингів" або агрегація.
            #
            # Поки що, для простоти, сортуємо за rating_value, потім за snapshot_date.
            # Це не ідеально для "останнього" лідерборду, якщо дати знімків різні.
            statement = statement.order_by(
                self.model.rating_value.desc(), # type: ignore
                self.model.snapshot_date.desc() # type: ignore
            )

        statement = statement.limit(limit).options(
            selectinload(self.model.user) # Завантажуємо інформацію про користувача
        )
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    # `create` успадкований. `RatingCreateSchema` використовується для створення запису.
    # `update` та `delete` зазвичай не використовуються для рейтингів, оскільки це історичні дані.

rating_repository = RatingRepository(RatingModel)

# TODO: Переконатися, що `RatingCreateSchema` відповідає потребам.
#       (user_id, group_id, rating_type_code, rating_value, snapshot_date є ключовими).
#
# TODO: Метод `get_leaderboard_for_group` потребує доопрацювання для коректного
#       отримання останніх актуальних рейтингів, якщо `snapshot_date` не вказано.
#       Це може вимагати використання `DISTINCT ON (user_id)` з правильним сортуванням
#       або підзапиту.
#
# Все виглядає як хороший початок для роботи з рейтингами.
# Основна складність тут - правильне формування запитів для лідербордів.
