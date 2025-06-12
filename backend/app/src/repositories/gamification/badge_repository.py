# backend/app/src/repositories/gamification/badge_repository.py
"""
Репозиторій для моделі "Бейдж" (Badge) в системі гейміфікації.

Цей модуль визначає клас `BadgeRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з бейджами (значками досягнень).
"""

from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession # Для type hinting у кастомних методах

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.gamification.badge import Badge
from backend.app.src.schemas.gamification.badge import BadgeCreateSchema, BadgeUpdateSchema
from backend.app.src.config import logger # Використання спільного логера


class BadgeRepository(BaseRepository[Badge, BadgeCreateSchema, BadgeUpdateSchema]):
    """
    Репозиторій для управління бейджами (`Badge`).

    Успадковує базові CRUD-методи від `BaseRepository` та може містити
    додаткові методи для отримання бейджів за ID групи або іншими критеріями.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `Badge`.
        """
        super().__init__(model=Badge)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_badges_by_group_id(
            self,
            session: AsyncSession,
            group_id: Optional[int],  # None для глобальних бейджів
            active_only: bool = True,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[Badge], int]:
        """
        Отримує список бейджів для вказаної групи (або глобальні, якщо group_id=None) з пагінацією.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            group_id (Optional[int]): ID групи або None для глобальних/системних бейджів.
            active_only (bool): Якщо True, повертає лише активні бейджі.
                                # TODO: [Перевірка Поля Стану] Узгодити з `technical_task.txt` / `structure-claude-v2.md`
                                #       наявність та значення поля стану (напр., `state="active"`).
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[Badge], int]: Кортеж зі списком бейджів та їх загальною кількістю.
        """
        logger.debug(
            f"Отримання бейджів для group_id: {'глобальні' if group_id is None else group_id}, "
            f"active_only: {active_only}, skip: {skip}, limit: {limit}"
        )
        filters_dict: Dict[str, Any] = {"group_id": group_id}

        if active_only:
            # Модель Badge успадковує BaseMainModel, яке має поле 'state' через StateMixin.
            # Припускаємо, що активний стан позначається як "active".
            # TODO: [Визначення Активного Стану] Уточнити значення для активного стану ("active", True, etc.)
            #       згідно з `technical_task.txt` / моделлю даних.
            if hasattr(self.model, "state"):
                filters_dict["state"] = "active"
            else:
                logger.warning(
                    f"Модель {self.model.__name__} не має поля 'state' для фільтрації активних бейджів. "
                    "Фільтр active_only не буде застосовано."
                )

        sort_by_field = "name"
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
            logger.debug(f"Знайдено {total_count} бейджів для group_id: {'глобальні' if group_id is None else group_id}")
            return items, total_count
        except Exception as e:
            logger.error(
                f"Помилка при отриманні бейджів для group_id "
                f"{'глобальні' if group_id is None else group_id}: {e}",
                exc_info=True
            )
            return [], 0

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
