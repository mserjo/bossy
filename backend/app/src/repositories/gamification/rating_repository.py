# backend/app/src/repositories/gamification/rating_repository.py
"""
Репозиторій для моделі "Рейтинг Користувача в Групі" (UserGroupRating).

Цей модуль визначає клас `UserGroupRatingRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з рейтингами користувачів у групах.
"""

from typing import List, Optional, Tuple, Any
from datetime import date  # Для фільтрації за period_end_date

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
from backend.app.src.core.dicts import RatingType # Імпорт RatingType Enum
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Абсолютний імпорт моделі та схем
from backend.app.src.models.gamification.rating import UserGroupRating
from backend.app.src.schemas.gamification.rating import (
    UserGroupRatingCreateSchema,
    UserGroupRatingUpdateSchema
)


class UserGroupRatingRepository(
    BaseRepository[UserGroupRating, UserGroupRatingCreateSchema, UserGroupRatingUpdateSchema]):
    """
    Репозиторій для управління рейтингами користувачів у групах (`UserGroupRating`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    методи для отримання рейтингу конкретного користувача в групі за певними критеріями
    та списку найкращих рейтингів для групи.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `UserGroupRating`.
        """
        super().__init__(model=UserGroupRating)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_rating_for_user_in_group(
            self,
            session: AsyncSession,
            user_id: int,
            group_id: int,
            rating_type: Optional[RatingType] = None,  # Змінено на RatingType Enum
            period_end_date: Optional[date] = None  # Для періодичних рейтингів
    ) -> Optional[UserGroupRating]:
        """
        Отримує запис рейтингу для конкретного користувача в конкретній групі,
        опціонально фільтруючи за типом рейтингу та датою завершення періоду.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            user_id (int): ID користувача.
            group_id (int): ID групи.
            rating_type (Optional[RatingType]): Тип рейтингу (Enum).
            period_end_date (Optional[date]): Дата завершення періоду для рейтингу.

        Returns:
            Optional[UserGroupRating]: Екземпляр моделі `UserGroupRating`, якщо знайдено, інакше None.
        """
        logger.debug(
            f"Отримання рейтингу для user_id {user_id}, group_id {group_id}, "
            f"type: {rating_type}, period_end: {period_end_date}"
        )

        conditions = [
            self.model.user_id == user_id,
            self.model.group_id == group_id
        ]
        if rating_type is not None:
            conditions.append(self.model.rating_type == rating_type) # Порівняння з Enum членом

        if period_end_date is not None:
            conditions.append(self.model.period_end_date == period_end_date)
        # Логіка для period_end_date IS NULL, якщо тип не 'overall' і дата не надана,
        # або якщо тип 'overall'.
        elif (rating_type is not None and rating_type != RatingType.OVERALL) or rating_type == RatingType.OVERALL:
            conditions.append(self.model.period_end_date.is_(None))


        stmt = select(self.model).where(*conditions)
        try:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Помилка при отриманні рейтингу для user_id {user_id}, group_id {group_id}: {e}",
                exc_info=True
            )
            return None

    async def get_top_ratings_for_group(
            self,
            session: AsyncSession,
            group_id: int,
            rating_type: Optional[RatingType] = None,  # Змінено на RatingType Enum
            period_end_date: Optional[date] = None,
            limit: int = 10
    ) -> List[UserGroupRating]:
        """
        Отримує список найкращих (top N) рейтингів для вказаної групи,
        опціонально фільтруючи за типом рейтингу та датою завершення періоду.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            group_id (int): ID групи.
            rating_type (Optional[RatingType]): Тип рейтингу (Enum).
            period_end_date (Optional[date]): Дата завершення періоду.
            limit (int): Максимальна кількість записів для повернення (топ N).

        Returns:
            List[UserGroupRating]: Список записів рейтингів, відсортованих за спаданням балів.
        """
        logger.debug(
            f"Отримання топ-{limit} рейтингів для group_id {group_id}, "
            f"type: {rating_type}, period_end: {period_end_date}"
        )
        filters_dict: Dict[str, Any] = {"group_id": group_id}

        if rating_type is not None:
            filters_dict["rating_type"] = rating_type # Передаємо Enum член напряму

        if period_end_date is not None:
            filters_dict["period_end_date"] = period_end_date
        # Логіка для period_end_date IS NULL для фільтра в get_multi
        elif (rating_type is not None and rating_type != RatingType.OVERALL) or rating_type == RatingType.OVERALL:
            filters_dict["period_end_date"] = None # Фільтр BaseRepository має обробити None як IS NULL


        sort_by_field = "rating_score"
        sort_order_str = "desc"

        try:
            items = await super().get_multi(
                session=session,
                skip=0, # Для top N, skip завжди 0
                limit=limit,
                filters=filters_dict,
                sort_by=sort_by_field,
                sort_order=sort_order_str
            )
            # Для get_top_ratings_for_group зазвичай не потрібен загальний count, лише список.
            # Якщо потрібен, можна розкоментувати:
            # total_count = await super().count(session=session, filters=filters_dict)
            # logger.debug(f"Загальна кількість відповідних рейтингів (не топ): {total_count}")
            return items
        except Exception as e:
            logger.error(
                f"Помилка при отриманні топ рейтингів для group_id {group_id}: {e}",
                exc_info=True
            )
            return []
        # return items # Цей рядок недосяжний


if __name__ == "__main__":
    # Демонстраційний блок для UserGroupRatingRepository.
    logger.info("--- Репозиторій Рейтингів Користувачів в Групах (UserGroupRatingRepository) ---")

    logger.info("Для тестування UserGroupRatingRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    logger.info(f"Він успадковує методи від BaseRepository для моделі {UserGroupRating.__name__}.")
    logger.info(f"  Очікує схему створення: {UserGroupRatingCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {UserGroupRatingUpdateSchema.__name__}")

    logger.info("\nСпецифічні методи:")
    logger.info("  - get_rating_for_user_in_group(user_id, group_id, rating_type, period_end_date)")
    logger.info("  - get_top_ratings_for_group(group_id, rating_type, period_end_date, limit)")

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
    # logger.info("TODO: Інтегрувати Enum 'RatingType' з core.dicts для поля 'rating_type' та відповідної логіки фільтрації.") # Вирішено
