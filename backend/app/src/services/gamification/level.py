# backend/app/src/services/gamification/level.py
# import logging # Замінено на централізований логер
from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime, timezone  # Додано для updated_at

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload  # Додано для завантаження зв'язків

# Повні шляхи імпорту
from backend.app.src.services.dictionaries.base_dict import BaseDictionaryService
from backend.app.src.models.gamification.level import Level  # Модель SQLAlchemy Level
from backend.app.src.models.auth.user import User  # Для зв'язків created_by_user, updated_by_user
from backend.app.src.models.files.file import FileRecord  # Для зв'язку icon_file
from backend.app.src.models.groups.group import Group  # Для зв'язку group
from backend.app.src.schemas.gamification.level import (  # Схеми Pydantic
    LevelCreate,
    LevelUpdate,
    LevelResponse,
)
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings  # Для доступу до конфігурацій (наприклад, DEBUG)


class LevelService(BaseDictionaryService[Level, LevelCreate, LevelUpdate, LevelResponse]):
    """
    Сервіс для управління визначеннями Рівнів.
    Рівні зазвичай визначаються мінімальною кількістю балів, необхідних для їх досягнення,
    і мають назву, опис та, можливо, іконку.
    Успадковує та розширює CRUD-операції від BaseDictionaryService.
    Унікальність полів `name` та `min_points_required` перевіряється в межах групи
    (якщо `group_id` вказано) або глобально.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує сервіс LevelService.

        :param db_session: Асинхронна сесія бази даних SQLAlchemy.
        """
        super().__init__(db_session, model=Level, response_schema=LevelResponse)
        logger.info(f"LevelService ініціалізовано для моделі: {self._model_name}")

    async def _load_relations(self, query: select) -> select:
        """Допоміжний метод для додавання selectinload для зв'язків Level."""
        return query.options(
            selectinload(Level.icon_file),
            selectinload(Level.group),
            selectinload(Level.created_by_user).options(selectinload(User.user_type)),
            selectinload(Level.updated_by_user).options(selectinload(User.user_type))
        )

    async def get_by_id(self, item_id: UUID) -> Optional[LevelResponse]:
        """Отримує рівень за ID з усіма пов'язаними сутностями."""
        logger.debug(f"Спроба отримання {self._model_name} (Рівень) за ID: {item_id}")
        stmt = await self._load_relations(select(self.model).where(self.model.id == item_id))
        item_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if item_db:
            logger.info(f"{self._model_name} з ID '{item_id}' знайдено.")
            return self.response_schema.model_validate(item_db)
        logger.info(f"{self._model_name} з ID '{item_id}' не знайдено.")
        return None

    async def get_level_by_name(self, name: str, group_id: Optional[UUID] = None) -> Optional[LevelResponse]:
        """
        Отримує рівень за його унікальним ім'ям в межах групи або глобально.
        """
        logger.debug(f"Спроба отримання Рівня за ім'ям: '{name}', група ID: {group_id}")

        stmt = select(self.model).where(self.model.name == name)
        if group_id:
            stmt = stmt.where(self.model.group_id == group_id)
        else:
            stmt = stmt.where(self.model.group_id.is_(None))

        stmt = await self._load_relations(stmt)
        item_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if item_db:
            logger.info(f"{self._model_name} з ім'ям '{name}' (група ID: {group_id}) знайдено.")
            return self.response_schema.model_validate(item_db)
        logger.info(f"{self._model_name} з ім'ям '{name}' (група ID: {group_id}) не знайдено.")
        return None

    async def _check_uniqueness(self, name: str, min_points: int, group_id: Optional[UUID],
                                item_id_to_exclude: Optional[UUID] = None) -> None:
        """Перевіряє унікальність імені та min_points_required в межах групи або глобально."""
        # Перевірка імені
        stmt_name = select(self.model.id).where(self.model.name == name)
        # Перевірка min_points_required
        stmt_points = select(self.model.id).where(self.model.min_points_required == min_points)

        scope_log_msg = "глобальній області"  # i18n
        if group_id:
            stmt_name = stmt_name.where(self.model.group_id == group_id)
            stmt_points = stmt_points.where(self.model.group_id == group_id)
            scope_log_msg = f"групі ID '{group_id}'"  # i18n
        else:
            stmt_name = stmt_name.where(self.model.group_id.is_(None))
            stmt_points = stmt_points.where(self.model.group_id.is_(None))

        if item_id_to_exclude:  # При оновленні виключаємо поточний елемент
            stmt_name = stmt_name.where(self.model.id != item_id_to_exclude)
            stmt_points = stmt_points.where(self.model.id != item_id_to_exclude)

        existing_by_name = (await self.db_session.execute(stmt_name)).scalar_one_or_none()
        if existing_by_name:
            msg = f"{self._model_name} з ім'ям '{name}' вже існує в {scope_log_msg}."  # i18n
            logger.warning(msg)
            raise ValueError(msg)

        existing_by_points = (await self.db_session.execute(stmt_points)).scalar_one_or_none()
        if existing_by_points:
            msg = f"{self._model_name} з min_points_required '{min_points}' вже існує в {scope_log_msg}."  # i18n
            logger.warning(msg)
            raise ValueError(msg)

    async def create(self, data: LevelCreate, created_by_user_id: UUID) -> LevelResponse:
        """Створює новий рівень, перевіряючи унікальність name та min_points_required."""
        logger.debug(f"Спроба створення нового {self._model_name} (Рівень) з ім'ям: '{data.name}'")
        await self._check_uniqueness(data.name, data.min_points_required, data.group_id)

        if data.icon_file_id and not await self.db_session.get(FileRecord, data.icon_file_id):
            # i18n
            raise ValueError(f"Файл іконки з ID '{data.icon_file_id}' не знайдено.")

        new_item_db = self.model(
            **data.model_dump(),
            created_by_user_id=created_by_user_id,
            updated_by_user_id=created_by_user_id
        )
        self.db_session.add(new_item_db)
        try:
            await self.commit()
            refreshed_item = await self.get_by_id(new_item_db.id)  # Отримуємо з усіма зв'язками
            if not refreshed_item: raise RuntimeError("Не вдалося отримати створений рівень.")  # Малоймовірно
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності '{data.name}': {e}", exc_info=settings.DEBUG)
            raise ValueError(f"Не вдалося створити {self._model_name}: конфлікт даних.")  # i18n

        logger.info(f"{self._model_name} '{refreshed_item.name}' ID: {refreshed_item.id} успішно створено.")
        return refreshed_item

    async def update(self, item_id: UUID, data: LevelUpdate, updated_by_user_id: UUID) -> Optional[LevelResponse]:
        """Оновлює існуючий рівень."""
        logger.debug(f"Спроба оновлення {self._model_name} (Рівень) з ID: {item_id}")

        item_db = (await self.db_session.execute(
            select(self.model).where(self.model.id == item_id)
        )).scalar_one_or_none()

        if not item_db:
            logger.warning(f"{self._model_name} з ID '{item_id}' не знайдено для оновлення.")
            return None

        update_data = data.model_dump(exclude_unset=True)

        new_name = update_data.get('name', item_db.name)
        new_min_points = update_data.get('min_points_required', item_db.min_points_required)
        new_group_id = update_data.get('group_id', item_db.group_id)
        if 'group_id' not in update_data and item_db.group_id is not None:
            new_group_id = item_db.group_id

        # Перевірка унікальності, якщо name, min_points_required або group_id змінюються
        if ('name' in update_data and new_name != item_db.name) or \
                ('min_points_required' in update_data and new_min_points != item_db.min_points_required) or \
                ('group_id' in update_data and new_group_id != item_db.group_id):
            await self._check_uniqueness(new_name, new_min_points, new_group_id, item_id_to_exclude=item_id)

        if 'icon_file_id' in update_data and update_data['icon_file_id'] is not None \
                and update_data['icon_file_id'] != item_db.icon_file_id:
            if not await self.db_session.get(FileRecord, update_data['icon_file_id']):
                # i18n
                raise ValueError(f"Файл іконки з ID '{update_data['icon_file_id']}' не знайдено.")

        for field, value in update_data.items():
            setattr(item_db, field, value)

        item_db.updated_by_user_id = updated_by_user_id
        item_db.updated_at = datetime.now(timezone.utc)

        self.db_session.add(item_db)
        try:
            await self.commit()
            refreshed_item = await self.get_by_id(item_db.id)  # Отримуємо з усіма зв'язками
            if not refreshed_item: raise RuntimeError("Не вдалося отримати оновлений рівень.")  # Малоймовірно
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності ID '{item_id}': {e}", exc_info=settings.DEBUG)
            raise ValueError(f"Не вдалося оновити {self._model_name}: конфлікт даних.")  # i18n

        logger.info(f"{self._model_name} '{refreshed_item.name}' ID: {refreshed_item.id} успішно оновлено.")
        return refreshed_item

    async def get_levels_ordered_by_points(self, group_id: Optional[UUID] = None, ascending: bool = True, skip: int = 0,
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

        if not hasattr(self.model, 'min_points_required'):
            logger.error(f"Модель {self._model_name} не має атрибута 'min_points_required'.")
            return []

        stmt = select(self.model)
        conditions = []
        if group_id is not None:  # Показати рівні вказаної групи + глобальні
            conditions.append(or_(self.model.group_id == group_id, self.model.group_id.is_(None)))
        if conditions:
            stmt = stmt.where(*conditions)

        order_field = self.model.min_points_required
        if not ascending:
            order_field = self.model.min_points_required.desc()

        # Додаткове сортування за level_order для стабільності або якщо точки однакові
        secondary_order_field = getattr(self.model, 'level_order', self.model.id)
        stmt = stmt.order_by(order_field, secondary_order_field).offset(skip).limit(limit)
        stmt = await self._load_relations(stmt)  # Завантажуємо зв'язки
        items_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        return [self.response_schema.model_validate(item) for item in items_db]

    async def get_level_for_points(self, points: int, group_id: Optional[UUID] = None) -> Optional[LevelResponse]:
        """
        Визначає відповідний рівень для заданої кількості балів у контексті групи (або глобально).
        Знаходить найвищий рівень, де min_points_required <= points.
        Враховує `level_order` для розв'язання нічиїх за балами.
        """
        logger.debug(f"Визначення рівня для {points} балів, група ID: {group_id}")

        if not hasattr(self.model, 'min_points_required') or not hasattr(self.model, 'level_order'):
            logger.error(f"Модель {self._model_name} не має 'min_points_required' або 'level_order'.")
            return None

        stmt = select(self.model).where(self.model.min_points_required <= points)

        # Фільтрація за групою: рівні цієї групи АБО глобальні рівні
        conditions = [or_(self.model.group_id == group_id, self.model.group_id.is_(None))]
        # Якщо group_id не надано, то group_id is None, що означає пошук тільки серед глобальних рівнів.
        if group_id is None:
            conditions = [self.model.group_id.is_(None)]

        stmt = stmt.where(*conditions)

        # Сортування: спочатку за спаданням балів, потім за спаданням level_order (вища перевага), потім за ID
        stmt = stmt.order_by(
            self.model.min_points_required.desc(),
            self.model.level_order.desc(),  # Припускаємо, що вищий level_order кращий
            self.model.id.desc()  # Для детермінізму
        )
        stmt = await self._load_relations(stmt)  # Завантажуємо зв'язки
        level_db = (await self.db_session.execute(stmt)).scalars().first()  # Беремо перший (найвищий підходящий)

        if level_db:
            logger.info(
                f"Рівень '{level_db.name}' (ID: {level_db.id}) визначено для {points} балів (група ID: {group_id}).")
            return self.response_schema.model_validate(level_db)

        logger.info(f"Специфічний рівень для {points} балів не знайдено (група ID: {group_id}).")
        return None

    # `delete` успадковується.
    # TODO: Розглянути захист від видалення рівнів, якщо вони вже присвоєні користувачам
    # (через UserLevel) або якщо є залежні правила.


logger.debug(f"{LevelService.__name__} (сервіс рівнів) успішно визначено.")
