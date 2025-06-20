# backend/app/src/services/gamification/level.py
from typing import List, Optional, Any
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError # Додано для обробки помилок

from backend.app.src.services.base import BaseService # Змінено на BaseService
from backend.app.src.models.gamification.level import Level  # Модель SQLAlchemy Level
from backend.app.src.repositories.gamification.level_repository import LevelRepository # Імпорт репозиторію
from backend.app.src.models.auth.user import User  # Для зв'язків created_by_user, updated_by_user
from backend.app.src.models.files.file import FileRecord  # Для зв'язку icon_file
from backend.app.src.models.groups.group import Group  # Для зв'язку group
from backend.app.src.schemas.gamification.level import (  # Схеми Pydantic
    LevelCreate,
    LevelUpdate,
    LevelResponse,
)
from backend.app.src.config import settings  # Для доступу до конфігурацій (наприклад, DEBUG)
from backend.app.src.config.logging import get_logger
from backend.app.src.core.i18n import _ # Added import
logger = get_logger(__name__)


class LevelService(BaseService): # Змінено успадкування на BaseService
    """
    Сервіс для управління визначеннями Рівнів.
    Рівні зазвичай визначаються мінімальною кількістю балів, необхідних для їх досягнення,
    і мають назву, опис та, можливо, іконку.
    Унікальність полів `name` та `min_points_required` перевіряється в межах групи
    (якщо `group_id` вказано) або глобально.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує сервіс LevelService.

        :param db_session: Асинхронна сесія бази даних SQLAlchemy.
        """
        super().__init__(db_session) # Передаємо тільки db_session
        self.level_repo = LevelRepository() # Ініціалізуємо репозиторій
        self.response_schema = LevelResponse # Зберігаємо схему відповіді
        self._model_name = Level.__name__ # Встановлюємо ім'я моделі
        logger.info(f"LevelService ініціалізовано для моделі: {self._model_name}")

    async def _load_relations(self, query: select) -> select: # select з sqlalchemy
        """Допоміжний метод для додавання selectinload для зв'язків Level."""
        return query.options(
            selectinload(Level.icon_file),
            selectinload(Level.group),
            selectinload(Level.created_by_user).options(selectinload(User.user_type)),
            selectinload(Level.updated_by_user).options(selectinload(User.user_type))
        )

    async def get_by_id(self, item_id: int) -> Optional[LevelResponse]: # Змінено UUID на int
        """Отримує рівень за ID з усіма пов'язаними сутностями."""
        logger.debug(f"Спроба отримання {self._model_name} (Рівень) за ID: {item_id}")
        # Залишаємо прямий запит для _load_relations
        stmt = await self._load_relations(select(self.level_repo.model).where(self.level_repo.model.id == item_id))
        item_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if item_db:
            logger.info(f"{self._model_name} з ID '{item_id}' знайдено.")
            return self.response_schema.model_validate(item_db)
        logger.info(f"{self._model_name} з ID '{item_id}' не знайдено.")
        return None

    async def get_level_by_name(self, name: str, group_id: Optional[int] = None) -> Optional[LevelResponse]: # Змінено UUID на int
        """
        Отримує рівень за його унікальним ім'ям в межах групи або глобально.
        """
        logger.debug(f"Спроба отримання Рівня за ім'ям: '{name}', група ID: {group_id}")
        # Залишаємо прямий запит для _load_relations
        stmt = select(self.level_repo.model).where(self.level_repo.model.name == name)
        if group_id:
            stmt = stmt.where(self.level_repo.model.group_id == group_id)
        else:
            stmt = stmt.where(self.level_repo.model.group_id.is_(None))

        stmt = await self._load_relations(stmt)
        item_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if item_db:
            logger.info(f"{self._model_name} з ім'ям '{name}' (група ID: {group_id}) знайдено.")
            return self.response_schema.model_validate(item_db)
        logger.info(f"{self._model_name} з ім'ям '{name}' (група ID: {group_id}) не знайдено.")
        return None

    async def _check_uniqueness(self, name: str, min_points: int, group_id: Optional[int], # Змінено UUID на int
                                item_id_to_exclude: Optional[int] = None) -> None: # Змінено UUID на int
        """Перевіряє унікальність імені та min_points_required в межах групи або глобально."""
        # Перевірка імені - використовуємо get_level_by_name (який робить прямий запит)
        existing_by_name = await self.get_level_by_name(name, group_id)
        if existing_by_name and (item_id_to_exclude is None or existing_by_name.id != item_id_to_exclude):
            scope_log_msg = _("in_group_scope", group_id=group_id) if group_id else _("global_scope")
            msg = _("gamification.level.errors.name_exists_in_scope", model_name=self._model_name, name=name, scope=scope_log_msg)
            logger.warning(f"{self._model_name} with name '{name}' already exists in {scope_log_msg}.") # Log can be more detailed
            raise ValueError(msg)

        # Перевірка min_points_required - використовуємо новий метод репозиторію
        existing_by_points = await self.level_repo.find_by_min_points_and_group(
            session=self.db_session, min_points=min_points, group_id=group_id
        )
        if existing_by_points and (item_id_to_exclude is None or existing_by_points.id != item_id_to_exclude):
            scope_log_msg = _("in_group_scope", group_id=group_id) if group_id else _("global_scope")
            msg = _("gamification.level.errors.min_points_exists_in_scope", model_name=self._model_name, points=min_points, scope=scope_log_msg)
            logger.warning(f"{self._model_name} with min_points_required '{min_points}' already exists in {scope_log_msg}.") # Log can be more detailed
            raise ValueError(msg)

    async def create(self, data: LevelCreate, created_by_user_id: int) -> LevelResponse: # Змінено UUID на int
        """Створює новий рівень, перевіряючи унікальність name та min_points_required."""
        logger.debug(f"Спроба створення нового {self._model_name} (Рівень) з ім'ям: '{data.name}'")
        await self._check_uniqueness(data.name, data.min_points_required, data.group_id)

        if data.icon_file_id and not await self.db_session.get(FileRecord, data.icon_file_id):
            raise ValueError(_("gamification.level.errors.icon_file_not_found", file_id=data.icon_file_id))

        try:
            new_item_db = await self.level_repo.create(
                session=self.db_session,
                obj_in=data,
                created_by_user_id=created_by_user_id,
                updated_by_user_id=created_by_user_id # При створенні
            )
            await self.commit()
            refreshed_item = await self.get_by_id(new_item_db.id)
            if not refreshed_item: raise RuntimeError(_("gamification.level.errors.critical_create_failed"))
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності '{data.name}': {e}", exc_info=settings.DEBUG)
            raise ValueError(_("gamification.level.errors.create_conflict", model_name=self._model_name, error_message=str(e)))

        logger.info(f"{self._model_name} '{refreshed_item.name}' ID: {refreshed_item.id} успішно створено.")
        return refreshed_item

    async def update(self, item_id: int, data: LevelUpdate, updated_by_user_id: int) -> Optional[LevelResponse]: # Змінено UUID на int
        """Оновлює існуючий рівень."""
        logger.debug(f"Спроба оновлення {self._model_name} (Рівень) з ID: {item_id}")

        item_db = await self.level_repo.get(session=self.db_session, id=item_id)

        if not item_db:
            logger.warning(f"{self._model_name} з ID '{item_id}' не знайдено для оновлення.")
            return None

        update_data_dict = data.model_dump(exclude_unset=True)

        new_name = update_data_dict.get('name', item_db.name)
        new_min_points = update_data_dict.get('min_points_required', item_db.min_points_required)
        new_group_id = update_data_dict.get('group_id') if 'group_id' in update_data_dict else item_db.group_id


        if ('name' in update_data_dict and new_name != item_db.name) or \
                ('min_points_required' in update_data_dict and new_min_points != item_db.min_points_required) or \
                ('group_id' in update_data_dict and new_group_id != item_db.group_id):
            await self._check_uniqueness(new_name, new_min_points, new_group_id, item_id_to_exclude=item_id)

        if 'icon_file_id' in update_data_dict and update_data_dict['icon_file_id'] is not None \
                and update_data_dict['icon_file_id'] != item_db.icon_file_id:
            if not await self.db_session.get(FileRecord, update_data_dict['icon_file_id']):
                raise ValueError(_("gamification.level.errors.icon_file_not_found", file_id=update_data_dict['icon_file_id']))

        # Оновлюємо через репозиторій
        # updated_at буде оброблено автоматично TimestampedMixin в BaseRepository.update
        try:
            updated_item_db = await self.level_repo.update(
                session=self.db_session,
                db_obj=item_db,
                obj_in=data, # Передаємо Pydantic схему LevelUpdate
                updated_by_user_id=updated_by_user_id
            )
            await self.commit()
            refreshed_item = await self.get_by_id(updated_item_db.id)
            if not refreshed_item: raise RuntimeError(_("gamification.level.errors.critical_update_failed"))
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності ID '{item_id}': {e}", exc_info=settings.DEBUG)
            raise ValueError(_("gamification.level.errors.update_conflict", model_name=self._model_name, error_message=str(e)))

        logger.info(f"{self._model_name} '{refreshed_item.name}' ID: {refreshed_item.id} успішно оновлено.")
        return refreshed_item

    async def get_levels_ordered_by_points(self, group_id: Optional[int] = None, ascending: bool = True, skip: int = 0, # Змінено UUID на int
                                           limit: int = 100) -> List[LevelResponse]:
        """
        Отримує всі рівні, відсортовані за min_points_required.
        Може фільтрувати за групою (показує рівні групи + глобальні, або тільки глобальні, або тільки групові).
        """
        # TODO: Уточнити логіку фільтрації group_id: включати глобальні, тільки глобальні, або тільки групові?
        # Наразі: якщо group_id вказано, показує рівні цієї групи ТА глобальні.
        # Якщо group_id не вказано, показує ВСІ рівні (всіх груп та глобальні).
        # Якщо потрібно тільки глобальні, коли group_id is None, потрібен дод. параметр global_only=True.

        log_msg = f"група ID: {group_id}, сортування: {'ASC' if ascending else 'DESC'}"
        logger.debug(f"Отримання всіх рівнів, відсортованих за балами ({log_msg})")

        if not hasattr(self.level_repo.model, 'min_points_required'): # Використовуємо self.level_repo.model
            logger.error(f"Модель {self._model_name} не має атрибута 'min_points_required'.")
            return []

        # Залишаємо прямий запит через складність фільтрації та сортування, що може не покриватися get_multi
        stmt = select(self.level_repo.model)
        conditions = []
        if group_id is not None:
            conditions.append(or_(self.level_repo.model.group_id == group_id, self.level_repo.model.group_id.is_(None)))
        if conditions:
            stmt = stmt.where(*conditions)

        order_field = self.level_repo.model.min_points_required
        if not ascending:
            order_field = self.level_repo.model.min_points_required.desc()

        secondary_order_field = getattr(self.level_repo.model, 'level_order', self.level_repo.model.id)
        stmt = stmt.order_by(order_field, secondary_order_field).offset(skip).limit(limit)
        stmt = await self._load_relations(stmt)
        items_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        return [self.response_schema.model_validate(item) for item in items_db]

    async def get_level_for_points(self, points: int, group_id: Optional[int] = None) -> Optional[LevelResponse]: # Змінено UUID на int
        """
        Визначає відповідний рівень для заданої кількості балів у контексті групи (або глобально).
        Знаходить найвищий рівень, де min_points_required <= points.
        Враховує `level_order` для розв'язання нічиїх за балами.
        """
        logger.debug(f"Визначення рівня для {points} балів, група ID: {group_id}")

        # Використовуємо метод репозиторію
        level_db = await self.level_repo.get_level_by_points(
            session=self.db_session, points=points, group_id=group_id
        )

        if level_db:
            # Якщо потрібно завантажити зв'язки для відповіді, які не завантажує репозиторій
            # (get_level_by_points в репо не має _load_relations)
            # Тоді робимо це через get_by_id сервісу:
            level_response = await self.get_by_id(level_db.id)
            if level_response:
                logger.info(
                    f"Рівень '{level_response.name}' (ID: {level_response.id}) визначено для {points} балів (група ID: {group_id}).")
                return level_response
            else: # Малоймовірно, якщо level_db щойно знайдено
                logger.error(f"Не вдалося перезавантажити рівень ID {level_db.id} зі зв'язками.")
                return None # Або повернути відповідь на основі level_db без повних зв'язків

        logger.info(f"Специфічний рівень для {points} балів не знайдено (група ID: {group_id}).")
        return None

    # `delete` успадковується.
    # TODO: Розглянути захист від видалення рівнів, якщо вони вже присвоєні користувачам
    # (через UserLevel) або якщо є залежні правила.


logger.debug(f"{LevelService.__name__} (сервіс рівнів) успішно визначено.")
