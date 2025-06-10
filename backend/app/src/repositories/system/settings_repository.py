# backend/app/src/repositories/system/settings_repository.py
"""
Репозиторій для моделі "Системне Налаштування" (SystemSetting).

Цей модуль визначає клас `SystemSettingRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з системними налаштуваннями,
наприклад, отримання налаштування за його унікальним ключем.
"""

from typing import List, Optional, Tuple, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.system.settings import SystemSetting
from backend.app.src.schemas.system.settings import SystemSettingCreateSchema, SystemSettingUpdateSchema


# from backend.app.src.config.logging import get_logger # Якщо потрібне логування

# logger = get_logger(__name__)

class SystemSettingRepository(BaseRepository[SystemSetting, SystemSettingCreateSchema, SystemSettingUpdateSchema]):
    """
    Репозиторій для управління системними налаштуваннями (`SystemSetting`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи для отримання налаштувань за ключем та тих, що можна редагувати.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `SystemSetting`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=SystemSetting)

    async def get_by_key(self, key: str) -> Optional[SystemSetting]:
        """
        Отримує запис системного налаштування за його унікальним програмним ключем.

        Args:
            key (str): Унікальний ключ налаштування.

        Returns:
            Optional[SystemSetting]: Екземпляр моделі `SystemSetting`, якщо знайдено, інакше None.
        """
        stmt = select(self.model).where(self.model.key == key)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_editable_settings(self, skip: int = 0, limit: int = 100) -> Tuple[List[SystemSetting], int]:
        """
        Отримує список системних налаштувань, які позначені як редаговані, з пагінацією.

        Args:
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[SystemSetting], int]: Кортеж зі списком налаштувань та їх загальною кількістю.
        """
        filters = [self.model.is_editable == True]
        order_by = [self.model.name.asc()]  # Сортувати за людиночитаною назвою
        return await self.get_multi(skip=skip, limit=limit, filters=filters, order_by=order_by)


if __name__ == "__main__":
    # Демонстраційний блок для SystemSettingRepository.
    print("--- Репозиторій Системних Налаштувань (SystemSettingRepository) ---")

    print("Для тестування SystemSettingRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    print(f"Він успадковує методи від BaseRepository для моделі {SystemSetting.__name__}.")
    print(f"  Очікує схему створення: {SystemSettingCreateSchema.__name__}")
    print(f"  Очікує схему оновлення: {SystemSettingUpdateSchema.__name__}")

    print("\nСпецифічні методи:")
    print("  - get_by_key(key: str)")
    print("  - get_editable_settings(skip: int = 0, limit: int = 100)")

    print("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
