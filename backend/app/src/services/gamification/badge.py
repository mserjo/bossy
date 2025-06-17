# backend/app/src/services/gamification/badge.py
from typing import List, Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select # sqlalchemy.future видалено
from sqlalchemy.orm import selectinload, or_  # Додано для завантаження зв'язків та or_
from sqlalchemy.exc import IntegrityError

from backend.app.src.services.base import BaseService
from backend.app.src.models.gamification.badge import Badge
from backend.app.src.repositories.gamification.badge_repository import BadgeRepository # Імпорт репозиторію
# BaseCacheService не потрібен, якщо сервіс не використовує BaseDictionaryService
# from backend.app.src.services.cache.base_cache import BaseCacheService
from backend.app.src.models.auth.user import User  # Для зв'язків created_by_user, updated_by_user
from backend.app.src.models.files.file import FileRecord  # Для зв'язку icon_file
from backend.app.src.models.groups.group import Group  # Для зв'язку group
from backend.app.src.schemas.gamification.badge import (  # Схеми Pydantic
    BadgeCreate,
    BadgeUpdate,
    BadgeResponse,
)
from backend.app.src.config import settings  # Для доступу до конфігурацій (наприклад, DEBUG)
from backend.app.src.config.logging import get_logger
from backend.app.src.core.i18n import _ # Added import
logger = get_logger(__name__)


