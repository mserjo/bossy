# backend/app/src/services/gamification/achievement.py
"""
Сервіс для управління досягненнями користувачів.

Відповідає за логіку нагородження користувачів бейджами (досягненнями)
та отримання інформації про їхні досягнення.
"""
from typing import List, Optional, Dict, Any # Tuple, Any видалено, Dict може бути корисним
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select # Оновлено імпорт
from sqlalchemy.orm import selectinload, noload
from sqlalchemy.exc import IntegrityError

from backend.app.src.services.base import BaseService
from backend.app.src.models.gamification.achievement import UserAchievement
from backend.app.src.models.gamification.badge import Badge
from backend.app.src.models.auth.user import User
from backend.app.src.models.groups.group import Group

from backend.app.src.schemas.gamification.achievement import (
    UserAchievementCreate,
    UserAchievementResponse
)
from backend.app.src.config import logger  # Використання спільного логера з конфігу
from backend.app.src.config import settings


class UserAchievementService(BaseService): # type: ignore
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
            selectinload(UserAchievement.badge),
            selectinload(UserAchievement.group),
            selectinload(UserAchievement.awarded_by).options(selectinload(User.user_type))
        ).where(UserAchievement.id == achievement_id)
        try:
            result = await self.db_session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Помилка при отриманні UserAchievement ID {achievement_id}: {e}", exc_info=settings.DEBUG)
            return None

    async def award_achievement_to_user(
            self,
            user_id: UUID,
            badge_id: UUID,
            achievement_data: UserAchievementCreate,
            awarded_by_user_id: Optional[UUID] = None
    ) -> UserAchievementResponse: # type: ignore
        """
        Нагороджує користувача досягненням (бейджем).

        :param user_id: ID користувача, якому надається досягнення.
        :param badge_id: ID бейджа, що надається.
        :param achievement_data: Дані для створення запису UserAchievement (контекст, група).
        :param awarded_by_user_id: ID користувача, який нагородив (якщо застосовно).
        :return: Pydantic схема UserAchievementResponse.
        :raises ValueError: Якщо користувача, бейдж, або групу не знайдено, або бейдж не повторюваний і вже є. # i18n
        :raises RuntimeError: У разі неконсистентності даних після коміту.
        """
        log_ctx_parts = [f"користувач ID '{user_id}'", f"бейдж ID '{badge_id}'"]
        if achievement_data.group_id:
            log_ctx_parts.append(f"група ID '{achievement_data.group_id}'")
        log_ctx = ", ".join(log_ctx_parts)
        logger.debug(f"Спроба нагородження досягненням: {log_ctx}.")

        async with self.db_session.begin_nested() if self.db_session.in_transaction() else self.db_session.begin():
            user = await self.db_session.get(User, user_id)
            if not user:
                raise ValueError(f"Користувача з ID '{user_id}' не знайдено.")  # i18n

            badge = await self.db_session.get(Badge, badge_id)
            if not badge:
                raise ValueError(f"Бейдж з ID '{badge_id}' не знайдено.")  # i18n

            if achievement_data.group_id:
                group = await self.db_session.get(Group, achievement_data.group_id)
                if not group:
                    raise ValueError(f"Групу з ID '{achievement_data.group_id}' не знайдено.")  # i18n

            if not badge.is_repeatable:
                existing_achievement_stmt = select(UserAchievement.id).where(
                    UserAchievement.user_id == user_id,
                    UserAchievement.badge_id == badge_id
                )
                if achievement_data.group_id:
                    existing_achievement_stmt = existing_achievement_stmt.where(
                        UserAchievement.group_id == achievement_data.group_id)
                else:
                    existing_achievement_stmt = existing_achievement_stmt.where(UserAchievement.group_id.is_(None))

                existing_result = await self.db_session.execute(existing_achievement_stmt)
                if existing_result.scalar_one_or_none():
                    msg = f"Бейдж '{badge.name}' (ID: {badge_id}) вже було надано цьому користувачеві в даному контексті і він не є повторюваним."  # i18n
                    logger.warning(msg)
                    raise ValueError(msg)

            new_achievement_data = achievement_data.model_dump()
            new_achievement_data.update({
                "user_id": user_id,
                "badge_id": badge_id,
                "awarded_by_user_id": awarded_by_user_id
            })
            new_achievement_db = UserAchievement(**new_achievement_data)
            self.db_session.add(new_achievement_db)
            await self.db_session.flush() # Щоб отримати ID
            await self.db_session.refresh(new_achievement_db)


        # Окремий блок try/except для коміту, щоб відкат не вплинув на вже отриманий new_achievement_db.id
        try:
            await self.commit()
        except IntegrityError as e: # Ця помилка мала б бути перехоплена раніше, якщо UniqueConstraint спрацював до flush
            await self.rollback()
            logger.error(f"Помилка цілісності при нагородженні ({log_ctx}): {e}", exc_info=settings.DEBUG)
            raise ValueError(f"Не вдалося нагородити досягненням через конфлікт даних: {e}") # i18n
        except Exception as e:
            await self.rollback()
            logger.error(f"Неочікувана помилка при коміті нагородження ({log_ctx}): {e}", exc_info=settings.DEBUG)
            raise

        # Отримуємо повний об'єкт для відповіді після успішного коміту
        refreshed_achievement = await self._get_orm_user_achievement_by_id(new_achievement_db.id) # type: ignore
        if not refreshed_achievement:
            logger.critical(
                f"Не вдалося отримати щойно створене досягнення ID {new_achievement_db.id} після коміту.") # type: ignore
            raise RuntimeError("Критична помилка: не вдалося отримати запис досягнення після збереження.") # i18n

        logger.info(
            f"Досягнення (Бейдж ID: '{badge_id}') успішно надано користувачу ID '{user_id}'. ID Запису: {refreshed_achievement.id}")
        return UserAchievementResponse.model_validate(refreshed_achievement)

    async def get_user_achievement_by_id(self, achievement_id: UUID) -> Optional[UserAchievementResponse]:
        """Отримує конкретний запис про нагородження досягненням за його ID."""
        logger.debug(f"Спроба отримання запису досягнення за ID: {achievement_id}")
        try:
            achievement_db = await self._get_orm_user_achievement_by_id(achievement_id)
            if achievement_db:
                logger.info(f"Запис досягнення з ID '{achievement_id}' знайдено.")
                return UserAchievementResponse.model_validate(achievement_db)

            logger.info(f"Запис досягнення з ID '{achievement_id}' не знайдено.")
            return None
        except Exception as e:
            logger.error(f"Помилка при отриманні запису досягнення ID {achievement_id}: {e}", exc_info=settings.DEBUG)
            return None

    async def list_achievements_for_user(
            self,
            session: AsyncSession, # Додано session
            user_id: UUID,
            group_id: Optional[UUID] = None,
            filter_global_only: bool = False,
            skip: int = 0,
            limit: int = 100
    ) -> List[UserAchievementResponse]: # Tuple замінено на List, оскільки count не повертався
        """
        Перелічує досягнення для вказаного користувача.
        Може фільтрувати за групою або показувати тільки глобальні досягнення.
        """
        log_ctx_parts = [f"користувач ID '{user_id}'"]
        if group_id: log_ctx_parts.append(f"група ID '{group_id}'")
        if filter_global_only and not group_id: log_ctx_parts.append("тільки глобальні")
        log_ctx = ", ".join(log_ctx_parts)
        logger.debug(f"Перелік досягнень для {log_ctx}, пропустити={skip}, ліміт={limit}")

        try:
            stmt = select(UserAchievement).options(
                selectinload(UserAchievement.user).options(noload("*")),
                selectinload(UserAchievement.badge),
                selectinload(UserAchievement.group),
                selectinload(UserAchievement.awarded_by).options(noload("*"))
            ).where(UserAchievement.user_id == user_id)

            if group_id is not None:
                stmt = stmt.where(UserAchievement.group_id == group_id)
            elif filter_global_only:
                stmt = stmt.where(UserAchievement.group_id.is_(None))

            stmt = stmt.order_by(UserAchievement.achieved_at.desc()).offset(skip).limit(limit)

            achievements_db_result = await session.execute(stmt) # Використовуємо передану сесію
            achievements_db = list(achievements_db_result.scalars().unique().all())

            response_list = [UserAchievementResponse.model_validate(ach) for ach in achievements_db]
            logger.info(f"Отримано {len(response_list)} досягнень для {log_ctx}.")
            return response_list
        except Exception as e:
            logger.error(f"Помилка при переліку досягнень для {log_ctx}: {e}", exc_info=settings.DEBUG)
            return []

    async def list_users_for_badge(
            self,
            session: AsyncSession, # Додано session
            badge_id: UUID,
            group_id: Optional[UUID] = None,
            filter_global_only: bool = False,
            skip: int = 0,
            limit: int = 100
    ) -> List[UserAchievementResponse]:
        """
        Перелічує користувачів (через їхні записи UserAchievement), які отримали вказаний бейдж.
        Може фільтрувати за групою або показувати тільки глобальні нагородження цим бейджем.
        """
        log_ctx_parts = [f"бейдж ID '{badge_id}'"]
        if group_id: log_ctx_parts.append(f"група ID '{group_id}'")
        if filter_global_only and not group_id: log_ctx_parts.append("тільки глобальні")
        log_ctx = ", ".join(log_ctx_parts)
        logger.debug(f"Перелік користувачів, що здобули {log_ctx}, пропустити={skip}, ліміт={limit}")

        try:
            stmt = select(UserAchievement).options(
                selectinload(UserAchievement.user).options(selectinload(User.user_type)),
                selectinload(UserAchievement.badge),
                selectinload(UserAchievement.group),
                selectinload(UserAchievement.awarded_by).options(noload("*"))
            ).where(UserAchievement.badge_id == badge_id)

            if group_id is not None:
                stmt = stmt.where(UserAchievement.group_id == group_id)
            elif filter_global_only:
                stmt = stmt.where(UserAchievement.group_id.is_(None))

            stmt = stmt.order_by(UserAchievement.achieved_at.desc()).offset(skip).limit(limit)

            achievements_db_result = await session.execute(stmt) # Використовуємо передану сесію
            achievements_db = list(achievements_db_result.scalars().unique().all())

            response_list = [UserAchievementResponse.model_validate(ach) for ach in achievements_db]
            logger.info(f"Отримано {len(response_list)} записів нагороджень для {log_ctx}.")
            return response_list
        except Exception as e:
            logger.error(f"Помилка при переліку користувачів для бейджа {badge_id}: {e}", exc_info=settings.DEBUG)
            return []

    # TODO: [Feature] Розглянути метод для відкликання досягнення (revoke_achievement),
    #       якщо це передбачено бізнес-логікою (`technical_task.txt`).
    # Це може включати видалення запису UserAchievement або позначення його як неактивного/відкликаного.


logger.debug(f"{UserAchievementService.__name__} (сервіс досягнень користувачів) успішно визначено.")
