# backend/app/src/services/gamification/badge.py
# import logging # Замінено на централізований логер
from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime, timezone  # Додано для updated_at

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload  # Додано для завантаження зв'язків

# Повні шляхи імпорту
from backend.app.src.services.dictionaries.base_dict import BaseDictionaryService
from backend.app.src.models.gamification.badge import Badge  # Модель SQLAlchemy Badge
from backend.app.src.models.auth.user import User  # Для зв'язків created_by_user, updated_by_user
from backend.app.src.models.files.file import FileRecord  # Для зв'язку icon_file
from backend.app.src.models.groups.group import Group  # Для зв'язку group
from backend.app.src.schemas.gamification.badge import (  # Схеми Pydantic
    BadgeCreate,
    BadgeUpdate,
    BadgeResponse,
)
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings  # Для доступу до конфігурацій (наприклад, DEBUG)


class BadgeService(BaseDictionaryService[Badge, BadgeCreate, BadgeUpdate, BadgeResponse]):
    """
    Сервіс для управління визначеннями Значків (Бейджів).
    Бейджі - це нагороди, які користувачі можуть заробити, визначені критеріями,
    назвою, описом та іконкою.
    Успадковує та розширює CRUD-операції від BaseDictionaryService.
    Унікальність поля `name` перевіряється в межах групи (якщо `group_id` вказано) або глобально.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує сервіс BadgeService.

        :param db_session: Асинхронна сесія бази даних SQLAlchemy.
        """
        super().__init__(db_session, model=Badge, response_schema=BadgeResponse)
        logger.info(f"BadgeService ініціалізовано для моделі: {self._model_name}")

    async def _load_relations(self, query: select) -> select:
        """Допоміжний метод для додавання selectinload для зв'язків Badge."""
        return query.options(
            selectinload(Badge.icon_file),
            selectinload(Badge.group),
            selectinload(Badge.created_by_user).options(selectinload(User.user_type)),
            selectinload(Badge.updated_by_user).options(selectinload(User.user_type))
        )

    async def get_by_id(self, item_id: UUID) -> Optional[BadgeResponse]:
        """Отримує бейдж за ID з усіма пов'язаними сутностями."""
        logger.debug(f"Спроба отримання {self._model_name} (Бейдж) за ID: {item_id}")
        stmt = await self._load_relations(select(self.model).where(self.model.id == item_id))
        item_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if item_db:
            logger.info(f"{self._model_name} з ID '{item_id}' знайдено.")
            return self.response_schema.model_validate(item_db)
        logger.info(f"{self._model_name} з ID '{item_id}' не знайдено.")
        return None

    async def get_badge_by_name(self, name: str, group_id: Optional[UUID] = None) -> Optional[BadgeResponse]:
        """
        Отримує бейдж за його унікальним ім'ям в межах групи або глобально.
        (Замінює get_by_code з базового сервісу, якщо Badge не має поля 'code').

        :param name: Ім'я бейджа.
        :param group_id: ID групи (None для глобальних бейджів).
        :return: Pydantic схема BadgeResponse або None.
        """
        logger.debug(f"Спроба отримання Бейджа за ім'ям: '{name}', група ID: {group_id}")

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

    async def get_all(self, skip: int = 0, limit: int = 100, group_id: Optional[UUID] = None,
                      include_global: bool = False) -> List[BadgeResponse]:
        """
        Отримує список бейджів з пагінацією.
        Може фільтрувати за групою та включати глобальні бейджі.

        :param skip: Кількість записів для пропуску.
        :param limit: Максимальна кількість записів.
        :param group_id: ID групи для фільтрації.
        :param include_global: Якщо True і group_id вказано, також включає глобальні бейджі.
                               Якщо group_id не вказано, цей параметр не має ефекту (показує всі).
                               Для показу ТІЛЬКИ глобальних, group_id має бути None, а include_global=True (або спец. параметр).
        :return: Список Pydantic схем BadgeResponse.
        """
        log_msg_parts = [f"skip={skip}", f"limit={limit}"]
        if group_id: log_msg_parts.append(f"група ID='{group_id}'")
        if include_global and group_id: log_msg_parts.append("включно з глобальними")

        logger.debug(f"Спроба отримання всіх {self._model_name} (Бейджів): {', '.join(log_msg_parts)}")

        conditions = []
        if group_id is not None:
            if include_global:
                conditions.append(or_(self.model.group_id == group_id, self.model.group_id.is_(None)))
            else:
                conditions.append(self.model.group_id == group_id)
        # Якщо group_id is None, то за замовчуванням показує всі (і глобальні, і групові).
        # TODO: Додати параметр `global_only: bool = False`, якщо потрібен явний фільтр тільки глобальних бейджів.

        stmt = select(self.model)
        if conditions:
            stmt = stmt.where(*conditions)

        stmt = await self._load_relations(stmt)
        # Сортування: спочатку групові (або ті, що мають group_id), потім глобальні (group_id IS NULL), потім за ім'ям
        stmt = stmt.order_by(self.model.group_id.nulls_last(), self.model.name).offset(skip).limit(limit)

        items_db = (await self.db_session.execute(stmt)).scalars().unique().all()  # unique() через options

        response_list = [self.response_schema.model_validate(item) for item in items_db]
        logger.info(f"Отримано {len(response_list)} {self._model_name} елементів.")
        return response_list

    async def _check_name_uniqueness(self, name: str, group_id: Optional[UUID],
                                     item_id_to_exclude: Optional[UUID] = None) -> None:
        """Перевіряє унікальність імені бейджа в межах групи або глобально."""
        stmt = select(self.model.id).where(self.model.name == name)
        scope_log_msg = "глобальній області"  # i18n
        if group_id:
            stmt = stmt.where(self.model.group_id == group_id)
            scope_log_msg = f"групі ID '{group_id}'"  # i18n
        else:
            stmt = stmt.where(self.model.group_id.is_(None))

        if item_id_to_exclude:  # При оновленні виключаємо поточний елемент
            stmt = stmt.where(self.model.id != item_id_to_exclude)

        existing_item_id = (await self.db_session.execute(stmt)).scalar_one_or_none()
        if existing_item_id:
            msg = f"{self._model_name} з ім'ям '{name}' вже існує в {scope_log_msg}."  # i18n
            logger.warning(msg)
            raise ValueError(msg)

    async def create(self, data: BadgeCreate, created_by_user_id: UUID) -> BadgeResponse:
        """Створює новий бейдж."""
        logger.debug(f"Спроба створення нового {self._model_name} (Бейдж) з ім'ям: '{data.name}'")
        await self._check_name_uniqueness(data.name, data.group_id)

        # Перевірка існування icon_file_id, якщо надано
        if data.icon_file_id and not await self.db_session.get(FileRecord, data.icon_file_id):
            # i18n
            raise ValueError(f"Файл іконки з ID '{data.icon_file_id}' не знайдено.")

        new_item_db = self.model(
            **data.model_dump(),
            created_by_user_id=created_by_user_id,
            updated_by_user_id=created_by_user_id  # При створенні
        )
        self.db_session.add(new_item_db)
        try:
            await self.commit()
            # Завантажуємо зв'язки для повної відповіді
            refreshed_item = await self.get_by_id(new_item_db.id)
            if not refreshed_item: raise RuntimeError("Не вдалося отримати створений бейдж.")  # Малоймовірно
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності '{data.name}': {e}", exc_info=settings.DEBUG)
            raise ValueError(f"Не вдалося створити {self._model_name}: конфлікт даних.")  # i18n

        logger.info(f"{self._model_name} '{refreshed_item.name}' ID: {refreshed_item.id} успішно створено.")
        return refreshed_item

    async def update(self, item_id: UUID, data: BadgeUpdate, updated_by_user_id: UUID) -> Optional[BadgeResponse]:
        """Оновлює існуючий бейдж."""
        logger.debug(f"Спроба оновлення {self._model_name} (Бейдж) з ID: {item_id}")

        item_db = (await self.db_session.execute(
            select(self.model).where(self.model.id == item_id)
        )).scalar_one_or_none()

        if not item_db:
            logger.warning(f"{self._model_name} з ID '{item_id}' не знайдено для оновлення.")
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Перевірка унікальності імені, якщо воно змінюється або змінюється група
        new_name = update_data.get('name', item_db.name)
        new_group_id = update_data.get('group_id', item_db.group_id)  # Важливо враховувати зміну group_id на None
        if 'group_id' not in update_data and item_db.group_id is not None:  # Якщо group_id не вказано в update, але є в БД
            new_group_id = item_db.group_id

        if ('name' in update_data and new_name != item_db.name) or \
                ('group_id' in update_data and new_group_id != item_db.group_id):
            await self._check_name_uniqueness(new_name, new_group_id, item_id_to_exclude=item_id)

        # Перевірка існування icon_file_id, якщо надано і змінено
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
            if not refreshed_item: raise RuntimeError("Не вдалося отримати оновлений бейдж.")  # Малоймовірно
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності ID '{item_id}': {e}", exc_info=settings.DEBUG)
            raise ValueError(f"Не вдалося оновити {self._model_name}: конфлікт даних.")  # i18n

        logger.info(f"{self._model_name} '{refreshed_item.name}' ID: {refreshed_item.id} успішно оновлено.")
        return refreshed_item

    async def list_badges_by_criteria_keyword(self, keyword: str, skip: int = 0, limit: int = 100) -> List[
        BadgeResponse]:
        """
        Перелічує бейджі, в описі критеріїв яких міститься вказане ключове слово.
        Припускає, що модель Badge має текстове поле 'criteria'.
        Пошук нечутливий до регістру.
        """
        logger.debug(f"Перелік бейджів за ключовим словом у критеріях: '{keyword}'")
        if not hasattr(self.model, 'criteria'):
            logger.warning(
                f"Модель Badge ({self._model_name}) не має поля 'criteria'. Пошук за ключовим словом неможливий.")
            return []

        stmt = select(self.model).where(self.model.criteria.ilike(f"%{keyword}%"))
        stmt = await self._load_relations(stmt)  # Завантажуємо зв'язки
        stmt = stmt.order_by(self.model.name).offset(skip).limit(limit)

        badges_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        response_list = [self.response_schema.model_validate(b) for b in badges_db]
        logger.info(f"Отримано {len(response_list)} бейджів, що відповідають ключовому слову '{keyword}' у критеріях.")
        return response_list

    # `delete` успадковується з BaseDictionaryService.
    # TODO: Розглянути необхідність захисту від видалення бейджів, які вже надані користувачам,
    # або мають інші залежності. Це може вимагати перевірки в методі delete.


logger.debug(f"{BadgeService.__name__} (сервіс бейджів) успішно визначено.")
