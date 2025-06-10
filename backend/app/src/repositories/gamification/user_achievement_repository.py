# /backend/app/src/repositories/gamification/user_achievement_repository.py
"""
Репозиторій для моделі "Досягнення Користувача" (UserAchievement).

Цей модуль визначає клас `UserAchievementRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з записами про отримання користувачами
бейджиків (досягнень).
"""

from typing import List, Optional, Tuple, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import selectinload

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.gamification.user_achievement import UserAchievement
from backend.app.src.schemas.gamification.achievement import (
    UserAchievementCreateSchema,
    # UserAchievementUpdateSchema зазвичай не потрібна, досягнення не змінюються
)
from pydantic import BaseModel as PydanticBaseModel  # Для UpdateSchemaType


# from backend.app.src.config.logging import get_logger # Якщо потрібне логування

# logger = get_logger(__name__)

# Досягнення зазвичай не оновлюються, а видаляються та створюються заново, якщо потрібно коригування.
class UserAchievementUpdateSchema(PydanticBaseModel):
    pass


class UserAchievementRepository(
    BaseRepository[UserAchievement, UserAchievementCreateSchema, UserAchievementUpdateSchema]):
    """
    Репозиторій для управління записами про досягнення користувачів (`UserAchievement`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи для отримання досягнень за користувачем, бейджем та групою.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `UserAchievement`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=UserAchievement)

    async def get_by_user_and_badge(
            self,
            user_id: int,
            badge_id: int,
            group_id: Optional[int] = None
    ) -> Optional[UserAchievement]:
        """
        Отримує запис про досягнення за ID користувача, ID бейджа та опціонально ID групи.
        Це корисно для перевірки, чи користувач вже має певний бейдж (у певному контексті групи).

        Args:
            user_id (int): ID користувача.
            badge_id (int): ID бейджа.
            group_id (Optional[int]): ID групи, якщо досягнення контекстно-залежне від групи.
                                      None для глобальних досягнень.

        Returns:
            Optional[UserAchievement]: Екземпляр моделі `UserAchievement`, якщо знайдено, інакше None.
        """
        filters = [
            self.model.user_id == user_id,
            self.model.badge_id == badge_id
        ]
        if group_id is not None:
            filters.append(self.model.group_id == group_id)
        else:
            filters.append(self.model.group_id.is_(None))  # Явна перевірка на NULL для глобальних

        stmt = select(self.model).where(*filters)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()  # UniqueConstraint має гарантувати не більше одного

    async def get_achievements_for_user(
            self,
            user_id: int,
            group_id: Optional[int] = None,  # Фільтр за конкретною групою
            include_global: bool = True,  # Чи включати глобальні досягнення (group_id IS NULL)
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[UserAchievement], int]:
        """
        Отримує список всіх досягнень (бейджиків) для вказаного користувача з пагінацією.
        Може фільтруватися за конкретною групою та/або включати глобальні досягнення.

        Args:
            user_id (int): ID користувача.
            group_id (Optional[int]): ID групи для фільтрації. Якщо None, і `include_global`=True,
                                      може повертати досягнення з різних груп або лише глобальні.
                                      Якщо вказано, `include_global` ігнорується для цього group_id.
            include_global (bool): Якщо True і group_id не вказано, включає глобальні досягнення.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[UserAchievement], int]: Кортеж зі списком досягнень та їх загальною кількістю.
        """
        filters = [self.model.user_id == user_id]
        if group_id is not None:
            filters.append(self.model.group_id == group_id)
        elif include_global:  # group_id is None and we want global achievements
            filters.append(self.model.group_id.is_(None))
        # Якщо group_id is None і include_global is False, то поверне лише ті, де group_id є NULL (якщо такі є),
        # або нічого, якщо всі досягнення прив'язані до груп. Логіка може потребувати уточнення.

        order_by = [self.model.created_at.desc()]  # Показувати новіші досягнення першими
        # options = [selectinload(self.model.badge), selectinload(self.model.group)]
        return await self.get_multi(skip=skip, limit=limit, filters=filters, order_by=order_by)  # , options=options)


if __name__ == "__main__":
    # Демонстраційний блок для UserAchievementRepository.
    print("--- Репозиторій Досягнень Користувача (UserAchievementRepository) ---")

    print("Для тестування UserAchievementRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    print(f"Він успадковує методи від BaseRepository для моделі {UserAchievement.__name__}.")
    print(f"  Очікує схему створення: {UserAchievementCreateSchema.__name__}")
    print(f"  Очікує схему оновлення: {UserAchievementUpdateSchema.__name__} (зараз порожня)")

    print("\nСпецифічні методи:")
    print("  - get_by_user_and_badge(user_id: int, badge_id: int, group_id: Optional[int] = None)")
    print(
        "  - get_achievements_for_user(user_id: int, group_id: Optional[int] = None, include_global: bool = True, skip: int = 0, limit: int = 100)")

    print("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
