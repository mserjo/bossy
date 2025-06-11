# backend/app/src/services/groups/group.py
# import logging # Замінено на централізований логер
from typing import List, Optional, Any, Dict
from uuid import UUID
from datetime import datetime, timezone # Додано для updated_at

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload, noload
from sqlalchemy.exc import IntegrityError

# Повні шляхи імпорту
from backend.app.src.services.base import BaseService
from backend.app.src.models.groups.group import Group # Модель SQLAlchemy Group
from backend.app.src.models.auth.user import User # Для творця та членів
from backend.app.src.models.dictionaries.group_types import GroupType # Для типу групи
from backend.app.src.models.groups.membership import GroupMembership # Для додавання творця як адміна
from backend.app.src.models.dictionaries.user_roles import UserRole # Для ролі адміна за замовчуванням
from backend.app.src.models.files.file import FileRecord # Для icon_file

from backend.app.src.schemas.groups.group import ( # Схеми Pydantic Group
    GroupCreate,
    GroupUpdate,
    GroupResponse,
    GroupDetailedResponse # Розширена схема відповіді
)
from backend.app.src.config.logging import logger # Централізований логер
from backend.app.src.config import settings # Для доступу до конфігурацій (наприклад, DEBUG)

# TODO: Визначити константу для коду ролі "ADMIN" в конфігурації або в спеціальному файлі констант.
ADMIN_ROLE_CODE = "ADMIN"

