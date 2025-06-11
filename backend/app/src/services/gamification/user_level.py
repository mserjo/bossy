# backend/app/src/services/gamification/user_level.py
# import logging # Замінено на централізований логер
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal  # Для балів користувача

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, noload
from sqlalchemy.exc import IntegrityError

# Повні шляхи імпорту
from backend.app.src.services.base import BaseService
from backend.app.src.models.gamification.user_level import UserLevel  # Модель SQLAlchemy UserLevel
from backend.app.src.models.gamification.level import Level  # Для визначень рівнів
from backend.app.src.models.auth.user import User
from backend.app.src.models.groups.group import Group  # Якщо рівні залежать від групи

from backend.app.src.schemas.gamification.user_level import UserLevelResponse
from backend.app.src.schemas.gamification.level import LevelResponse  # Для вкладених деталей рівня

from backend.app.src.services.bonuses.account import UserAccountService  # Для отримання балів
from backend.app.src.services.gamification.level import LevelService  # Для отримання визначень рівнів

from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings  # Для доступу до конфігурацій (наприклад, DEBUG)


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
        logger.info("UserLevelService ініціалізовано.")

    async def _get_orm_user_level(self, user_id: UUID, group_id: Optional[UUID] = None, load_relations: bool = True) -> \
    Optional[UserLevel]:
        """Внутрішній метод для отримання ORM моделі UserLevel."""
        stmt = select(UserLevel).where(UserLevel.user_id == user_id)

        # Фільтрація за group_id: якщо group_id надано, шукаємо запис для цієї групи.
        # Якщо group_id є None, шукаємо глобальний запис UserLevel (де group_id IS NULL).
        if group_id:
            stmt = stmt.where(UserLevel.group_id == group_id)
        else:
            stmt = stmt.where(UserLevel.group_id.is_(None))

        if load_relations:
            options_to_load = [
                selectinload(UserLevel.user).options(selectinload(User.user_type)),
                selectinload(UserLevel.level).options(
                    selectinload(Level.icon_file),  # Завантажуємо іконку рівня
                    selectinload(Level.group)  # Завантажуємо групу визначення рівня (якщо є)
                )
            ]
            if group_id:  # Завантажуємо групу самого UserLevel, якщо вона є
                options_to_load.append(selectinload(UserLevel.group))
            stmt = stmt.options(*options_to_load)

        return (await self.db_session.execute(stmt)).scalar_one_or_none()

    async def get_user_level(
            self,
            user_id: UUID,
            group_id: Optional[UUID] = None  # None для глобального рівня користувача
    ) -> Optional[UserLevelResponse]:
        """
        Отримує поточний рівень користувача для вказаного контексту (глобально або для групи).

        :param user_id: ID користувача.
        :param group_id: ID групи (None для глобального контексту).
        :return: Pydantic схема UserLevelResponse або None, якщо рівень не присвоєно.
        """
        log_ctx_parts = [f"користувач ID '{user_id}'"]
        if group_id:
            log_ctx_parts.append(f"група ID '{group_id}'")
        else:
            log_ctx_parts.append("(глобальний контекст)")
        log_ctx = ", ".join(log_ctx_parts)
        logger.debug(f"Спроба отримання UserLevel для {log_ctx}.")

        user_level_db = await self._get_orm_user_level(user_id, group_id, load_relations=True)

        if user_level_db:
            level_name = getattr(user_level_db.level, 'name', 'N/A') if user_level_db.level else 'N/A'
            logger.info(f"Запис UserLevel знайдено для {log_ctx} (Рівень: {level_name}).")
            return UserLevelResponse.model_validate(user_level_db)  # Pydantic v2

        logger.info(f"Запис UserLevel не знайдено для {log_ctx}.")
        return None

    async def update_user_level(
            self,
            user_id: UUID,
            group_id: Optional[UUID] = None,  # None для глобального контексту
    ) -> Optional[UserLevelResponse]:  # Може повернути None, якщо балів недостатньо для будь-якого рівня
        """
        Оновлює (або створює/видаляє) запис про рівень користувача на основі його поточних балів.

        :param user_id: ID користувача.
        :param group_id: ID групи (None для глобального контексту).
        :return: Pydantic схема UserLevelResponse оновленого/створеного рівня або None.
        :raises ValueError: Якщо виникає конфлікт даних при збереженні. # i18n
        """
        log_ctx_parts = [f"користувач ID '{user_id}'"]
        if group_id:
            log_ctx_parts.append(f"група ID '{group_id}'")
        else:
            log_ctx_parts.append("(глобальний контекст)")
        log_ctx = ", ".join(log_ctx_parts)
        logger.info(f"Спроба оновлення рівня для {log_ctx}.")

        # 1. Отримати поточні бали користувача для цього контексту (група або глобально)
        #    `group_id` для `account_service.get_user_account` відповідає контексту рівня.
        user_account = await self.account_service.get_user_account(user_id, group_id=group_id)
        current_points_value = user_account.balance if user_account else Decimal("0.00")
        logger.info(f"Поточні бали для {log_ctx}: {current_points_value}")

        # 2. Визначити цільовий рівень на основі балів та контексту групи
        #    `group_id` для `level_service.get_level_for_points` також відповідає контексту.
        target_level_schema: Optional[LevelResponse] = await self.level_service.get_level_for_points(
            points=int(current_points_value),  # get_level_for_points очікує int
            group_id=group_id
        )

        # 3. Отримати існуючий запис UserLevel для цього контексту
        existing_user_level_db = await self._get_orm_user_level(user_id, group_id,
                                                                load_relations=False)  # Зв'язки не потрібні для логіки

        current_time = datetime.now(timezone.utc)

        if not target_level_schema:  # Балів недостатньо для будь-якого рівня
            logger.info(f"Для {current_points_value} балів не визначено жодного рівня ({log_ctx}).")
            if existing_user_level_db:  # Якщо був попередній рівень, його треба видалити
                logger.info(
                    f"Видалення існуючого запису UserLevel ID {existing_user_level_db.id} для {log_ctx}, оскільки балів недостатньо.")
                await self.db_session.delete(existing_user_level_db)
                await self.commit()
            return None  # Рівень не присвоєно або видалено

        # Цільовий рівень визначено
        if existing_user_level_db:  # Якщо запис UserLevel існує
            if existing_user_level_db.level_id == target_level_schema.id:
                logger.info(f"{log_ctx} вже на потрібному рівні: '{target_level_schema.name}'. Оновлення не потрібне.")
                # Повертаємо поточний стан з завантаженими зв'язками
                return await self.get_user_level(user_id, group_id)
            else:  # Рівень змінився
                logger.info(
                    f"Оновлення рівня для {log_ctx} з ID '{existing_user_level_db.level_id}' на новий ID '{target_level_schema.id}' ('{target_level_schema.name}').")
                existing_user_level_db.level_id = target_level_schema.id
                existing_user_level_db.achieved_at = current_time  # Оновлюємо час досягнення нового рівня
                # `updated_at` оновлюється автоматично моделлю
                user_level_to_save = existing_user_level_db
        else:  # Створюємо новий запис UserLevel
            logger.info(
                f"Створення нового запису UserLevel для {log_ctx} на рівні ID '{target_level_schema.id}' ('{target_level_schema.name}').")
            user_level_to_save = UserLevel(
                user_id=user_id,
                level_id=target_level_schema.id,
                group_id=group_id,  # Буде None для глобального контексту
                achieved_at=current_time
                # `created_at`, `updated_at` встановлюються моделлю
            )
            self.db_session.add(user_level_to_save)

        try:
            await self.commit()
            # Отримуємо оновлений/створений запис з усіма зв'язками для відповіді
            refreshed_user_level = await self._get_orm_user_level(user_id, group_id, load_relations=True)
            if not refreshed_user_level:  # Малоймовірно, якщо коміт пройшов
                logger.error(f"Не вдалося отримати UserLevel для {log_ctx} після коміту.")
                # i18n
                raise RuntimeError("Помилка оновлення рівня: не вдалося отримати запис після збереження.")
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності UserLevel для {log_ctx}: {e}", exc_info=settings.DEBUG)
            # i18n
            raise ValueError(f"Не вдалося оновити/створити рівень користувача через конфлікт даних: {e}")

        logger.info(f"Рівень для {log_ctx} успішно встановлено на '{target_level_schema.name}'.")
        return UserLevelResponse.model_validate(refreshed_user_level)  # Pydantic v2

    async def list_users_at_level(
            self,
            level_id: UUID,
            group_id: Optional[UUID] = None,  # None для глобального контексту рівня
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
