# backend/app/src/services/gamification/rating.py
# import logging # Замінено на централізований логер
from typing import List, Optional, Dict, Any  # Dict, Any не використовуються, можна прибрати
from uuid import UUID
from datetime import datetime, timezone  # date не використовується, можна прибрати
from decimal import Decimal  # Для балів рейтингу

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload  # joinedload не використовується
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func  # Для агрегації, наприклад, func.count

# Повні шляхи імпорту
from backend.app.src.services.base import BaseService
from backend.app.src.models.gamification.rating import UserGroupRating  # Модель SQLAlchemy UserGroupRating
from backend.app.src.models.auth.user import User
from backend.app.src.models.groups.group import Group
from backend.app.src.services.bonuses.account import UserAccountService  # Для отримання балів користувача

from backend.app.src.schemas.gamification.rating import (  # Схеми Pydantic
    UserGroupRatingResponse,
    GroupLeaderboardResponse
    # UserGroupRatingCreate, UserGroupRatingUpdate - рейтинги зазвичай розраховуються, а не CRUD напряму
)
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings  # Для доступу до конфігурацій (наприклад, DEBUG)

# TODO: Визначити конвенцію для `period_identifier` (наприклад, "all_time", "YYYY-MM", або ID сезону/події).
#  Це має бути узгоджено з тим, як періоди визначаються та використовуються в системі.
DEFAULT_PERIOD_IDENTIFIER = "all_time"  # Приклад ідентифікатора для "за весь час"


