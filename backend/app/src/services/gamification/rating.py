# backend/app/src/services/gamification/rating.py
from typing import List, Optional
from datetime import datetime, timezone, date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from backend.app.src.services.base import BaseService
from backend.app.src.models.gamification.rating import UserGroupRating
from backend.app.src.repositories.gamification.rating_repository import UserGroupRatingRepository # Імпорт репозиторію
from backend.app.src.models.auth.user import User
from backend.app.src.models.groups.group import Group
from backend.app.src.services.bonuses.account import UserAccountService

from backend.app.src.schemas.gamification.rating import (
    UserGroupRatingResponse,
    UserGroupRatingCreateSchema, # Додано для створення
    UserGroupRatingUpdateSchema, # Додано для оновлення
    GroupLeaderboardResponse
)
from backend.app.src.core.dicts import RatingType # Імпорт RatingType Enum
from backend.app.src.config import settings
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

DEFAULT_RATING_TYPE = RatingType.OVERALL # Змінено на Enum


class UserRatingService(BaseService):
    """
    Сервіс для управління рейтингами користувачів та таблицями лідерів у межах груп.
    Обробляє розрахунок та оновлення записів UserGroupRating.
    Рейтинги базуються на накопичених бонусних балах користувачів.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        self.account_service = UserAccountService(db_session)
        self.rating_repo = UserGroupRatingRepository() # Ініціалізація репозиторію
        logger.info("UserRatingService ініціалізовано.")

    async def get_user_group_rating(
            self,
            user_id: int, # Змінено UUID на int
            group_id: int, # Змінено UUID на int
            rating_type: RatingType = DEFAULT_RATING_TYPE,
            period_end_date: Optional[date] = None
    ) -> Optional[UserGroupRatingResponse]:
        """
        Отримує запис рейтингу користувача в групі за певний період.
        """
        log_ctx = f"користувач ID '{user_id}', група ID '{group_id}', тип '{rating_type.value}', дата кінця періоду '{period_end_date}'"
        logger.debug(f"Спроба отримання UserGroupRating для {log_ctx}.")

        rating_db = await self.rating_repo.get_rating_for_user_in_group(
            session=self.db_session,
            user_id=user_id,
            group_id=group_id,
            rating_type=rating_type,
            period_end_date=period_end_date
        )

        if rating_db:
            logger.info(f"Запис UserGroupRating знайдено для {log_ctx}.")
            # TODO: Переконатися, що UserGroupRatingResponse може завантажити user, group, якщо потрібно.
            # Можливо, потрібен буде окремий get_by_id з selectinload, якщо repo метод не завантажує.
            # Наразі припускаємо, що model_validate обробить це.
            return UserGroupRatingResponse.model_validate(rating_db)

        logger.info(f"Запис UserGroupRating не знайдено для {log_ctx}.")
        return None

    async def update_user_group_rating(
            self,
            user_id: int, # Змінено UUID на int
            group_id: int, # Змінено UUID на int
            rating_type: RatingType = DEFAULT_RATING_TYPE,
            period_start_date: Optional[date] = None, # Додано для повноти даних
            period_end_date: Optional[date] = None   # Додано для повноти даних
    ) -> UserGroupRatingResponse:
        """
        Оновлює або створює запис рейтингу користувача для вказаної групи та періоду.
        """
        log_ctx = (f"користувач ID '{user_id}', група ID '{group_id}', тип '{rating_type.value}', "
                   f"період: {period_start_date} - {period_end_date}")
        logger.info(f"Спроба оновлення/створення рейтингу для {log_ctx}.")

        user_account = await self.account_service.get_user_account(user_id, group_id=group_id)
        new_score = user_account.balance if user_account else Decimal("0.00")
        if not user_account:
            logger.warning(f"Бонусний рахунок для {log_ctx} не знайдено. Рейтинг буде розраховано з 0 балами.")
        logger.info(f"Розраховано новий бал для {log_ctx}: {new_score}")

        rating_db = await self.rating_repo.get_rating_for_user_in_group(
            session=self.db_session,
            user_id=user_id,
            group_id=group_id,
            rating_type=rating_type,
            period_end_date=period_end_date # period_start_date не використовується в get_rating_for_user_in_group
        )

        current_time = datetime.now(timezone.utc)
        updated_orm_obj: Optional[UserGroupRating] = None

        if rating_db:
            # TODO: Перевірити логіку про timedelta(minutes=1) - чи потрібна вона тут, або це має бути налаштування
            if rating_db.rating_score == new_score and rating_db.last_calculated_at and \
               (current_time - rating_db.last_calculated_at) < settings.RATING_UPDATE_THRESHOLD_MINUTES * 60: # Використовуємо timedelta
                logger.info(f"Рейтинг для {log_ctx} вже {new_score} і нещодавно оновлений. Оновлення не потрібне.")
                updated_orm_obj = rating_db
            else:
                logger.info(f"Оновлення рейтингу для {log_ctx} з {rating_db.rating_score} до {new_score}.")
                update_schema = UserGroupRatingUpdateSchema(
                    rating_score=new_score,
                    last_calculated_at=current_time
                    # period_start_date, period_end_date, rating_type не оновлюються для існуючого запису
                )
                updated_orm_obj = await self.rating_repo.update(
                    session=self.db_session, db_obj=rating_db, obj_in=update_schema
                )
        else:
            logger.info(f"Створення нового запису UserGroupRating для {log_ctx} з балом {new_score}.")
            create_schema = UserGroupRatingCreateSchema(
                user_id=user_id,
                group_id=group_id,
                rating_score=new_score,
                rating_type=rating_type,
                period_start_date=period_start_date,
                period_end_date=period_end_date,
                last_calculated_at=current_time
            )
            updated_orm_obj = await self.rating_repo.create(session=self.db_session, obj_in=create_schema)

        if not updated_orm_obj: # Якщо create/update повернули None (малоймовірно для BaseRepository)
             logger.error(f"Не вдалося оновити або створити запис рейтингу для {log_ctx}.")
             raise RuntimeError("Помилка оновлення/створення запису рейтингу.")

        try:
            await self.commit()
            # Для завантаження зв'язків user та group, якщо вони не завантажені репозиторієм.
            # BaseRepository методи create/update повертають ORM об'єкт, але без гарантії завантажених зв'язків.
            # Використовуємо selectinload для отримання фінального об'єкта для відповіді.
            final_rating_stmt = select(UserGroupRating).options(
                selectinload(UserGroupRating.user).options(selectinload(User.user_type)),
                selectinload(UserGroupRating.group)
            ).where(UserGroupRating.id == updated_orm_obj.id)

            refreshed_rating_db = (await self.db_session.execute(final_rating_stmt)).scalar_one_or_none()
            if not refreshed_rating_db: # Дуже малоймовірно
                 logger.critical(f"Не вдалося отримати щойно оновлений/створений рейтинг ID {updated_orm_obj.id}")
                 raise RuntimeError("Критична помилка: Не вдалося отримати рейтинг після збереження.")

        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності UserGroupRating для {log_ctx}: {e}", exc_info=settings.DEBUG)
            raise ValueError(f"Не вдалося оновити/створити рейтинг через конфлікт даних: {e}")
        except Exception as e:
            await self.rollback()
            logger.error(f"Неочікувана помилка при коміті рейтингу для {log_ctx}: {e}", exc_info=settings.DEBUG)
            raise

        logger.info(f"UserGroupRating для {log_ctx} успішно встановлено на бал {new_score}.")
        return UserGroupRatingResponse.model_validate(refreshed_rating_db)

    async def get_group_leaderboard(
            self,
            group_id: int, # Змінено UUID на int
            rating_type: RatingType = DEFAULT_RATING_TYPE,
            period_end_date: Optional[date] = None,
            limit: int = 100
    ) -> GroupLeaderboardResponse:
        """
        Генерує таблицю лідерів для вказаної групи та періоду.
        """
        log_ctx = f"група ID '{group_id}', тип '{rating_type.value}', дата кінця періоду '{period_end_date}'"
        logger.info(f"Генерація лідерборду для {log_ctx}, ліміт {limit}.")

        # Використовуємо репозиторій для отримання топ рейтингів
        # TODO: Переконатися, що get_top_ratings_for_group завантажує user.user_type
        # Якщо ні, то потрібно буде або розширити репо, або довантажувати в циклі (менш ефективно).
        # Поточний get_top_ratings_for_group не має selectinload.
        # Залишаємо прямий запит для збереження selectinload.

        stmt = select(UserGroupRating).options(
            selectinload(UserGroupRating.user).options(selectinload(User.user_type)),
        ).where(
            UserGroupRating.group_id == group_id,
            UserGroupRating.rating_type == rating_type
        )
        if period_end_date is not None:
            stmt = stmt.where(UserGroupRating.period_end_date == period_end_date)
        elif rating_type == RatingType.OVERALL: # Для OVERALL period_end_date має бути NULL
             stmt = stmt.where(UserGroupRating.period_end_date.is_(None))
        # Для інших типів, якщо period_end_date is None, це може означати "поточний відкритий період" - логіка потребує уточнення.
        # Поки що, якщо period_end_date is None і тип не OVERALL, фільтр по даті не додається (покаже всі періоди цього типу).

        stmt = stmt.order_by(
            UserGroupRating.rating_score.desc(),
            UserGroupRating.last_calculated_at.asc(),
            UserGroupRating.user_id.asc()
        ).limit(limit)
        ratings_db = (await self.db_session.execute(stmt)).scalars().all()

        leaderboard_entries = [UserGroupRatingResponse.model_validate(r) for r in ratings_db]

        # Загальна кількість учасників рейтингу для цієї групи та періоду
        # Використовуємо count з репозиторію (BaseRepository)
        filters_for_count: Dict[str, Any] = {
            "group_id": group_id,
            "rating_type": rating_type,
        }
        if period_end_date is not None:
            filters_for_count["period_end_date"] = period_end_date
        elif rating_type == RatingType.OVERALL:
            filters_for_count["period_end_date"] = None

        total_participants = await self.rating_repo.count(session=self.db_session, filters=filters_for_count)

        group_name = "N/A"
        group_obj = await self.db_session.get(Group, group_id) # Залишаємо пряме отримання Group
        if group_obj:
            group_name = group_obj.name

        return GroupLeaderboardResponse(
            group_id=group_id,
            group_name=group_name,
            period_identifier=f"{rating_type.value}:{period_end_date.isoformat() if period_end_date else 'all_time'}", # Формуємо ідентифікатор періоду
            ratings=leaderboard_entries,
            total_participants=total_participants,
            generated_at=datetime.now(timezone.utc)
        )

    # TODO: Розглянути метод для періодичного перерахунку всіх рейтингів (наприклад, раз на день або після значних подій).
    # async def recalculate_all_ratings_for_period(rating_type: RatingType, period_end_date: Optional[date] = None, group_id: Optional[int] = None): ...

logger.debug(f"{UserRatingService.__name__} (сервіс рейтингів користувачів) успішно визначено.")
