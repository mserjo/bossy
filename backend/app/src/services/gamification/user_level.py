# backend/app/src/services/gamification/user_level.py
"""
Сервіс для управління рівнями користувачів в системі гейміфікації.

Відповідає за розрахунок, оновлення та отримання інформації
про рівні, досягнуті користувачами, на основі їхніх балів або інших критеріїв.
"""
from typing import List, Optional # Tuple, Any, UUID видалено
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, noload
from sqlalchemy.exc import IntegrityError

from backend.app.src.services.base import BaseService
from backend.app.src.models.gamification.user_level import UserLevel
from backend.app.src.repositories.gamification.user_level_repository import UserLevelRepository # Імпорт репозиторію
from backend.app.src.models.gamification.level import Level
from backend.app.src.models.auth.user import User
from backend.app.src.models.groups.group import Group

from backend.app.src.schemas.gamification.user_level import (
    UserLevelResponse,
    UserLevelCreateSchema,
)
from backend.app.src.schemas.gamification.level import LevelResponse

from backend.app.src.services.bonuses.account import UserAccountService
from backend.app.src.services.gamification.level import LevelService

from backend.app.src.config import settings
from backend.app.src.config.logging import get_logger
from backend.app.src.core.i18n import _
logger = get_logger(__name__)


class UserLevelService(BaseService):
    """
    Сервіс для управління рівнями користувачів на основі їхніх накопичених балів або досягнень.
    Обробляє розрахунок та оновлення записів UserLevel.
    Кожен користувач може мати один запис UserLevel для кожного контексту (глобально або на групу).
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        self.account_service = UserAccountService(db_session)
        self.level_service = LevelService(db_session)
        self.user_level_repo = UserLevelRepository() # Ініціалізація репозиторію
        logger.info("UserLevelService ініціалізовано.")

    async def _get_orm_user_level_with_relations(self, user_level_id: int) -> Optional[UserLevel]:
        """Внутрішній метод для отримання ORM моделі UserLevel з усіма зв'язками за ID запису UserLevel."""
        # Цей метод потрібен для консистентного завантаження зв'язків для відповіді.
        # Репозиторійний get() може не завантажувати всі необхідні глибинні зв'язки.
        stmt = select(UserLevel).options(
            selectinload(UserLevel.user).options(selectinload(User.user_type)),
            selectinload(UserLevel.level).options(
                selectinload(Level.icon_file),
                selectinload(Level.group) # Зв'язок рівня з групою, якщо є
            ),
            selectinload(UserLevel.group) # Зв'язок UserLevel з групою, якщо є
        ).where(UserLevel.id == user_level_id)
        try:
            result = await self.db_session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Помилка при отриманні UserLevel ID {user_level_id} зі зв'язками: {e}", exc_info=settings.DEBUG)
            return None


    async def get_user_level_record(
            self,
            user_id: int,
            group_id: Optional[int] = None
    ) -> Optional[UserLevel]: # Повертає ORM модель
        """Отримує ORM модель UserLevel для користувача в контексті. Використовує репозиторій."""
        # Цей метод буде використовуватися всередині update_user_level
        # Репозиторійний метод get_current_level_for_user_in_group може бути не зовсім те,
        # що потрібно, якщо він сортує за level_number, а нам потрібен просто запис.
        # Якщо UserLevel унікальний по user_id, group_id, то простий filter потрібен.
        # Припускаємо, що UserLevel має бути унікальним по (user_id, group_id).
        # Використовуємо новий метод репозиторію.
        return await self.user_level_repo.get_by_user_and_group(
            session=self.db_session,
            user_id=user_id,
            group_id=group_id
        )


    async def get_user_level(
            self,
            user_id: int, # Змінено UUID на int
            group_id: Optional[int] = None # Змінено UUID на int
    ) -> Optional[UserLevelResponse]:
        """
        Отримує поточний рівень користувача для вказаного контексту (глобально або для групи).
        """
        log_ctx_parts = [f"користувач ID '{user_id}'"]
        if group_id:
            log_ctx_parts.append(f"група ID '{group_id}'")
        else:
            log_ctx_parts.append("(глобальний контекст)")
        log_ctx = ", ".join(log_ctx_parts)
        logger.debug(f"Спроба отримання UserLevel для {log_ctx}.")
        try:
            # Використовуємо get_user_level_record для отримання ORM моделі без зв'язків,
            # а потім _get_orm_user_level_with_relations для завантаження зв'язків для відповіді.
            user_level_base = await self.get_user_level_record(user_id, group_id)

            if user_level_base:
                user_level_db_with_relations = await self._get_orm_user_level_with_relations(user_level_base.id)
                if user_level_db_with_relations:
                    level_name = getattr(user_level_db_with_relations.level, 'name', 'N/A') if user_level_db_with_relations.level else 'N/A'
                    logger.info(f"Запис UserLevel знайдено для {log_ctx} (Рівень: {level_name}).")
                    return UserLevelResponse.model_validate(user_level_db_with_relations)
                else: # Малоймовірно, якщо user_level_base знайдено
                    logger.error(f"Не вдалося перезавантажити UserLevel ID {user_level_base.id} зі зв'язками.")


            logger.info(f"Запис UserLevel не знайдено для {log_ctx}.")
            return None
        except Exception as e:
            logger.error(f"Помилка при отриманні UserLevel для {log_ctx}: {e}", exc_info=settings.DEBUG)
            return None

    async def update_user_level(
            self,
            user_id: int, # Змінено UUID на int
            group_id: Optional[int] = None, # Змінено UUID на int
    ) -> Optional[UserLevelResponse]:
        """
        Оновлює (або створює/видаляє) запис про рівень користувача на основі його поточних балів.
        """
        log_ctx_parts = [f"користувач ID '{user_id}'"]
        if group_id:
            log_ctx_parts.append(f"група ID '{group_id}'")
        else:
            log_ctx_parts.append("(глобальний контекст)")
        log_ctx = ", ".join(log_ctx_parts)
        logger.info(f"Спроба оновлення рівня для {log_ctx}.")

        user_account = await self.account_service.get_user_account(user_id, group_id=group_id)
        current_points_value = user_account.balance if user_account else Decimal("0.00")
        logger.info(f"Поточні бали для {log_ctx}: {current_points_value}")

        target_level_schema: Optional[LevelResponse] = await self.level_service.get_level_for_points(
            points=int(current_points_value),
            group_id=group_id
        )

        existing_user_level_db = await self.get_user_level_record(user_id, group_id)
        current_time = datetime.now(timezone.utc)
        saved_user_level_orm: Optional[UserLevel] = None

        try:
            if not target_level_schema:
                logger.info(f"Для {current_points_value} балів не визначено жодного рівня ({log_ctx}).")
                if existing_user_level_db:
                    logger.info(f"Видалення існуючого запису UserLevel ID {existing_user_level_db.id} для {log_ctx}.")
                    await self.user_level_repo.remove(session=self.db_session, id=existing_user_level_db.id)
                    await self.commit()
                return None

            if existing_user_level_db:
                if existing_user_level_db.level_id == target_level_schema.id:
                    logger.info(f"{log_ctx} вже на потрібному рівні: '{target_level_schema.name}'. Оновлення не потрібне.")
                    saved_user_level_orm = existing_user_level_db
                else:
                    logger.info(
                        f"Оновлення рівня для {log_ctx} з ID '{existing_user_level_db.level_id}' на новий ID '{target_level_schema.id}' ('{target_level_schema.name}').")
                    # UserLevelUpdateSchema - порожня, тому оновлюємо поля напряму або через dict
                    # BaseRepository.update очікує Pydantic схему або dict.
                    # Оскільки UserLevelUpdateSchema порожня, ми не можемо її використовувати.
                    # Тому оновлюємо поля напряму на ORM об'єкті.
                    existing_user_level_db.level_id = target_level_schema.id
                    existing_user_level_db.achieved_at = current_time
                    # updated_at оновлюється автоматично через TimestampedMixin
                    self.db_session.add(existing_user_level_db) # Додаємо до сесії для відстеження
                    saved_user_level_orm = existing_user_level_db
            else:
                logger.info(
                    f"Створення нового запису UserLevel для {log_ctx} на рівні ID '{target_level_schema.id}' ('{target_level_schema.name}').")
                create_schema = UserLevelCreateSchema(
                    user_id=user_id,
                    level_id=target_level_schema.id,
                    group_id=group_id,
                    achieved_at=current_time
                )
                saved_user_level_orm = await self.user_level_repo.create(session=self.db_session, obj_in=create_schema)

            if saved_user_level_orm: # Тільки якщо є що зберігати (новий або змінений)
                 await self.commit()
                 # Потрібно перезавантажити зі зв'язками для відповіді
                 refreshed_user_level = await self._get_orm_user_level_with_relations(saved_user_level_orm.id)
                 if not refreshed_user_level:
                     logger.error(f"Не вдалося отримати UserLevel ID {saved_user_level_orm.id} зі зв'язками після коміту.")
                     raise RuntimeError(_("gamification.user_level.errors.critical_update_failed"))
                 logger.info(f"Рівень для {log_ctx} успішно встановлено на '{target_level_schema.name}'.")
                 return UserLevelResponse.model_validate(refreshed_user_level)
            else: # Якщо рівень не змінився і не було чого зберігати
                 return await self.get_user_level(user_id, group_id) # Повертаємо поточний стан

        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності UserLevel для {log_ctx}: {e}", exc_info=settings.DEBUG)
            raise ValueError(_("gamification.user_level.errors.update_create_conflict", error_message=str(e)))
        except Exception as e: # Обробка інших можливих помилок
            await self.rollback()
            logger.error(f"Неочікувана помилка при оновленні рівня для {log_ctx}: {e}", exc_info=settings.DEBUG)
            raise


    async def list_users_at_level(
            self,
            level_id: int, # Змінено UUID на int
            group_id: Optional[int] = None, # Змінено UUID на int
            skip: int = 0,
            limit: int = 100
    ) -> List[UserLevelResponse]:
        """
        Перелічує всіх користувачів, які досягли вказаного рівня в заданому контексті.

        :param level_id: ID рівня.
        :param group_id: ID групи (None для глобального контексту).
        :param skip: Кількість записів для пропуску.
        :param limit: Максимальна кількість записів.
        :return: Список Pydantic схем UserLevelResponse.
        """
        log_ctx_parts = [f"рівень ID '{level_id}'"]
        if group_id:
            log_ctx_parts.append(f"група ID '{group_id}'")
        else:
            log_ctx_parts.append("(глобальний контекст)")
        log_ctx = ", ".join(log_ctx_parts)
        logger.debug(f"Перелік користувачів на {log_ctx}, пропустити={skip}, ліміт={limit}.")

        stmt = select(UserLevel).options(
            selectinload(UserLevel.user).options(selectinload(User.user_type)),
            selectinload(UserLevel.level).options(selectinload(Level.icon_file)),  # Завантажуємо іконку рівня
            selectinload(UserLevel.group)  # Завантажуємо групу UserLevel, якщо є
        ).where(UserLevel.level_id == level_id)

        if group_id:
            stmt = stmt.where(UserLevel.group_id == group_id)
        else:
            stmt = stmt.where(UserLevel.group_id.is_(None))  # Явно для глобального контексту

        # Сортування за датою досягнення (новіші спочатку), потім за ID користувача
        stmt = stmt.order_by(UserLevel.achieved_at.desc(), UserLevel.user_id.asc()).offset(skip).limit(limit)
        user_levels_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        response_list = [UserLevelResponse.model_validate(ul) for ul in user_levels_db]  # Pydantic v2
        logger.info(f"Отримано {len(response_list)} користувачів на {log_ctx}.")
        return response_list

    # TODO: Розглянути метод для отримання історії рівнів користувача (якщо UserLevel записується при кожній зміні,
    # а не тільки оновлюється поточний). Поточна модель UserLevel передбачає один запис на user/group.


logger.debug(f"{UserLevelService.__name__} (сервіс рівнів користувачів) успішно визначено.")