class BadgeService(BaseService): # Змінено успадкування на BaseService
    """
    Сервіс для управління визначеннями Значків (Бейджів).
    Бейджі - це нагороди, які користувачі можуть заробити, визначені критеріями,
    назвою, описом та іконкою.
    Унікальність поля `name` перевіряється в межах групи (якщо `group_id` вказано) або глобально.
    """

    def __init__(self, db_session: AsyncSession): # Видалено cache_service
        """
        Ініціалізує сервіс BadgeService.

        :param db_session: Асинхронна сесія бази даних SQLAlchemy.
        """
        super().__init__(db_session) # Передаємо тільки db_session
        self.badge_repo = BadgeRepository() # Ініціалізуємо репозиторій
        self.response_schema = BadgeResponse # Зберігаємо схему відповіді для використання
        self._model_name = Badge.__name__ # Встановлюємо ім'я моделі вручну
        logger.info(f"BadgeService ініціалізовано для моделі: {self._model_name}")

    async def _load_relations(self, query: select) -> select: # select з sqlalchemy
        """Допоміжний метод для додавання selectinload для зв'язків Badge."""
        return query.options(
            selectinload(Badge.icon_file),
            selectinload(Badge.group),
            selectinload(Badge.created_by_user).options(selectinload(User.user_type)),
            selectinload(Badge.updated_by_user).options(selectinload(User.user_type))
        )

    async def get_by_id(self, item_id: int) -> Optional[BadgeResponse]: # item_id: UUID -> int
        """
        Отримує бейдж за ID з усіма пов'язаними сутностями.
        :param item_id: ID бейджа (int).
        """
        logger.debug(f"Спроба отримання {self._model_name} (Бейдж) за ID: {item_id}")
        stmt = await self._load_relations(select(self.model).where(self.model.id == item_id))
        item_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if item_db:
            logger.info(f"{self._model_name} з ID '{item_id}' знайдено.")
            return self.response_schema.model_validate(item_db)
        logger.info(f"{self._model_name} з ID '{item_id}' не знайдено.")
        return None

    async def get_badge_by_name(self, name: str, group_id: Optional[int] = None) -> Optional[BadgeResponse]: # group_id: Optional[UUID] -> Optional[int]
        """
        Отримує бейдж за його унікальним ім'ям в межах групи або глобально.
        (Замінює get_by_code з базового сервісу, якщо Badge не має поля 'code').

        :param name: Ім'я бейджа.
        :param group_id: ID групи (Optional[int], None для глобальних бейджів).
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

    async def get_all(self, skip: int = 0, limit: int = 100, group_id: Optional[int] = None, # group_id: Optional[UUID] -> Optional[int]
                      include_global: bool = False) -> List[BadgeResponse]:
        """
        Отримує список бейджів з пагінацією.
        Може фільтрувати за групою та включати глобальні бейджі.

        :param skip: Кількість записів для пропуску.
        :param limit: Максимальна кількість записів.
        :param group_id: ID групи (Optional[int]) для фільтрації.
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

    async def _check_name_uniqueness(self, name: str, group_id: Optional[int], # group_id: Optional[UUID] -> Optional[int]
                                     item_id_to_exclude: Optional[int] = None) -> None: # item_id_to_exclude: Optional[UUID] -> Optional[int]
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
            # msg = f"{self._model_name} з ім'ям '{name}' вже існує в {scope_log_msg}."  # Original for log
            # logger.warning(msg) # Log can be more detailed
            # For user-facing error, use the translated version:
            translated_scope = _("in_group_scope", group_id=group_id) if group_id else _("global_scope")
            raise ValueError(_("gamification.badge.errors.name_exists_in_scope", model_name=self._model_name, name=name, scope=translated_scope))

    async def create(self, data: BadgeCreate, created_by_user_id: int) -> BadgeResponse: # created_by_user_id: UUID -> int
        """
        Створює новий бейдж.
        :param data: Дані для створення.
        :param created_by_user_id: ID користувача (int), що створює запис.
        """
        logger.debug(f"Спроба створення нового {self._model_name} (Бейдж) з ім'ям: '{data.name}'")
        await self._check_name_uniqueness(data.name, data.group_id)

        if data.icon_file_id and not await self.db_session.get(FileRecord, data.icon_file_id):
            raise ValueError(_("gamification.badge.errors.icon_file_not_found", file_id=data.icon_file_id))

        # Створюємо словник даних для kwargs, щоб передати created_by_user_id та updated_by_user_id
        # Хоча модель Badge їх не має, BaseRepository.create може їх прийняти, якщо вони є в **kwargs
        # Але краще передавати їх явно, якщо модель їх підтримує.
        # Поточна модель Badge успадковує BaseMainModel, яка має created_by_user_id, updated_by_user_id.

        badge_data_for_repo = data.model_dump()
        # created_by_user_id та updated_by_user_id будуть встановлені через kwargs в repo.create,
        # якщо модель їх підтримує і BaseRepository.create це обробляє.
        # Або, якщо модель має ці поля, їх можна додати в BadgeCreate схему.
        # Поки що припускаємо, що BaseRepository.create може прийняти їх як kwargs.

        try:
            new_item_db = await self.badge_repo.create(
                session=self.db_session,
                obj_in=data, # Передаємо Pydantic схему
                created_by_user_id=created_by_user_id,
                updated_by_user_id=created_by_user_id
            )
            await self.commit()
            refreshed_item = await self.get_by_id(new_item_db.id) # Використовуємо get_by_id сервісу для завантаження зв'язків
            if not refreshed_item: raise RuntimeError(_("gamification.badge.errors.critical_create_failed"))
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності '{data.name}': {e}", exc_info=settings.DEBUG)
            raise ValueError(_("gamification.badge.errors.create_conflict", model_name=self._model_name, error_message=str(e)))

        logger.info(f"{self._model_name} '{refreshed_item.name}' ID: {refreshed_item.id} успішно створено.")
        return refreshed_item

    async def update(self, item_id: int, data: BadgeUpdate, updated_by_user_id: int) -> Optional[BadgeResponse]: # item_id, updated_by_user_id: UUID -> int
        """
        Оновлює існуючий бейдж.
        :param item_id: ID бейджа (int) для оновлення.
        :param data: Дані для оновлення.
        :param updated_by_user_id: ID користувача (int), що виконує оновлення.
        """
        logger.debug(f"Спроба оновлення {self._model_name} (Бейдж) з ID: {item_id}")

        item_db = await self.badge_repo.get(session=self.db_session, id=item_id) # Використовуємо репозиторій

        if not item_db:
            logger.warning(f"{self._model_name} з ID '{item_id}' не знайдено для оновлення.")
            return None

        update_data_dict = data.model_dump(exclude_unset=True)

        new_name = update_data_dict.get('name', item_db.name)
        # Обробка group_id: якщо 'group_id' є в update_data_dict, використовуємо його значення,
        # інакше залишаємо поточне значення item_db.group_id.
        # Це важливо, бо Pydantic model_dump(exclude_unset=True) не включатиме group_id, якщо він не був наданий в data.
        new_group_id = update_data_dict.get('group_id') if 'group_id' in update_data_dict else item_db.group_id


        if ('name' in update_data_dict and new_name != item_db.name) or \
           ('group_id' in update_data_dict and new_group_id != item_db.group_id):
            await self._check_name_uniqueness(new_name, new_group_id, item_id_to_exclude=item_id)

        if 'icon_file_id' in update_data_dict and update_data_dict['icon_file_id'] is not None \
                and update_data_dict['icon_file_id'] != item_db.icon_file_id:
            if not await self.db_session.get(FileRecord, update_data_dict['icon_file_id']):
                raise ValueError(_("gamification.badge.errors.icon_file_not_found", file_id=update_data_dict['icon_file_id']))

        # BaseRepository.update очікує obj_in як Pydantic схему або dict.
        # Передаємо data (BadgeUpdate schema), а updated_by_user_id як kwarg.
        try:
            updated_item_db = await self.badge_repo.update(
                session=self.db_session,
                db_obj=item_db,
                obj_in=data, # Передаємо оригінальну Pydantic схему BadgeUpdate
                updated_by_user_id=updated_by_user_id
                # updated_at оновлюється автоматично через TimestampedMixin в BaseRepository.update
            )
            await self.commit()
            refreshed_item = await self.get_by_id(updated_item_db.id)
            if not refreshed_item: raise RuntimeError(_("gamification.badge.errors.critical_update_failed"))
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності ID '{item_id}': {e}", exc_info=settings.DEBUG)
            raise ValueError(_("gamification.badge.errors.update_conflict", model_name=self._model_name, error_message=str(e)))

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
