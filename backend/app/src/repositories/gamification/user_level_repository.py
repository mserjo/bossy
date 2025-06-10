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
from backend.app.src.models.gamification.level import Level  # Для join в get_by_user_and_group
from backend.app.src.schemas.gamification.user_level import UserLevelCreateSchema


# from backend.app.src.config.logging import get_logger # Якщо потрібне логування

# logger = get_logger(__name__)

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

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `UserLevel`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=UserLevel)

    async def get_current_level_for_user_in_group(self, user_id: int, group_id: int) -> Optional[UserLevel]:
        """
        Отримує поточний (найвищий досягнутий) рівень для користувача в конкретній групі.

        Args:
            user_id (int): ID користувача.
            group_id (int): ID групи.

        Returns:
            Optional[UserLevel]: Екземпляр `UserLevel`, що представляє найвищий
                                 досягнутий рівень, або None, якщо рівнів не досягнуто.
        """
        stmt = (
            select(self.model)
            .join(Level, self.model.level_id == Level.id)  # Приєднуємо Level для сортування за level_number
            .where(
                self.model.user_id == user_id,
                self.model.group_id == group_id
            )
            # Сортуємо за level_number у спадаючому порядку, щоб перший результат був найвищим рівнем.
            # Також можна сортувати за required_points, якщо level_number не завжди послідовний.
            .order_by(Level.level_number.desc(), Level.required_points.desc(), self.model.created_at.desc())
        )
        result = await self.db_session.execute(stmt)
        return result.scalars().first()  # Повертає перший (найвищий) або None

    async def get_all_achieved_levels_for_user_in_group(
            self,
            user_id: int,
            group_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[UserLevel], int]:
        """
        Отримує список всіх рівнів, досягнутих користувачем у конкретній групі, з пагінацією.
        Корисно для перегляду історії досягнень рівнів.

        Args:
            user_id (int): ID користувача.
            group_id (int): ID групи.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[UserLevel], int]: Кортеж зі списком досягнутих рівнів та їх загальною кількістю.
        """
        filters = [
            self.model.user_id == user_id,
            self.model.group_id == group_id
        ]
        # Сортування за часом досягнення (новіші перші) або за номером рівня
        order_by = [self.model.created_at.desc()]
        # options = [selectinload(self.model.level), selectinload(self.model.user)]
        return await self.get_multi(skip=skip, limit=limit, filters=filters, order_by=order_by)  # , options=options)


if __name__ == "__main__":
    # Демонстраційний блок для UserLevelRepository.
    print("--- Репозиторій Рівнів Користувача (UserLevelRepository) ---")

    print("Для тестування UserLevelRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    print(f"Він успадковує методи від BaseRepository для моделі {UserLevel.__name__}.")
    print(f"  Очікує схему створення: {UserLevelCreateSchema.__name__}")
    print(f"  Очікує схему оновлення: {UserLevelUpdateSchema.__name__} (зараз порожня)")

    print("\nСпецифічні методи:")
    print("  - get_current_level_for_user_in_group(user_id: int, group_id: int) -> Optional[UserLevel]")
    print("  - get_all_achieved_levels_for_user_in_group(user_id: int, group_id: int, skip: int = 0, limit: int = 100)")

    print("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
