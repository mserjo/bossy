# backend/app/src/repositories/gamification/badge_repository.py
"""
Репозиторій для моделі "Бейдж" (Badge) в системі гейміфікації.

Цей модуль визначає клас `BadgeRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з бейджами (значками досягнень).
"""

from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.gamification.badge import Badge
from backend.app.src.schemas.gamification.badge import BadgeCreateSchema, BadgeUpdateSchema
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)


class BadgeRepository(BaseRepository[Badge, BadgeCreateSchema, BadgeUpdateSchema]):
    """
    Репозиторій для управління бейджами (`Badge`).

    Успадковує базові CRUD-методи від `BaseRepository` та може містити
    додаткові методи для отримання бейджів за ID групи або іншими критеріями.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `Badge`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=Badge)

    async def get_badges_by_group_id(
            self,
            group_id: Optional[int],  # None для глобальних бейджів
            active_only: bool = True,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[Badge], int]:
        """
        Отримує список бейджів для вказаної групи (або глобальні, якщо group_id=None) з пагінацією.

        Args:
            group_id (Optional[int]): ID групи або None для глобальних/системних бейджів.
            active_only (bool): Якщо True, повертає лише активні бейджі (state='active').
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[Badge], int]: Кортеж зі списком бейджів та їх загальною кількістю.
        """
        filters = [self.model.group_id == group_id]
        if active_only:
            # Модель Badge успадковує BaseMainModel, яке має поле 'state' через StateMixin.
            # Припускаємо, що активний стан позначається як "active".
            # TODO: Узгодити значення "active" з можливим Enum для станів.
            if hasattr(self.model, "state"):
                filters.append(self.model.state == "active")
            # else:
            # logger.warning(f"Модель {self.model.__name__} не має поля 'state' для фільтрації активних бейджів.")

        order_by = [self.model.name.asc()]  # Сортувати за назвою
        return await self.get_multi(skip=skip, limit=limit, filters=filters, order_by=order_by)

    # Тут можна додати інші специфічні методи, наприклад, пошук бейджів за тегами,
    # якщо б модель Badge мала поле для тегів.


if __name__ == "__main__":
    # Демонстраційний блок для BadgeRepository.
    logger.info("--- Репозиторій Бейджів Гейміфікації (BadgeRepository) ---")

    logger.info("Для тестування BadgeRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    logger.info(f"Він успадковує методи від BaseRepository для моделі {Badge.__name__}.")
    logger.info(f"  Очікує схему створення: {BadgeCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {BadgeUpdateSchema.__name__}")

    logger.info("\nСпецифічні методи:")
    logger.info(
        "  - get_badges_by_group_id(group_id: Optional[int], active_only: bool = True, skip: int = 0, limit: int = 100)")

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
    logger.info("TODO: Узгодити логіку фільтрації 'active_only' з реальним полем/Enum стану в моделі Badge.")
