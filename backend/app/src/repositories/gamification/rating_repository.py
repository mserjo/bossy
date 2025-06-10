# /backend/app/src/repositories/gamification/rating_repository.py
"""
Репозиторій для моделі "Рейтинг Користувача в Групі" (UserGroupRating).

Цей модуль визначає клас `UserGroupRatingRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з рейтингами користувачів у групах.
"""

from typing import List, Optional, Tuple, Any
from datetime import date  # Для фільтрації за period_end_date

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import selectinload

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.gamification.rating import UserGroupRating
from backend.app.src.schemas.gamification.rating import (
    UserGroupRatingCreateSchema,
    UserGroupRatingUpdateSchema
)


# from backend.app.src.config.logging import get_logger # Якщо потрібне логування

# logger = get_logger(__name__)

class UserGroupRatingRepository(
    BaseRepository[UserGroupRating, UserGroupRatingCreateSchema, UserGroupRatingUpdateSchema]):
    """
    Репозиторій для управління рейтингами користувачів у групах (`UserGroupRating`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    методи для отримання рейтингу конкретного користувача в групі за певними критеріями
    та списку найкращих рейтингів для групи.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `UserGroupRating`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=UserGroupRating)

    async def get_rating_for_user_in_group(
            self,
            user_id: int,
            group_id: int,
            rating_type: Optional[str] = None,  # Очікується значення з RatingType Enum
            period_end_date: Optional[date] = None  # Для періодичних рейтингів
    ) -> Optional[UserGroupRating]:
        """
        Отримує запис рейтингу для конкретного користувача в конкретній групі,
        опціонально фільтруючи за типом рейтингу та датою завершення періоду.

        Args:
            user_id (int): ID користувача.
            group_id (int): ID групи.
            rating_type (Optional[str]): Тип рейтингу (наприклад, 'overall', 'monthly').
            period_end_date (Optional[date]): Дата завершення періоду для рейтингу.

        Returns:
            Optional[UserGroupRating]: Екземпляр моделі `UserGroupRating`, якщо знайдено, інакше None.
        """
        filters = [
            self.model.user_id == user_id,
            self.model.group_id == group_id
        ]
        if rating_type is not None:
            filters.append(self.model.rating_type == rating_type)

        if period_end_date is not None:
            filters.append(self.model.period_end_date == period_end_date)
        # Якщо period_end_date не вказано, а тип рейтингу не 'overall',
        # можливо, потрібно шукати запис, де period_end_date IS NULL.
        # Це залежить від логіки зберігання "overall" рейтингів.
        elif rating_type != "overall":  # Припускаємо, що "overall" має period_end_date IS NULL
            filters.append(self.model.period_end_date.is_(None))

        stmt = select(self.model).where(*filters)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()  # UniqueConstraint має гарантувати не більше одного

    async def get_top_ratings_for_group(
            self,
            group_id: int,
            rating_type: Optional[str] = None,  # Очікується значення з RatingType Enum
            period_end_date: Optional[date] = None,
            limit: int = 10
    ) -> List[UserGroupRating]:
        """
        Отримує список найкращих (top N) рейтингів для вказаної групи,
        опціонально фільтруючи за типом рейтингу та датою завершення періоду.

        Args:
            group_id (int): ID групи.
            rating_type (Optional[str]): Тип рейтингу.
            period_end_date (Optional[date]): Дата завершення періоду.
            limit (int): Максимальна кількість записів для повернення (топ N).

        Returns:
            List[UserGroupRating]: Список записів рейтингів, відсортованих за спаданням балів.
        """
        filters = [self.model.group_id == group_id]
        if rating_type is not None:
            filters.append(self.model.rating_type == rating_type)

        if period_end_date is not None:
            filters.append(self.model.period_end_date == period_end_date)
        elif rating_type != "overall":
            filters.append(self.model.period_end_date.is_(None))

        order_by = [self.model.rating_score.desc()]

        # Використовуємо get_multi для отримання топ N записів
        items, _ = await self.get_multi(filters=filters, order_by=order_by, limit=limit, skip=0)
        return items


if __name__ == "__main__":
    # Демонстраційний блок для UserGroupRatingRepository.
    print("--- Репозиторій Рейтингів Користувачів в Групах (UserGroupRatingRepository) ---")

    print("Для тестування UserGroupRatingRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    print(f"Він успадковує методи від BaseRepository для моделі {UserGroupRating.__name__}.")
    print(f"  Очікує схему створення: {UserGroupRatingCreateSchema.__name__}")
    print(f"  Очікує схему оновлення: {UserGroupRatingUpdateSchema.__name__}")

    print("\nСпецифічні методи:")
    print("  - get_rating_for_user_in_group(user_id, group_id, rating_type, period_end_date)")
    print("  - get_top_ratings_for_group(group_id, rating_type, period_end_date, limit)")

    print("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
    print("TODO: Інтегрувати Enum 'RatingType' з core.dicts для поля 'rating_type' та відповідної логіки фільтрації.")
