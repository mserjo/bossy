# backend/app/src/repositories/gamification/user_level_repository.py
"""
Репозиторій для моделі "Рівень Користувача" (UserLevel).

Цей модуль визначає клас `UserLevelRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з записами про досягнення користувачами
певних рівнів гейміфікації.
"""

from typing import List, Optional, Tuple, Any

from sqlalchemy import select, func, join
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import BaseModel as PydanticBaseModel  # Для UpdateSchemaType

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделей та схем
from backend.app.src.models.gamification.user_level import UserLevel
from backend.app.src.models.gamification.level import Level  # Для join в get_current_level_for_user_in_group
from backend.app.src.schemas.gamification.user_level import UserLevelCreateSchema
from backend.app.src.config import logger # Використання спільного логера


# Записи UserLevel зазвичай не оновлюються; створюється новий запис при досягненні нового рівня.
# Тому UpdateSchema може бути простою заглушкою.
class UserLevelUpdateSchema(PydanticBaseModel):
    pass


class UserLevelRepository(BaseRepository[UserLevel, UserLevelCreateSchema, UserLevelUpdateSchema]):
    """
    Репозиторій для управління записами про рівні, досягнуті користувачами (`UserLevel`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    методи для отримання поточного/найвищого рівня користувача в групі
    та історії всіх досягнутих рівнів.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `UserLevel`.
        """
        super().__init__(model=UserLevel)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_current_level_for_user_in_group(
            self, session: AsyncSession, user_id: int, group_id: int
    ) -> Optional[UserLevel]:
        """
        Отримує поточний (найвищий досягнутий) рівень для користувача в конкретній групі.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            user_id (int): ID користувача.
            group_id (int): ID групи.

        Returns:
            Optional[UserLevel]: Екземпляр `UserLevel`, що представляє найвищий
                                 досягнутий рівень, або None, якщо рівнів не досягнуто.
        """
        logger.debug(f"Отримання поточного рівня для user_id {user_id} в group_id {group_id}")
        stmt = (
            select(self.model)
            .join(Level, self.model.level_id == Level.id)
            .where(
                self.model.user_id == user_id,
                self.model.group_id == group_id
            )
            .order_by(Level.level_number.desc(), Level.required_points.desc(), self.model.created_at.desc())
        )
        try:
            result = await session.execute(stmt)
            return result.scalars().first()
        except Exception as e:
            logger.error(
                f"Помилка при отриманні поточного рівня для user_id {user_id}, group_id {group_id}: {e}",
                exc_info=True
            )
            return None

    async def get_all_achieved_levels_for_user_in_group(
            self,
            session: AsyncSession,
            user_id: int,
            group_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[UserLevel], int]:
        """
        Отримує список всіх рівнів, досягнутих користувачем у конкретній групі, з пагінацією.
        Корисно для перегляду історії досягнень рівнів.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            user_id (int): ID користувача.
            group_id (int): ID групи.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[UserLevel], int]: Кортеж зі списком досягнутих рівнів та їх загальною кількістю.
        """
        logger.debug(
            f"Отримання всіх досягнутих рівнів для user_id {user_id}, group_id {group_id}, "
            f"skip: {skip}, limit: {limit}"
        )
        filters_dict: Dict[str, Any] = {
            "user_id": user_id,
            "group_id": group_id
        }
        sort_by_field = "created_at"
        sort_order_str = "desc" # Показувати новіші досягнення першими

        # options = [selectinload(self.model.level), selectinload(self.model.user)] # для передачі в get_multi
        try:
            items = await super().get_multi(
                session=session,
                skip=skip,
                limit=limit,
                filters=filters_dict,
                sort_by=sort_by_field,
                sort_order=sort_order_str
                # options=options
            )
            total_count = await super().count(session=session, filters=filters_dict)
            logger.debug(
                f"Знайдено {total_count} досягнутих рівнів для user_id {user_id}, group_id {group_id}"
            )
            return items, total_count
        except Exception as e:
            logger.error(
                f"Помилка при отриманні всіх досягнутих рівнів для user_id {user_id}, group_id {group_id}: {e}",
                exc_info=True
            )
            return [], 0


if __name__ == "__main__":
    # Демонстраційний блок для UserLevelRepository.
    logger.info("--- Репозиторій Рівнів Користувача (UserLevelRepository) ---")

    logger.info("Для тестування UserLevelRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    logger.info(f"Він успадковує методи від BaseRepository для моделі {UserLevel.__name__}.")
    logger.info(f"  Очікує схему створення: {UserLevelCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {UserLevelUpdateSchema.__name__} (зараз порожня)")

    logger.info("\nСпецифічні методи:")
    logger.info("  - get_current_level_for_user_in_group(user_id: int, group_id: int) -> Optional[UserLevel]")
    logger.info("  - get_all_achieved_levels_for_user_in_group(user_id: int, group_id: int, skip: int = 0, limit: int = 100)")

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
