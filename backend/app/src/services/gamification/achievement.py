# backend/app/src/services/gamification/achievement.py
# import logging # Замінено на централізований логер
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, noload
from sqlalchemy.exc import IntegrityError

from backend.app.src.services.base import BaseService # Повний шлях
from backend.app.src.models.gamification.achievement import UserAchievement # Модель SQLAlchemy UserAchievement
from backend.app.src.models.gamification.badge import Badge # Для контексту Badge
from backend.app.src.models.auth.user import User # Для контексту User
from backend.app.src.models.groups.group import Group # Якщо досягнення контекстно-залежні від групи

from backend.app.src.schemas.gamification.achievement import ( # Схеми Pydantic
    UserAchievementCreate, # Схема для нагородження досягненням
    UserAchievementResponse
)
from backend.app.src.config.logging import logger # Централізований логер
from backend.app.src.config import settings # Для доступу до конфігурацій (наприклад, DEBUG)

class UserAchievementService(BaseService):
    """
    Сервіс для управління досягненнями користувачів (нагородження користувачів значками-бейджами).
    Обробляє створення та отримання записів UserAchievement.
    Досягнення представляють собою зв'язок між користувачем (User) та значком (Badge),
    який він отримав, можливо, в контексті певної групи та з додатковими деталями.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("UserAchievementService ініціалізовано.")

    async def _get_orm_user_achievement_by_id(self, achievement_id: UUID) -> Optional[UserAchievement]:
        """Внутрішній метод для отримання ORM моделі UserAchievement з усіма зв'язками."""
        stmt = select(UserAchievement).options(
            selectinload(UserAchievement.user).options(selectinload(User.user_type)),
            selectinload(UserAchievement.badge), # Завантажуємо повний об'єкт Badge
            selectinload(UserAchievement.group), # Завантажуємо повний об'єкт Group, якщо є
            selectinload(UserAchievement.awarded_by).options(selectinload(User.user_type)) # Ким видано
        ).where(UserAchievement.id == achievement_id)
        return (await self.db_session.execute(stmt)).scalar_one_or_none()


    async def award_achievement_to_user(
        self,
        user_id: UUID,
        badge_id: UUID,
        achievement_data: UserAchievementCreate, # Містить context_details, group_id
        awarded_by_user_id: Optional[UUID] = None # Хто видає (наприклад, адмін або система)
    ) -> UserAchievementResponse:
        """
        Нагороджує користувача досягненням (бейджем).

        :param user_id: ID користувача, якому надається досягнення.
        :param badge_id: ID бейджа, що надається.
        :param achievement_data: Дані для створення запису UserAchievement (контекст, група).
        :param awarded_by_user_id: ID користувача, який нагородив (якщо застосовно).
        :return: Pydantic схема UserAchievementResponse.
        :raises ValueError: Якщо користувача, бейдж, або групу не знайдено, або бейдж не повторюваний і вже є. # i18n
        """
        log_ctx_parts = [f"користувач ID '{user_id}'", f"бейдж ID '{badge_id}'"]
        if achievement_data.group_id:
            log_ctx_parts.append(f"група ID '{achievement_data.group_id}'")
        log_ctx = ", ".join(log_ctx_parts)
        logger.debug(f"Спроба нагородження досягненням: {log_ctx}.")

        user = await self.db_session.get(User, user_id)
        if not user:
            # i18n
            raise ValueError(f"Користувача з ID '{user_id}' не знайдено.")

        badge = await self.db_session.get(Badge, badge_id)
        if not badge:
            # i18n
            raise ValueError(f"Бейдж з ID '{badge_id}' не знайдено.")

        # Перевірка групи, якщо group_id надано в achievement_data
        if achievement_data.group_id:
            group = await self.db_session.get(Group, achievement_data.group_id)
            if not group:
                # i18n
                raise ValueError(f"Групу з ID '{achievement_data.group_id}' не знайдено.")

        # Перевірка, чи бейдж є повторюваним
        if not badge.is_repeatable:
            existing_achievement_stmt = select(UserAchievement.id).where(
                UserAchievement.user_id == user_id,
                UserAchievement.badge_id == badge_id
            )
            if achievement_data.group_id: # Якщо досягнення в контексті групи
                existing_achievement_stmt = existing_achievement_stmt.where(UserAchievement.group_id == achievement_data.group_id)
            else: # Якщо досягнення глобальне
                existing_achievement_stmt = existing_achievement_stmt.where(UserAchievement.group_id.is_(None))

            if (await self.db_session.execute(existing_achievement_stmt)).scalar_one_or_none():
                msg = f"Бейдж '{badge.name}' (ID: {badge_id}) вже було надано цьому користувачеві в даному контексті і він не є повторюваним." # i18n
                logger.warning(msg)
                raise ValueError(msg)

        # Створення запису UserAchievement
        # `achieved_at` встановлюється автоматично моделлю
        new_achievement_db = UserAchievement(
            user_id=user_id,
            badge_id=badge_id,
            group_id=achievement_data.group_id, # Може бути None
            context_details=achievement_data.context_details,
            awarded_by_user_id=awarded_by_user_id
            # `created_at` та `updated_at` (якщо є в моделі) встановлюються автоматично
        )

        self.db_session.add(new_achievement_db)
        try:
            await self.commit()
            # Отримуємо повний об'єкт для відповіді
            refreshed_achievement = await self._get_orm_user_achievement_by_id(new_achievement_db.id)
            if not refreshed_achievement: # Малоймовірно
                logger.critical(f"Не вдалося отримати щойно створене досягнення ID {new_achievement_db.id} після коміту.")
                # i18n
                raise RuntimeError("Критична помилка: не вдалося отримати запис досягнення після збереження.")
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності при нагородженні ({log_ctx}): {e}", exc_info=settings.DEBUG)
            # i18n
            raise ValueError(f"Не вдалося нагородити досягненням через конфлікт даних: {e}")

        logger.info(f"Досягнення (Бейдж ID: '{badge_id}') успішно надано користувачу ID '{user_id}'. ID Запису: {refreshed_achievement.id}")
        return UserAchievementResponse.model_validate(refreshed_achievement) # Pydantic v2

    async def get_user_achievement_by_id(self, achievement_id: UUID) -> Optional[UserAchievementResponse]:
        """Отримує конкретний запис про нагородження досягненням за його ID."""
        logger.debug(f"Спроба отримання запису досягнення за ID: {achievement_id}")

        achievement_db = await self._get_orm_user_achievement_by_id(achievement_id)
        if achievement_db:
            logger.info(f"Запис досягнення з ID '{achievement_id}' знайдено.")
            return UserAchievementResponse.model_validate(achievement_db) # Pydantic v2

        logger.info(f"Запис досягнення з ID '{achievement_id}' не знайдено.")
        return None

    async def list_achievements_for_user(
        self,
        user_id: UUID,
        group_id: Optional[UUID] = None, # Фільтр за ID групи
        filter_global_only: bool = False, # Якщо True і group_id не вказано, показує тільки глобальні
        skip: int = 0,
        limit: int = 100
    ) -> List[UserAchievementResponse]:
        """
        Перелічує досягнення для вказаного користувача.
        Може фільтрувати за групою або показувати тільки глобальні досягнення.
        """
        log_ctx_parts = [f"користувач ID '{user_id}'"]
        if group_id: log_ctx_parts.append(f"група ID '{group_id}'")
        if filter_global_only and not group_id: log_ctx_parts.append("тільки глобальні")
        log_ctx = ", ".join(log_ctx_parts)
        logger.debug(f"Перелік досягнень для {log_ctx}, пропустити={skip}, ліміт={limit}")

        stmt = select(UserAchievement).options(
            selectinload(UserAchievement.user).options(noload("*")), # Уникаємо завантаження всього користувача, тільки ID
            selectinload(UserAchievement.badge),
            selectinload(UserAchievement.group),
            selectinload(UserAchievement.awarded_by).options(noload("*"))
        ).where(UserAchievement.user_id == user_id)

        if group_id is not None:
            stmt = stmt.where(UserAchievement.group_id == group_id)
        elif filter_global_only: # group_id не вказано, але потрібні тільки глобальні
            stmt = stmt.where(UserAchievement.group_id.is_(None))
        # Якщо group_id is None і filter_global_only is False, показує всі досягнення користувача (і глобальні, і групові).

        stmt = stmt.order_by(UserAchievement.achieved_at.desc()).offset(skip).limit(limit)
        achievements_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        response_list = [UserAchievementResponse.model_validate(ach) for ach in achievements_db] # Pydantic v2
        logger.info(f"Отримано {len(response_list)} досягнень для {log_ctx}.")
        return response_list

    async def list_users_for_badge(
        self,
        badge_id: UUID,
        group_id: Optional[UUID] = None, # Фільтр за ID групи
        filter_global_only: bool = False, # Якщо True і group_id не вказано, показує тільки глобальні
        skip: int = 0,
        limit: int = 100
    ) -> List[UserAchievementResponse]: # Повертає список UserAchievement, звідки можна отримати користувачів
        """
        Перелічує користувачів (через їхні записи UserAchievement), які отримали вказаний бейдж.
        Може фільтрувати за групою або показувати тільки глобальні нагородження цим бейджем.
        """
        log_ctx_parts = [f"бейдж ID '{badge_id}'"]
        if group_id: log_ctx_parts.append(f"група ID '{group_id}'")
        if filter_global_only and not group_id: log_ctx_parts.append("тільки глобальні")
        log_ctx = ", ".join(log_ctx_parts)
        logger.debug(f"Перелік користувачів, що здобули {log_ctx}, пропустити={skip}, ліміт={limit}")

        stmt = select(UserAchievement).options(
            selectinload(UserAchievement.user).options(selectinload(User.user_type)), # Завантажуємо користувача для відповіді
            selectinload(UserAchievement.badge), # Можна noload("*"), якщо сам бейдж не потрібен у відповіді
            selectinload(UserAchievement.group),
            selectinload(UserAchievement.awarded_by).options(noload("*"))
        ).where(UserAchievement.badge_id == badge_id)

        if group_id is not None:
            stmt = stmt.where(UserAchievement.group_id == group_id)
        elif filter_global_only:
            stmt = stmt.where(UserAchievement.group_id.is_(None))
        # Якщо group_id is None і filter_global_only is False, показує всіх користувачів з цим бейджем.

        stmt = stmt.order_by(UserAchievement.achieved_at.desc()).offset(skip).limit(limit)
        achievements_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        response_list = [UserAchievementResponse.model_validate(ach) for ach in achievements_db] # Pydantic v2
        logger.info(f"Отримано {len(response_list)} записів нагороджень для {log_ctx}.")
        return response_list

    # TODO: Розглянути метод для відкликання досягнення (revoke_achievement), якщо це передбачено бізнес-логікою.
    # Це може включати видалення запису UserAchievement або позначення його як неактивного/відкликаного.

logger.debug(f"{UserAchievementService.__name__} (сервіс досягнень користувачів) успішно визначено.")
