# backend/app/src/repositories/gamification/level_repository.py
"""
Репозиторій для моделі "Рівень" (Level) в системі гейміфікації.

Цей модуль визначає клас `LevelRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з рівнями гейміфікації,
наприклад, отримання рівнів для конкретної групи або за номером рівня.
"""

from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession # Для type hinting у кастомних методах

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.gamification.level import Level
from backend.app.src.schemas.gamification.level import LevelCreateSchema, LevelUpdateSchema
from backend.app.src.config.logging import get_logger # Стандартизований імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)


class LevelRepository(BaseRepository[Level, LevelCreateSchema, LevelUpdateSchema]):
    """
    Репозиторій для управління рівнями гейміфікації (`Level`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи для отримання рівнів за ID групи або за номером рівня в групі.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `Level`.
        """
        super().__init__(model=Level)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_levels_by_group_id(
            self, session: AsyncSession, group_id: Optional[int], skip: int = 0, limit: int = 100
    ) -> Tuple[List[Level], int]:
        """
        Отримує список рівнів для вказаної групи (або глобальні, якщо group_id=None) з пагінацією.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            group_id (Optional[int]): ID групи або None для глобальних рівнів.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[Level], int]: Кортеж зі списком рівнів та їх загальною кількістю.
        """
        logger.debug(
            f"Отримання рівнів для group_id: {'глобальні' if group_id is None else group_id}, "
            f"skip: {skip}, limit: {limit}"
        )
        filters_dict: Dict[str, Any] = {"group_id": group_id}

        # TODO: [Сортування] BaseRepository.get_multi наразі підтримує сортування лише за одним полем.
        #       Початковий запит був `order_by = [self.model.level_number.asc(), self.model.required_points.asc()]`.
        #       Наразі сортуємо за `level_number`. Розглянути розширення BaseRepository для мульти-сортування.
        sort_by_field = "level_number"
        sort_order_str = "asc"

        try:
            items = await super().get_multi(
                session=session,
                skip=skip,
                limit=limit,
                filters=filters_dict,
                sort_by=sort_by_field,
                sort_order=sort_order_str
            )
            total_count = await super().count(session=session, filters=filters_dict)
            logger.debug(f"Знайдено {total_count} рівнів для group_id: {'глобальні' if group_id is None else group_id}")
            return items, total_count
        except Exception as e:
            logger.error(
                f"Помилка при отриманні рівнів для group_id "
                f"{'глобальні' if group_id is None else group_id}: {e}",
                exc_info=True
            )
            return [], 0

    async def get_level_by_number(
            self, session: AsyncSession, level_number: int, group_id: Optional[int] = None
    ) -> Optional[Level]:
        """
        Отримує рівень за його порядковим номером у вказаній групі (або глобальний).

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            level_number (int): Порядковий номер рівня.
            group_id (Optional[int]): ID групи або None для глобальних рівнів.

        Returns:
            Optional[Level]: Екземпляр моделі `Level`, якщо знайдено, інакше None.
        """
        logger.debug(
            f"Отримання рівня за номером: {level_number}, group_id: {'глобальний' if group_id is None else group_id}"
        )
        stmt = select(self.model).where(
            self.model.group_id == group_id,
            self.model.level_number == level_number
        )
        try:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Помилка при отриманні рівня за номером {level_number}, "
                f"group_id {'глобальний' if group_id is None else group_id}: {e}",
                exc_info=True
            )
            return None

    async def get_level_by_points(
            self, session: AsyncSession, points: int, group_id: Optional[int] = None
    ) -> Optional[Level]:
        """
        Визначає рівень, якому відповідає задана кількість балів, у вказаній групі (або глобальний).
        Повертає найвищий досягнутий рівень.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            points (int): Кількість балів.
            group_id (Optional[int]): ID групи або None для глобальних рівнів.

        Returns:
            Optional[Level]: Екземпляр моделі `Level`, якщо знайдено, інакше None.
        """
        logger.debug(
            f"Отримання рівня за балами: {points}, group_id: {'глобальний' if group_id is None else group_id}"
        )
        stmt = (
            select(self.model)
            .where(
                self.model.group_id == group_id,
                self.model.required_points <= points
            )
            .order_by(self.model.required_points.desc(), self.model.level_number.desc())
        )
        try:
            result = await session.execute(stmt)
            return result.scalars().first() # Повертає перший результат або None, якщо нічого не знайдено
        except Exception as e:
            logger.error(
                f"Помилка при отриманні рівня за балами {points}, "
                f"group_id {'глобальний' if group_id is None else group_id}: {e}",
                exc_info=True
            )
            return None


if __name__ == "__main__":
    # Демонстраційний блок для LevelRepository.
    logger.info("--- Репозиторій Рівнів Гейміфікації (LevelRepository) ---")

    logger.info("Для тестування LevelRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    logger.info(f"Він успадковує методи від BaseRepository для моделі {Level.__name__}.")
    logger.info(f"  Очікує схему створення: {LevelCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {LevelUpdateSchema.__name__}")

    logger.info("\nСпецифічні методи:")
    logger.info("  - get_levels_by_group_id(group_id: Optional[int], skip: int = 0, limit: int = 100)")
    logger.info("  - get_level_by_number(group_id: Optional[int], level_number: int)")
    logger.info("  - get_level_by_points(group_id: Optional[int], points: int)")

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