class GroupService(BaseService):
    """
    Сервіс для управління основними операціями з групами, включаючи створення,
    оновлення, отримання та видалення груп.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("GroupService ініціалізовано.")

    async def get_group_by_id(self, group_id: UUID, include_details: bool = False) -> Optional[GroupResponse]: # Або GroupDetailedResponse
        """
        Отримує групу за її ID.
        Опціонально може включати більше деталей, таких як члени групи, налаштування тощо.

        :param group_id: ID групи.
        :param include_details: Якщо True, завантажує розширену інформацію про групу.
        :return: Pydantic схема GroupResponse або GroupDetailedResponse, або None, якщо не знайдено.
        """
        logger.debug(f"Спроба отримання групи за ID: {group_id}, include_details: {include_details}")

        query = select(Group).where(Group.id == group_id)
        if include_details:
            query = query.options(
                selectinload(Group.group_type),
                selectinload(Group.icon_file),
                selectinload(Group.created_by_user).options(selectinload(User.user_type)),
                selectinload(Group.updated_by_user).options(selectinload(User.user_type)),
                # Завантаження членів групи та їх деталей
                selectinload(Group.members).options(
                    selectinload(GroupMembership.user).options(
                        selectinload(User.user_type),
                        selectinload(User.roles) # Ролі користувача в системі, не плутати з роллю в групі
                    ),
                    selectinload(GroupMembership.user_role) # Роль користувача в цій групі
                ),
                # TODO: Додати selectinload для Group.settings, якщо є прямий зв'язок і потрібно в GroupDetailedResponse
                # selectinload(Group.settings),
            )
        else: # Для звичайного GroupResponse можемо завантажити менше
             query = query.options(
                selectinload(Group.group_type),
                selectinload(Group.icon_file),
                selectinload(Group.created_by_user).options(noload("*")) # Тільки ID, якщо UserResponse не потрібен повністю
            )

        group_db = (await self.db_session.execute(query)).scalar_one_or_none()

        if group_db:
            logger.info(f"Групу з ID '{group_id}' знайдено.")
            response_model = GroupDetailedResponse if include_details else GroupResponse
            return response_model.model_validate(group_db) # Pydantic v2

        logger.info(f"Групу з ID '{group_id}' не знайдено.")
        return None

    async def create_group(self, group_create_data: GroupCreate, creator_id: UUID) -> GroupDetailedResponse:
        """
        Створює нову групу та встановлює творця як початкового адміністратора.

        :param group_create_data: Дані для нової групи.
        :param creator_id: ID користувача, що створює групу.
        :return: Pydantic схема GroupDetailedResponse створеної групи.
        :raises ValueError: Якщо користувача-творця, тип групи або роль адміна за замовчуванням не знайдено,
                            або якщо виникає конфлікт даних. # i18n
        """
        logger.debug(f"Спроба створення нової групи '{group_create_data.name}' користувачем ID: {creator_id}")

        creator_user_db = await self.db_session.get(User, creator_id)
        if not creator_user_db:
            msg = f"Користувача-творця з ID '{creator_id}' не знайдено." # i18n
            logger.error(msg + " Неможливо створити групу.")
            raise ValueError(msg)

        if group_create_data.group_type_id:
            if not await self.db_session.get(GroupType, group_create_data.group_type_id):
                msg = f"Тип групи з ID '{group_create_data.group_type_id}' не знайдено." # i18n
                logger.error(msg)
                raise ValueError(msg)

        if group_create_data.icon_file_id:
            if not await self.db_session.get(FileRecord, group_create_data.icon_file_id):
                msg = f"Файл іконки з ID '{group_create_data.icon_file_id}' не знайдено." # i18n
                logger.error(msg)
                raise ValueError(msg)

        # TODO: Уточнити політику унікальності імен груп (наприклад, глобально, чи в межах користувача-творця).
        # Наразі унікальність імені групи не перевіряється на рівні сервісу за замовчуванням.
        # Якщо потрібна, додати перевірку тут.

        new_group_db = Group(
            **group_create_data.model_dump(), # Pydantic v2
            created_by_user_id=creator_id,
            updated_by_user_id=creator_id # При створенні
            # `created_at`, `updated_at` встановлюються автоматично моделлю
        )
        self.db_session.add(new_group_db)

        # Додавання творця як адміністратора групи
        admin_role_db = (await self.db_session.execute(
            select(UserRole).where(UserRole.code == ADMIN_ROLE_CODE)
        )).scalar_one_or_none()

        if not admin_role_db:
            # Важливо відкотити, якщо група вже додана до сесії, але ще не закомічена
            await self.rollback() # Запобігаємо частковому створенню
            msg = f"Роль за замовчуванням '{ADMIN_ROLE_CODE}' не знайдено в базі даних." # i18n
            logger.error(msg + " Неможливо призначити творця адміністратором.")
            raise ValueError(msg + " Налаштування групи не вдалося.")

        await self.db_session.flush() # Отримуємо new_group_db.id перед створенням членства

        initial_membership = GroupMembership(
            user_id=creator_id,
            group_id=new_group_db.id,
            user_role_id=admin_role_db.id, # Роль Адміністратора Групи
            is_active=True,
            # `joined_at`, `updated_at` встановлюються автоматично моделлю
        )
        self.db_session.add(initial_membership)

        try:
            await self.commit()
            # Отримуємо групу з усіма деталями для відповіді
            created_group_detailed = await self.get_group_by_id(new_group_db.id, include_details=True)
            if not created_group_detailed: # Малоймовірно, але перевірка для надійності
                # i18n
                raise RuntimeError(f"Критична помилка: не вдалося отримати створену групу ID {new_group_db.id} після коміту.")

            logger.info(f"Групу '{new_group_db.name}' (ID: {new_group_db.id}) успішно створено користувачем ID '{creator_id}'.")
            return created_group_detailed # GroupDetailedResponse
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності при створенні групи '{group_create_data.name}': {e}", exc_info=settings.DEBUG)
            # i18n
            raise ValueError(f"Не вдалося створити групу через конфлікт даних: {e}")
        except Exception as e:
            await self.rollback()
            logger.error(f"Неочікувана помилка при створенні групи '{group_create_data.name}': {e}", exc_info=settings.DEBUG)
            raise

    async def update_group(self, group_id: UUID, group_update_data: GroupUpdate, current_user_id: UUID) -> Optional[GroupDetailedResponse]:
        """Оновлює деталі групи."""
        # Перевірка прав (адмін групи або суперюзер) має бути на рівні API.
        logger.debug(f"Спроба оновлення групи ID: {group_id} користувачем ID: {current_user_id}")

        group_to_update = await self.db_session.get(Group, group_id)
        if not group_to_update:
            logger.warning(f"Групу ID '{group_id}' не знайдено для оновлення.")
            return None

        update_data = group_update_data.model_dump(exclude_unset=True) # Pydantic v2

        if 'group_type_id' in update_data and update_data['group_type_id'] is not None \
           and group_to_update.group_type_id != update_data['group_type_id']:
            if not await self.db_session.get(GroupType, update_data['group_type_id']):
                # i18n
                raise ValueError(f"Новий тип групи ID '{update_data['group_type_id']}' не знайдено.")

        if 'icon_file_id' in update_data and update_data['icon_file_id'] is not None \
            and group_to_update.icon_file_id != update_data['icon_file_id']:
            if not await self.db_session.get(FileRecord, update_data['icon_file_id']):
                 # i18n
                raise ValueError(f"Новий файл іконки ID '{update_data['icon_file_id']}' не знайдено.")


        for field, value in update_data.items():
            setattr(group_to_update, field, value)

        group_to_update.updated_by_user_id = current_user_id
        group_to_update.updated_at = datetime.now(timezone.utc) # Явне оновлення

        self.db_session.add(group_to_update)
        try:
            await self.commit()
            updated_group_detailed = await self.get_group_by_id(group_id, include_details=True)
            if not updated_group_detailed: # Малоймовірно
                 # i18n
                raise RuntimeError(f"Критична помилка: не вдалося отримати оновлену групу ID {group_id} після коміту.")
            logger.info(f"Групу ID '{group_id}' успішно оновлено користувачем ID '{current_user_id}'.")
            return updated_group_detailed
        except IntegrityError as e: # Обробка можливих конфліктів унікальності на рівні БД
            await self.rollback()
            logger.error(f"Помилка цілісності при оновленні групи ID '{group_id}': {e}", exc_info=settings.DEBUG)
            # i18n
            raise ValueError(f"Не вдалося оновити групу через конфлікт даних: {e}")
        except Exception as e:
            await self.rollback()
            logger.error(f"Помилка при оновленні групи ID '{group_id}': {e}", exc_info=settings.DEBUG)
            raise

    async def delete_group(self, group_id: UUID, current_user_id: UUID) -> bool:
        """Видаляє групу."""
        # Перевірка прав та бізнес-логіки (напр., чи є активні члени) - на рівні API або тут.
        # TODO: Уточнити каскадне видалення або обмеження (напр., якщо є члени, завдання, налаштування).
        logger.debug(f"Спроба видалення групи ID: {group_id} користувачем ID: {current_user_id}")

        group_db = await self.db_session.get(Group, group_id)
        if not group_db:
            logger.warning(f"Групу ID '{group_id}' не знайдено для видалення.")
            return False

        # Приклад перевірки бізнес-логіки:
        # member_count = await self.db_session.scalar(select(func.count(GroupMembership.id)).where(GroupMembership.group_id == group_id))
        # if member_count and member_count > 0:
        #     raise ValueError(f"Неможливо видалити групу ID '{group_id}', оскільки вона має {member_count} членів.") # i18n

        try:
            await self.db_session.delete(group_db)
            await self.commit()
            logger.info(f"Групу ID '{group_id}' успішно видалено користувачем ID '{current_user_id}'.")
            return True
        except IntegrityError as e: # Якщо є залежні записи, що блокують видалення
            await self.rollback()
            logger.error(f"Помилка цілісності '{group_id}': {e}. Можливо, група використовується.", exc_info=settings.DEBUG)
            # i18n
            raise ValueError(f"Група '{group_db.name}' використовується і не може бути видалена.")
        except Exception as e:
            await self.rollback()
            logger.error(f"Неочікувана помилка '{group_id}': {e}", exc_info=settings.DEBUG)
            raise


    async def list_user_groups(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[GroupResponse]:
        """Перелічує всі групи, активним членом яких є користувач."""
        logger.debug(f"Перелік груп для користувача ID: {user_id}, пропустити={skip}, ліміт={limit}")

        stmt = select(Group).join(Group.members).where(
            GroupMembership.user_id == user_id,
            GroupMembership.is_active == True # Тільки активні членства
        ).options(
            selectinload(Group.group_type),
            selectinload(Group.icon_file),
            selectinload(Group.created_by_user).options(noload("*")) # Мінімізуємо дані творця
        ).order_by(Group.name).offset(skip).limit(limit)

        groups_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        response_list = [GroupResponse.model_validate(g) for g in groups_db] # Pydantic v2
        logger.info(f"Отримано {len(response_list)} груп для користувача ID '{user_id}'.")
        return response_list

    async def get_group_activity_report(self, group_id: UUID) -> Dict[str, Any]: # Заглушка
        """Генерує звіт про активність групи (заглушка)."""
        logger.info(f"Генерація звіту активності для групи ID: {group_id} (Заглушка)")
        # i18n
        return {"group_id": group_id, "status": "Генерація звіту ще не реалізована."}


logger.debug(f"{GroupService.__name__} (сервіс груп) успішно визначено.")
