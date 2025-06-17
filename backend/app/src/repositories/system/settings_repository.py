# backend/app/src/repositories/system/settings_repository.py
"""
Репозиторій для моделі "Системне Налаштування" (SystemSetting).

Цей модуль визначає клас `SystemSettingRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з системними налаштуваннями,
наприклад, отримання налаштування за його унікальним ключем.
"""

from typing import List, Optional, Tuple, Any, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.system.settings import SystemSetting
from backend.app.src.schemas.system.settings import SystemSettingCreateSchema, SystemSettingUpdateSchema
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


class SystemSettingRepository(BaseRepository[SystemSetting, SystemSettingCreateSchema, SystemSettingUpdateSchema]):
    """
    Репозиторій для управління системними налаштуваннями (`SystemSetting`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи для отримання налаштувань за ключем та тих, що можна редагувати.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `SystemSetting`.
        """
        super().__init__(model=SystemSetting)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_by_key(self, session: AsyncSession, key: str) -> Optional[SystemSetting]:
        """
        Отримує запис системного налаштування за його унікальним програмним ключем.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            key (str): Унікальний ключ налаштування.

        Returns:
            Optional[SystemSetting]: Екземпляр моделі `SystemSetting`, якщо знайдено, інакше None.
        """
        logger.debug(f"Отримання SystemSetting за ключем: {key}")
        stmt = select(self.model).where(self.model.key == key)
        try:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Помилка при отриманні SystemSetting за ключем {key}: {e}", exc_info=True)
            return None

    async def get_editable_settings(
            self, session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Tuple[List[SystemSetting], int]:
        """
        Отримує список системних налаштувань, які позначені як редаговані, з пагінацією.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[SystemSetting], int]: Кортеж зі списком налаштувань та їх загальною кількістю.
        """
        logger.debug(f"Отримання редагованих налаштувань, skip: {skip}, limit: {limit}")
        filters_dict: Dict[str, Any] = {"is_editable": True}
        sort_by_field = "name"
        sort_order_str = "asc"  # Сортувати за людиночитаною назвою

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
            logger.debug(f"Знайдено {total_count} редагованих налаштувань.")
            return items, total_count
        except Exception as e:
            logger.error(f"Помилка при отриманні редагованих налаштувань: {e}", exc_info=True)
            return [], 0


if __name__ == "__main__":
    # Демонстраційний блок для SystemSettingRepository.
    logger.info("--- Репозиторій Системних Налаштувань (SystemSettingRepository) ---")

    logger.info("Для тестування SystemSettingRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    logger.info(f"Він успадковує методи від BaseRepository для моделі {SystemSetting.__name__}.")
    logger.info(f"  Очікує схему створення: {SystemSettingCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {SystemSettingUpdateSchema.__name__}")

    logger.info("\nСпецифічні методи:")
    logger.info("  - get_by_key(key: str)")
    logger.info("  - get_editable_settings(skip: int = 0, limit: int = 100)")

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
