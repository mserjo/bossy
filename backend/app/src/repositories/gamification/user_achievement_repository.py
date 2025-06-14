# backend/app/src/repositories/gamification/user_achievement_repository.py
"""
Репозиторій для моделі "Досягнення Користувача" (UserAchievement).

Цей модуль визначає клас `UserAchievementRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з записами про отримання користувачами
бейджиків (досягнень).
"""

from typing import List, Optional, Tuple, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.gamification.user_achievement import UserAchievement
from backend.app.src.schemas.gamification.achievement import UserAchievementCreateSchema
# UserAchievementUpdateSchema зазвичай не потрібна, досягнення не змінюються
from pydantic import BaseModel as PydanticBaseModel  # Для UpdateSchemaType
from backend.app.src.config.logging import get_logger # Стандартизований імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)


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

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `UserAchievement`.
        """
        super().__init__(model=UserAchievement)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_by_user_and_badge(
            self,
            session: AsyncSession,
            user_id: int,
            badge_id: int,
            group_id: Optional[int] = None
    ) -> Optional[UserAchievement]:
        """
        Отримує запис про досягнення за ID користувача, ID бейджа та опціонально ID групи.
        Це корисно для перевірки, чи користувач вже має певний бейдж (у певному контексті групи).

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            user_id (int): ID користувача.
            badge_id (int): ID бейджа.
            group_id (Optional[int]): ID групи, якщо досягнення контекстно-залежне від групи.
                                      None для глобальних досягнень.

        Returns:
            Optional[UserAchievement]: Екземпляр моделі `UserAchievement`, якщо знайдено, інакше None.
        """
        logger.debug(
            f"Отримання UserAchievement для user_id {user_id}, badge_id {badge_id}, "
            f"group_id: {'глобальне' if group_id is None else group_id}"
        )
        conditions = [
            self.model.user_id == user_id,
            self.model.badge_id == badge_id
        ]
        if group_id is not None:
            conditions.append(self.model.group_id == group_id)
        else:
            conditions.append(self.model.group_id.is_(None))

        stmt = select(self.model).where(*conditions)
        try:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Помилка при отриманні UserAchievement для user_id {user_id}, badge_id {badge_id}: {e}",
                exc_info=True
            )
            return None

    async def get_achievements_for_user(
            self,
            session: AsyncSession,
            user_id: int,
            group_id: Optional[int] = None,
            include_global: bool = True,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[UserAchievement], int]:
        """
        Отримує список всіх досягнень (бейджиків) для вказаного користувача з пагінацією.
        Може фільтруватися за конкретною групою та/або включати глобальні досягнення.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            user_id (int): ID користувача.
            group_id (Optional[int]): ID групи для фільтрації. Якщо None, і `include_global`=True,
                                      поверне глобальні досягнення (group_id IS NULL).
                                      Якщо вказано, `include_global` ігнорується для цього group_id.
            include_global (bool): Якщо True і group_id не вказано, включає глобальні досягнення.
                                   Якщо False і group_id не вказано, поверне порожній список (або помилку, залежно від логіки).
                                   Поточна логіка: якщо group_id is None and include_global is False, то фільтр group_id не застосовується,
                                   що поверне досягнення з усіх груп. Це може потребувати уточнення.
                                   Пропонується: якщо group_id is None and include_global is False, то не шукати нічого або лише ті, де group_id НЕ NULL.
                                   Поки що, якщо group_id is None and include_global is False, то фільтр по group_id не додається.
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[UserAchievement], int]: Кортеж зі списком досягнень та їх загальною кількістю.
        """
        logger.debug(
            f"Отримання досягнень для user_id {user_id}, group_id: {group_id}, "
            f"include_global: {include_global}, skip: {skip}, limit: {limit}"
        )
        filters_dict: Dict[str, Any] = {"user_id": user_id}

        if group_id is not None:
            filters_dict["group_id"] = group_id
        elif include_global:  # group_id is None and we want global achievements
            filters_dict["group_id"] = None # Явна перевірка на NULL
        # else: # group_id is None and include_global is False - не додаємо фільтр по group_id,
                # що означає "всі досягнення користувача у всіх групах" + глобальні, якщо вони без group_id.
                # Якщо потрібно строго "лише в групах, не глобальні", потрібен фільтр group_id.isnot(None).
                # Поточна логіка get_multi не підтримує isnot(None) напряму через dict.
                # Для такої логіки краще використовувати прямий запит SQLAlchemy.
                # Залишаємо як є: якщо group_id не заданий і include_global=False, то фільтра по group_id немає.

        sort_by_field = "created_at"
        sort_order_str = "desc"  # Новіші досягнення першими

        # options = [selectinload(self.model.badge), selectinload(self.model.group)] # для передачі в get_multi
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
            logger.debug(f"Знайдено {total_count} досягнень для user_id {user_id} з заданими фільтрами.")
            return items, total_count
        except Exception as e:
            logger.error(
                f"Помилка при отриманні досягнень для user_id {user_id}: {e}",
                exc_info=True
            )
            return [], 0


if __name__ == "__main__":
    # Демонстраційний блок для UserAchievementRepository.
    logger.info("--- Репозиторій Досягнень Користувача (UserAchievementRepository) ---")

    logger.info("Для тестування UserAchievementRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    logger.info(f"Він успадковує методи від BaseRepository для моделі {UserAchievement.__name__}.")
    logger.info(f"  Очікує схему створення: {UserAchievementCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {UserAchievementUpdateSchema.__name__} (зараз порожня)")

    logger.info("\nСпецифічні методи:")
    logger.info("  - get_by_user_and_badge(user_id: int, badge_id: int, group_id: Optional[int] = None)")
    logger.info(
        "  - get_achievements_for_user(user_id: int, group_id: Optional[int] = None, include_global: bool = True, skip: int = 0, limit: int = 100)")

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