class UserRatingService(BaseService):
    """
    Сервіс для управління рейтингами користувачів та таблицями лідерів у межах груп.
    Обробляє розрахунок та оновлення записів UserGroupRating.
    Рейтинги базуються на накопичених бонусних балах користувачів.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        self.account_service = UserAccountService(db_session)  # Ініціалізація сервісу рахунків
        logger.info("UserRatingService ініціалізовано.")

    async def get_user_group_rating(
            self,
            user_id: UUID,
            group_id: UUID,
            period_identifier: Optional[str] = None  # Якщо None, використовується DEFAULT_PERIOD_IDENTIFIER
    ) -> Optional[UserGroupRatingResponse]:
        """
        Отримує запис рейтингу користувача в групі за певний період.

        :param user_id: ID користувача.
        :param group_id: ID групи.
        :param period_identifier: Ідентифікатор періоду (наприклад, "all_time", "2023-10").
        :return: Pydantic схема UserGroupRatingResponse або None.
        """
        effective_period = period_identifier if period_identifier is not None else DEFAULT_PERIOD_IDENTIFIER
        log_ctx = f"користувач ID '{user_id}', група ID '{group_id}', період '{effective_period}'"
        logger.debug(f"Спроба отримання UserGroupRating для {log_ctx}.")

        stmt = select(UserGroupRating).options(
            selectinload(UserGroupRating.user).options(selectinload(User.user_type)),
            selectinload(UserGroupRating.group)
        ).where(
            UserGroupRating.user_id == user_id,
            UserGroupRating.group_id == group_id,
            UserGroupRating.period_identifier == effective_period  # Використовуємо поле period_identifier
        )

        rating_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if rating_db:
            logger.info(f"Запис UserGroupRating знайдено для {log_ctx}.")
            return UserGroupRatingResponse.model_validate(rating_db)  # Pydantic v2

        logger.info(f"Запис UserGroupRating не знайдено для {log_ctx}.")
        return None

    async def update_user_group_rating(
            self,
            user_id: UUID,
            group_id: UUID,
            period_identifier: Optional[str] = None  # Якщо None, використовується DEFAULT_PERIOD_IDENTIFIER
    ) -> UserGroupRatingResponse:  # Повертає UserGroupRatingResponse, не Optional, бо створить якщо не існує
        """
        Оновлює або створює запис рейтингу користувача для вказаної групи та періоду.
        Рейтинг розраховується на основі поточного балансу бонусного рахунку користувача в цій групі.

        :param user_id: ID користувача.
        :param group_id: ID групи.
        :param period_identifier: Ідентифікатор періоду.
        :return: Pydantic схема оновленого або створеного UserGroupRatingResponse.
        :raises ValueError: Якщо виникає конфлікт даних при збереженні. # i18n
        """
        effective_period = period_identifier if period_identifier is not None else DEFAULT_PERIOD_IDENTIFIER
        log_ctx = f"користувач ID '{user_id}', група ID '{group_id}', період '{effective_period}'"
        logger.info(f"Спроба оновлення/створення рейтингу для {log_ctx}.")

        # Отримання поточного балансу користувача в групі
        # Для "all_time" рейтингу, group_id в UserAccountService має бути group_id.
        # Якщо рейтинг за період стосується глобального рахунку, group_id тут має бути None.
        # TODO: Уточнити, чи залежить `group_id` для `UserAccountService` від `period_identifier`.
        #  Поки що припускаємо, що рейтинг завжди в контексті групи, тому `group_id` передається.
        user_account = await self.account_service.get_user_account(user_id, group_id=group_id)

        new_score = Decimal("0.00")
        if user_account:
            new_score = user_account.balance  # Баланс вже є Decimal
        else:
            logger.warning(f"Бонусний рахунок для {log_ctx} не знайдено. Рейтинг буде розраховано з 0 балами.")

        logger.info(f"Розраховано новий бал для {log_ctx}: {new_score}")

        # Пошук існуючого запису рейтингу
        stmt_existing = select(UserGroupRating).where(
            UserGroupRating.user_id == user_id,
            UserGroupRating.group_id == group_id,
            UserGroupRating.period_identifier == effective_period
        )
        rating_db = (await self.db_session.execute(stmt_existing)).scalar_one_or_none()

        current_time = datetime.now(timezone.utc)
        if rating_db:  # Якщо запис існує, оновлюємо
            if rating_db.rating_score == new_score and rating_db.last_calculated_at and \
                    (current_time - rating_db.last_calculated_at) < timedelta(
                minutes=1):  # Не оновлювати занадто часто, якщо бал не змінився
                logger.info(f"Рейтинг для {log_ctx} вже {new_score} і нещодавно оновлений. Оновлення не потрібне.")
            else:
                logger.info(f"Оновлення рейтингу для {log_ctx} з {rating_db.rating_score} до {new_score}.")
                rating_db.rating_score = new_score
                rating_db.last_calculated_at = current_time
        else:  # Створюємо новий запис
            logger.info(f"Створення нового запису UserGroupRating для {log_ctx} з балом {new_score}.")
            rating_db = UserGroupRating(
                user_id=user_id,
                group_id=group_id,
                rating_score=new_score,
                period_identifier=effective_period,
                last_calculated_at=current_time
                # `rank` не зберігається, розраховується для лідерборду
            )
            self.db_session.add(rating_db)

        try:
            await self.commit()
            # Оновлюємо для завантаження зв'язків user та group
            await self.db_session.refresh(rating_db, attribute_names=['user', 'group'])
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності UserGroupRating для {log_ctx}: {e}", exc_info=settings.DEBUG)
            # i18n
            raise ValueError(f"Не вдалося оновити/створити рейтинг через конфлікт даних: {e}")

        logger.info(f"UserGroupRating для {log_ctx} успішно встановлено на бал {new_score}.")
        return UserGroupRatingResponse.model_validate(rating_db)  # Pydantic v2

    async def get_group_leaderboard(
            self,
            group_id: UUID,
            period_identifier: Optional[str] = None,  # Якщо None, використовується DEFAULT_PERIOD_IDENTIFIER
            limit: int = 100
    ) -> GroupLeaderboardResponse:
        """
        Генерує таблицю лідерів для вказаної групи та періоду.

        :param group_id: ID групи.
        :param period_identifier: Ідентифікатор періоду.
        :param limit: Максимальна кількість записів у лідерборді.
        :return: Pydantic схема GroupLeaderboardResponse.
        """
        effective_period = period_identifier if period_identifier is not None else DEFAULT_PERIOD_IDENTIFIER
        log_ctx = f"група ID '{group_id}', період '{effective_period}'"
        logger.info(f"Генерація лідерборду для {log_ctx}, ліміт {limit}.")

        stmt = select(UserGroupRating).options(
            selectinload(UserGroupRating.user).options(selectinload(User.user_type)),
            # Завантажуємо користувача для відповіді
            # Група вже відома з group_id, але можна завантажити для консистентності, якщо потрібно
            # selectinload(UserGroupRating.group)
        ).where(
            UserGroupRating.group_id == group_id,
            UserGroupRating.period_identifier == effective_period
        )

        # Сортування: бал (спадання), час останнього розрахунку (зростання - хто раніше досяг, той вище), ID користувача (для стабільності)
        stmt = stmt.order_by(
            UserGroupRating.rating_score.desc(),
            UserGroupRating.last_calculated_at.asc(),
            UserGroupRating.user_id.asc()
        ).limit(limit)

        ratings_db = (await self.db_session.execute(stmt)).scalars().all()

        # TODO: Якщо потрібен явний `rank` в UserGroupRatingResponse, його треба розрахувати тут.
        # Наприклад, на основі позиції в відсортованому списку ratings_db.
        # Або використовувати віконні функції SQL, якщо це підтримується і ефективно.
        leaderboard_entries = [UserGroupRatingResponse.model_validate(r) for r in ratings_db]  # Pydantic v2

        # Загальна кількість учасників рейтингу для цієї групи та періоду
        count_stmt = select(func.count(UserGroupRating.id)).where(
            UserGroupRating.group_id == group_id,
            UserGroupRating.period_identifier == effective_period
        )
        total_participants = (await self.db_session.execute(count_stmt)).scalar_one_or_none() or 0

        group_name = "N/A"  # i18n
        group_obj = await self.db_session.get(Group, group_id)
        if group_obj:
            group_name = group_obj.name

        logger.info(f"Отримано {len(leaderboard_entries)} записів для лідерборду {log_ctx}.")

        return GroupLeaderboardResponse(
            group_id=group_id,
            group_name=group_name,
            period_identifier=effective_period,
            ratings=leaderboard_entries,
            total_participants=total_participants,
            generated_at=datetime.now(timezone.utc)
        )

    # TODO: Розглянути метод для періодичного перерахунку всіх рейтингів (наприклад, раз на день або після значних подій).
    # async def recalculate_all_ratings_for_period(period_identifier: str, group_id: Optional[UUID] = None): ...


logger.debug(f"{UserRatingService.__name__} (сервіс рейтингів користувачів) успішно визначено.")
