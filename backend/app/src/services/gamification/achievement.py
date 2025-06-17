# backend/app/src/services/gamification/achievement.py
"""
Сервіс для управління досягненнями користувачів.

Відповідає за логіку нагородження користувачів бейджами (досягненнями)
та отримання інформації про їхні досягнення.

# Примітка: Тип ID для UserAchievement (achievement_id) та Badge (badge_id) припускається як int, оскільки моделі не були надані для перевірки.
"""
from typing import List, Optional, Dict, Any # Dict, Any залишені для new_achievement_data
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select # Оновлено імпорт
from sqlalchemy.orm import selectinload, noload
from sqlalchemy.exc import IntegrityError

from backend.app.src.services.base import BaseService
from backend.app.src.models.gamification.achievement import UserAchievement
from backend.app.src.repositories.gamification.user_achievement_repository import UserAchievementRepository # Імпорт репозиторію
from backend.app.src.models.gamification.badge import Badge
from backend.app.src.models.auth.user import User
from backend.app.src.models.groups.group import Group

from backend.app.src.schemas.gamification.achievement import (
    UserAchievementCreate,
    UserAchievementResponse
)
from backend.app.src.config import settings
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


class UserAchievementService(BaseService): # type: ignore видалено
    """
    Сервіс для управління досягненнями користувачів (нагородження користувачів значками-бейджами).
    Обробляє створення та отримання записів UserAchievement.
    Досягнення представляють собою зв'язок між користувачем (User) та значком (Badge),
    який він отримав, можливо, в контексті певної групи та з додатковими деталями.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        self.user_achievement_repo = UserAchievementRepository() # Ініціалізація репозиторію
        logger.info("UserAchievementService ініціалізовано.")

    async def _get_orm_user_achievement_by_id(self, achievement_id: int) -> Optional[UserAchievement]: # achievement_id: UUID -> int
        """
        Внутрішній метод для отримання ORM моделі UserAchievement з усіма зв'язками.
        :param achievement_id: ID запису досягнення (int).
        """
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
            user_id: int, # UUID -> int
            badge_id: int, # UUID -> int
            achievement_data: UserAchievementCreate,
            awarded_by_user_id: Optional[int] = None # Optional[UUID] -> Optional[int]
    ) -> UserAchievementResponse: # type: ignore видалено
        """
        Нагороджує користувача досягненням (бейджем).

        :param user_id: ID користувача (int), якому надається досягнення.
        :param badge_id: ID бейджа (int), що надається.
        :param achievement_data: Дані для створення запису UserAchievement (контекст, група).
        :param awarded_by_user_id: ID користувача (int), який нагородив (якщо застосовно).
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
                # Використовуємо репозиторій для перевірки існуючого досягнення
                existing_achievement = await self.user_achievement_repo.get_by_user_and_badge(
                    session=self.db_session,
                    user_id=user_id,
                    badge_id=badge_id,
                    group_id=achievement_data.group_id
                )
                if existing_achievement:
                    msg = f"Бейдж '{badge.name}' (ID: {badge_id}) вже було надано цьому користувачеві в даному контексті і він не є повторюваним."
                    logger.warning(msg)
                    raise ValueError(msg)

            # Дані для створення UserAchievementCreateSchema, який приймає UserAchievementRepository.create
            # awarded_at встановлюється автоматично через TimestampedMixin
            create_schema_data = UserAchievementCreate(
                user_id=user_id,
                badge_id=badge_id,
                group_id=achievement_data.group_id,
                achieved_at=achievement_data.achieved_at or datetime.now(timezone.utc), # Забезпечуємо achieved_at
                context_data=achievement_data.context_data,
                awarded_by_user_id=awarded_by_user_id
            )

            new_achievement_db = await self.user_achievement_repo.create(
                session=self.db_session,
                obj_in=create_schema_data
            )
            # Попередній flush та refresh не потрібні, оскільки create з BaseRepository повертає ORM об'єкт

        # Коміт після виходу з блоку with session.begin() (якщо він був) або тут
        try:
            await self.commit()
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності при нагородженні ({log_ctx}): {e}", exc_info=settings.DEBUG)
            raise ValueError(f"Не вдалося нагородити досягненням через конфлікт даних: {e}")
        except Exception as e:
            await self.rollback()
            logger.error(f"Неочікувана помилка при коміті нагородження ({log_ctx}): {e}", exc_info=settings.DEBUG)
            raise

        # Отримуємо повний об'єкт для відповіді після успішного коміту
        refreshed_achievement = await self._get_orm_user_achievement_by_id(new_achievement_db.id) # type: ignore видалено
        if not refreshed_achievement:
            logger.critical(
                f"Не вдалося отримати щойно створене досягнення ID {new_achievement_db.id} після коміту.")
            raise RuntimeError("Критична помилка: не вдалося отримати запис досягнення після збереження.") # i18n

        logger.info(
            f"Досягнення (Бейдж ID: '{badge_id}') успішно надано користувачу ID '{user_id}'. ID Запису: {refreshed_achievement.id}")
        return UserAchievementResponse.model_validate(refreshed_achievement)

    async def get_user_achievement_by_id(self, achievement_id: int) -> Optional[UserAchievementResponse]: # achievement_id: UUID -> int
        """
        Отримує конкретний запис про нагородження досягненням за його ID.
        :param achievement_id: ID запису досягнення (int).
        """
        logger.debug(f"Спроба отримання запису досягнення за ID: {achievement_id}")
        try:
            # Використовуємо _get_orm_user_achievement_by_id для завантаження зв'язків,
            # оскільки repo.get() може не завантажувати їх так, як потрібно для UserAchievementResponse.
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
            user_id: int,
            group_id: Optional[int] = None,
            filter_global_only: bool = False, # Цей параметр буде оброблено в repo
            skip: int = 0,
            limit: int = 100
    ) -> List[UserAchievementResponse]:
        """
        Перелічує досягнення для вказаного користувача.
        Може фільтрувати за групою або показувати тільки глобальні досягнення.
        """
        log_ctx_parts = [f"користувач ID '{user_id}'"]
        if group_id: log_ctx_parts.append(f"група ID '{group_id}'")
        # filter_global_only використовується в repo.get_achievements_for_user
        # якщо group_id is None
        if filter_global_only and group_id is None: log_ctx_parts.append("тільки глобальні")
        log_ctx = ", ".join(log_ctx_parts)
        logger.debug(f"Перелік досягнень для {log_ctx}, пропустити={skip}, ліміт={limit}")

        try:
            # Використовуємо метод репозиторію
            # Репозиторій повертає Tuple[List[UserAchievement], int], нам потрібен тільки список.
            # TODO: Розглянути, чи потрібне завантаження зв'язків тут.
            # Якщо UserAchievementResponse потребує зв'язків, які не завантажуються в repo.get_achievements_for_user,
            # то потрібен буде цикл з _get_orm_user_achievement_by_id або розширення репо.
            # Наразі припускаємо, що моделі мають selectinload в своїх визначеннях зв'язків.
            achievements_db_list, _ = await self.user_achievement_repo.get_achievements_for_user(
                session=self.db_session,
                user_id=user_id,
                group_id=group_id,
                include_global=filter_global_only if group_id is None else False, # Логіка include_global для репо
                skip=skip,
                limit=limit
            )

            # Якщо UserAchievementResponse потребує більш глибоких зв'язків, ніж ті, що завантажує репозиторій:
            # response_list = []
            # for ach_base in achievements_db_list:
            #     detailed_ach = await self._get_orm_user_achievement_by_id(ach_base.id)
            #     if detailed_ach:
            #         response_list.append(UserAchievementResponse.model_validate(detailed_ach))
            # Або, якщо зв'язки в моделі налаштовані на selectinload:
            response_list = [UserAchievementResponse.model_validate(ach) for ach in achievements_db_list]

            logger.info(f"Отримано {len(response_list)} досягнень для {log_ctx}.")
            return response_list
        except Exception as e:
            logger.error(f"Помилка при переліку досягнень для {log_ctx}: {e}", exc_info=settings.DEBUG)
            return []

    async def list_users_for_badge(
            self,
            badge_id: int,
            group_id: Optional[int] = None,
            filter_global_only: bool = False, # Параметр для repo
            skip: int = 0,
            limit: int = 100
    ) -> List[UserAchievementResponse]:
        """
        Перелічує користувачів (через їхні записи UserAchievement), які отримали вказаний бейдж.
        Може фільтрувати за групою або показувати тільки глобальні нагородження цим бейджем.
        """
        log_ctx_parts = [f"бейдж ID '{badge_id}'"]
        if group_id: log_ctx_parts.append(f"група ID '{group_id}'")
        if filter_global_only and group_id is None: log_ctx_parts.append("тільки глобальні")
        log_ctx = ", ".join(log_ctx_parts)
        logger.debug(f"Перелік користувачів, що здобули {log_ctx}, пропустити={skip}, ліміт={limit}")

        try:
            # Використовуємо новий метод репозиторію
            # TODO: Аналогічно до list_achievements_for_user, питання завантаження зв'язків.
            achievements_db_list, _ = await self.user_achievement_repo.get_achievements_for_badge(
                session=self.db_session,
                badge_id=badge_id,
                group_id=group_id,
                include_global=filter_global_only if group_id is None else False,
                skip=skip,
                limit=limit
            )

            # Припускаємо, що UserAchievementResponse обробляє ORM об'єкти і їх зв'язки (lazy/selectin loaded)
            response_list = [UserAchievementResponse.model_validate(ach) for ach in achievements_db_list]

            logger.info(f"Отримано {len(response_list)} записів нагороджень для {log_ctx}.")
            return response_list
        except Exception as e:
            logger.error(f"Помилка при переліку користувачів для бейджа {badge_id}: {e}", exc_info=settings.DEBUG)
            return []

    # TODO: [Feature] Розглянути метод для відкликання досягнення (revoke_achievement),
    #       якщо це передбачено бізнес-логікою (`technical_task.txt`).
    # Це може включати видалення запису UserAchievement або позначення його як неактивного/відкликаного.


logger.debug(f"{UserAchievementService.__name__} (сервіс досягнень користувачів) успішно визначено.")
