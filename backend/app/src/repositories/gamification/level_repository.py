# backend/app/src/repositories/gamification/level_repository.py
"""
Репозиторій для моделі "Рівень" (Level) в системі гейміфікації.

Цей модуль визначає клас `LevelRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з рівнями гейміфікації,
наприклад, отримання рівнів для конкретної групи або за номером рівня.
"""

from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.gamification.level import Level
from backend.app.src.schemas.gamification.level import LevelCreateSchema, LevelUpdateSchema


# from backend.app.src.config.logging import get_logger # Якщо потрібне логування

# logger = get_logger(__name__)

class LevelRepository(BaseRepository[Level, LevelCreateSchema, LevelUpdateSchema]):
    """
    Репозиторій для управління рівнями гейміфікації (`Level`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи для отримання рівнів за ID групи або за номером рівня в групі.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `Level`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=Level)

    async def get_levels_by_group_id(self, group_id: Optional[int], skip: int = 0, limit: int = 100) -> Tuple[
        List[Level], int]:
        """
        Отримує список рівнів для вказаної групи (або глобальні, якщо group_id=None) з пагінацією.

        Args:
            group_id (Optional[int]): ID групи або None для глобальних рівнів.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[Level], int]: Кортеж зі списком рівнів та їх загальною кількістю.
        """
        filters = [self.model.group_id == group_id]
        order_by = [self.model.level_number.asc(), self.model.required_points.asc()]
        return await self.get_multi(skip=skip, limit=limit, filters=filters, order_by=order_by)

    async def get_level_by_number(self, level_number: int, group_id: Optional[int] = None) -> Optional[Level]:
        """
        Отримує рівень за його порядковим номером у вказаній групі (або глобальний).

        Args:
            level_number (int): Порядковий номер рівня.
            group_id (Optional[int]): ID групи або None для глобальних рівнів.


        Returns:
            Optional[Level]: Екземпляр моделі `Level`, якщо знайдено, інакше None.
        """
        stmt = select(self.model).where(
            self.model.group_id == group_id,  # Працює і для group_id IS NULL
            self.model.level_number == level_number
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_level_by_points(self, points: int, group_id: Optional[int] = None) -> Optional[Level]:
        """
        Визначає рівень, якому відповідає задана кількість балів, у вказаній групі (або глобальний).
        Повертає найвищий досягнутий рівень.

        Args:
            points (int): Кількість балів.
            group_id (Optional[int]): ID групи або None для глобальних рівнів.

        Returns:
            Optional[Level]: Екземпляр моделі `Level`, якщо знайдено, інакше None.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.group_id == group_id,
                self.model.required_points <= points
            )
            .order_by(self.model.required_points.desc(), self.model.level_number.desc())  # Найвищий підходящий рівень
        )
        result = await self.db_session.execute(stmt)
        return result.scalars().first()


if __name__ == "__main__":
    # Демонстраційний блок для LevelRepository.
    print("--- Репозиторій Рівнів Гейміфікації (LevelRepository) ---")

    print("Для тестування LevelRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    print(f"Він успадковує методи від BaseRepository для моделі {Level.__name__}.")
    print(f"  Очікує схему створення: {LevelCreateSchema.__name__}")
    print(f"  Очікує схему оновлення: {LevelUpdateSchema.__name__}")

    print("\nСпецифічні методи:")
    print("  - get_levels_by_group_id(group_id: Optional[int], skip: int = 0, limit: int = 100)")
    print("  - get_level_by_number(group_id: Optional[int], level_number: int)")
    print("  - get_level_by_points(group_id: Optional[int], points: int)")

    print("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
