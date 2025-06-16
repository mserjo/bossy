# backend/app/src/services/groups/group.py
"""
Сервіс для управління групами.

Надає бізнес-логіку для створення, оновлення, видалення, отримання груп,
а також для управління членством та іншими аспектами груп.
"""
from typing import List, Optional, Dict, Any # Tuple не використовується в сигнатурах
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func # Оновлено імпорт select, func може знадобитися
from sqlalchemy.orm import selectinload, noload # joinedload видалено
from sqlalchemy.exc import IntegrityError

# Повні шляхи імпорту
from backend.app.src.services.base import BaseService
from backend.app.src.models.groups.group import Group
from backend.app.src.repositories.groups.group_repository import GroupRepository # Імпорт репозиторію
from backend.app.src.models.auth.user import User
from backend.app.src.models.dictionaries.group_types import GroupType
from backend.app.src.models.groups.membership import GroupMembership
from backend.app.src.models.dictionaries.user_roles import UserRole
from backend.app.src.models.files.file import FileRecord

from backend.app.src.schemas.groups.group import (
    GroupCreate,
    GroupUpdate,
    GroupResponse,
    GroupDetailedResponse
)
from backend.app.src.config import logger  # Використання спільного логера з конфігу
from backend.app.src.config import settings

# TODO: [Configuration] Визначити константу для коду ролі "ADMIN" в конфігурації або в `core.constants`.
ADMIN_ROLE_CODE = "ADMIN"


class GroupService(BaseService):
    """
    Сервіс для управління основними операціями з групами, включаючи створення,
    оновлення, отримання та видалення груп.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        self.group_repo = GroupRepository() # Ініціалізація репозиторію
        logger.info("GroupService ініціалізовано.")

    async def get_group_by_id(self, group_id: int, include_details: bool = False) -> Optional[ # Змінено UUID на int
        GroupResponse]:  # Або GroupDetailedResponse
        """
        Отримує групу за її ID.
        Опціонально може включати більше деталей, таких як члени групи, налаштування тощо.

        :param group_id: ID групи.
        :param include_details: Якщо True, завантажує розширену інформацію про групу.
        :return: Pydantic схема GroupResponse або GroupDetailedResponse, або None, якщо не знайдено.
        """
        logger.debug(f"Спроба отримання групи за ID: {group_id}, include_details: {include_details}")
        try:
            # Залишаємо прямий запит для гнучкого selectinload
            query = select(Group).where(Group.id == group_id)
            if include_details:
                query = query.options(
                    selectinload(Group.group_type),
                    selectinload(Group.icon_file), # Припускаємо, що icon_file - це зв'язок, а не просто icon_file_id
                    selectinload(Group.created_by_user).options(selectinload(User.user_type)),
                    selectinload(Group.updated_by_user).options(selectinload(User.user_type)),
                    selectinload(Group.members).options(
                        selectinload(GroupMembership.user).options(
                            selectinload(User.user_type),
                            selectinload(User.roles) # User.roles - чи існує такий зв'язок?
                        ),
                        selectinload(GroupMembership.role) # Змінено з user_role на role, відповідно до моделі GroupMembership
                    ),
                    selectinload(Group.settings), # Додано settings, якщо є
                )
            else: # Мінімальне завантаження для GroupResponse
                query = query.options(
                    selectinload(Group.group_type),
                    selectinload(Group.icon_file),
                     # created_by_user може бути не потрібним для простого GroupResponse, але зазвичай є
                    selectinload(Group.created_by_user).options(noload("*")),
                )


            group_db_result = await self.db_session.execute(query)
            group_db = group_db_result.scalar_one_or_none()

            if group_db:
                logger.info(f"Групу з ID '{group_id}' знайдено.")
                response_model = GroupDetailedResponse if include_details else GroupResponse
                return response_model.model_validate(group_db)

            logger.info(f"Групу з ID '{group_id}' не знайдено.")
            return None
        except Exception as e:
            logger.error(f"Помилка при отриманні групи за ID {group_id}: {e}", exc_info=settings.DEBUG)
            return None

    async def create_group(self, group_create_data: GroupCreate, creator_id: int) -> GroupDetailedResponse: # Змінено UUID на int
        """
        Створює нову групу та встановлює творця як початкового адміністратора.

        :param group_create_data: Дані для нової групи.
        :param creator_id: ID користувача, що створює групу.
        :return: Pydantic схема GroupDetailedResponse створеної групи.
        :raises ValueError: Якщо користувача-творця, тип групи або роль адміна за замовчуванням не знайдено,
                            або якщо виникає конфлікт даних. # i18n
        """
        logger.debug(f"Спроба створення нової групи '{group_create_data.name}' користувачем ID: {creator_id}")

        # Перевірки існування пов'язаних сутностей залишаються в сервісі
        creator_user_db = await self.db_session.get(User, creator_id)
        if not creator_user_db:
            msg = f"Користувача-творця з ID '{creator_id}' не знайдено."
            logger.error(msg + " Неможливо створити групу.")
            raise ValueError(msg)

        if group_create_data.group_type_id:
            if not await self.db_session.get(GroupType, group_create_data.group_type_id):
                msg = f"Тип групи з ID '{group_create_data.group_type_id}' не знайдено."
                logger.error(msg)
                raise ValueError(msg)

        if group_create_data.icon_file_id: # Припускаємо, що модель Group має icon_file_id
            if not await self.db_session.get(FileRecord, group_create_data.icon_file_id):
                msg = f"Файл іконки з ID '{group_create_data.icon_file_id}' не знайдено."
                logger.error(msg)
                raise ValueError(msg)

        # Створення групи через репозиторій
        # Поля created_by_user_id, updated_by_user_id мають бути оброблені в repo.create або передані як kwargs
        try:
            # Потрібно передати creator_id в repo.create, якщо він встановлює created_by_user_id
            # BaseRepository.create приймає obj_in та **kwargs.
            # Якщо GroupCreate не містить created_by_user_id, передаємо його через kwargs.
            # Модель Group успадковує BaseMainModel, тому ці поля є.
            new_group_db = await self.group_repo.create(
                session=self.db_session,
                obj_in=group_create_data,
                created_by_user_id=creator_id, # Передаємо як kwarg
                updated_by_user_id=creator_id  # Передаємо як kwarg
            )
            # На цьому етапі new_group_db вже додано до сесії через repo.create

            # Додавання творця як адміністратора групи (залишається в сервісі)
            admin_role_db = (await self.db_session.execute(
                select(UserRole).where(UserRole.code == ADMIN_ROLE_CODE) # ADMIN_ROLE_CODE - константа
            )).scalar_one_or_none()

            if not admin_role_db:
                # Відкат не потрібен, якщо коміт ще не було, але сесія може бути "забруднена"
                # Якщо repo.create робить flush, то new_group_db вже має ID
                # Потрібно або видалити new_group_db з сесії, або відкотити сесію
                await self.rollback() # Краще відкотити, щоб скасувати додавання new_group_db
                msg = f"Роль за замовчуванням '{ADMIN_ROLE_CODE}' не знайдено в базі даних."
                logger.error(msg + " Неможливо призначити творця адміністратором.")
                raise ValueError(msg + " Налаштування групи не вдалося.")

            # Потрібен ID групи для GroupMembership. Якщо repo.create не робить flush, робимо тут.
            # Припускаємо, що repo.create робить flush, і new_group_db.id доступний.
            if new_group_db.id is None: # Додаткова перевірка, якщо repo.create не гарантує flush
                 await self.db_session.flush([new_group_db])


            initial_membership = GroupMembership(
                user_id=creator_id,
                group_id=new_group_db.id,
                role_id=admin_role_db.id, # Змінено на role_id
                is_active=True,
            )
            self.db_session.add(initial_membership)

            await self.commit() # Основний коміт для групи та членства

            created_group_detailed = await self.get_group_by_id(new_group_db.id, include_details=True)
            if not created_group_detailed:
                raise RuntimeError(
                    f"Критична помилка: не вдалося отримати створену групу ID {new_group_db.id} після коміту.")

            logger.info(
                f"Групу '{new_group_db.name}' (ID: {new_group_db.id}) успішно створено користувачем ID '{creator_id}'.")
            return created_group_detailed
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності при створенні групи '{group_create_data.name}': {e}",
                         exc_info=settings.DEBUG)
            raise ValueError(f"Не вдалося створити групу через конфлікт даних: {e}")
        except Exception as e:
            await self.rollback()
            logger.error(f"Неочікувана помилка при створенні групи '{group_create_data.name}': {e}",
                         exc_info=settings.DEBUG)
            raise

    async def update_group(self, group_id: int, group_update_data: GroupUpdate, current_user_id: int) -> Optional[ # Змінено UUID на int
        GroupDetailedResponse]:
        """Оновлює деталі групи."""
        logger.debug(f"Спроба оновлення групи ID: {group_id} користувачем ID: {current_user_id}")

        group_to_update = await self.group_repo.get(session=self.db_session, id=group_id) # Використання репозиторію
        if not group_to_update:
            logger.warning(f"Групу ID '{group_id}' не знайдено для оновлення.")
            return None

        # Перевірки існування пов'язаних сутностей залишаються в сервісі
        update_data_dict = group_update_data.model_dump(exclude_unset=True)
        if 'group_type_id' in update_data_dict and update_data_dict['group_type_id'] is not None \
                and group_to_update.group_type_id != update_data_dict['group_type_id']:
            if not await self.db_session.get(GroupType, update_data_dict['group_type_id']):
                raise ValueError(f"Новий тип групи ID '{update_data_dict['group_type_id']}' не знайдено.")

        if 'icon_file_id' in update_data_dict and update_data_dict['icon_file_id'] is not None \
                and group_to_update.icon_file_id != update_data_dict['icon_file_id']: # Припускаємо, що модель Group має icon_file_id
            if not await self.db_session.get(FileRecord, update_data_dict['icon_file_id']):
                raise ValueError(f"Новий файл іконки ID '{update_data_dict['icon_file_id']}' не знайдено.")

        # Оновлення через репозиторій. updated_at оновлюється автоматично через TimestampedMixin.
        try:
            updated_group_db = await self.group_repo.update(
                session=self.db_session,
                db_obj=group_to_update,
                obj_in=group_update_data, # Передаємо Pydantic схему
                updated_by_user_id=current_user_id # Передаємо як kwarg
            )
            await self.commit()

            updated_group_detailed = await self.get_group_by_id(updated_group_db.id, include_details=True)
            if not updated_group_detailed:
                raise RuntimeError(f"Критична помилка: не вдалося отримати оновлену групу ID {updated_group_db.id} після коміту.")
            logger.info(f"Групу ID '{group_id}' успішно оновлено користувачем ID '{current_user_id}'.")
            return updated_group_detailed
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності при оновленні групи ID '{group_id}': {e}", exc_info=settings.DEBUG)
            raise ValueError(f"Не вдалося оновити групу через конфлікт даних: {e}")
        except Exception as e:
            await self.rollback()
            logger.error(f"Помилка при оновленні групи ID '{group_id}': {e}", exc_info=settings.DEBUG)
            raise

    async def delete_group(self, group_id: int, current_user_id: int) -> bool: # Змінено UUID на int
        """Видаляє групу."""
        logger.debug(f"Спроба видалення групи ID: {group_id} користувачем ID: {current_user_id}")

        group_to_delete = await self.group_repo.get(session=self.db_session, id=group_id)
        if not group_to_delete:
            logger.warning(f"Групу ID '{group_id}' не знайдено для видалення.")
            return False

        group_name_for_log = group_to_delete.name

        try:
            await self.group_repo.remove(session=self.db_session, id=group_id)
            await self.commit()
            logger.info(f"Групу ID '{group_id}' ({group_name_for_log}) успішно видалено користувачем ID '{current_user_id}'.")
            return True
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності при видаленні групи ID '{group_id}' ({group_name_for_log}): {e}. Можливо, група використовується.",
                         exc_info=settings.DEBUG)
            raise ValueError(f"Група '{group_name_for_log}' використовується і не може бути видалена.")
        except Exception as e:
            await self.rollback()
            logger.error(f"Неочікувана помилка при видаленні групи ID '{group_id}' ({group_name_for_log}): {e}", exc_info=settings.DEBUG)
            raise

    async def list_user_groups(self, user_id: int, skip: int = 0, limit: int = 100) -> List[GroupResponse]: # Змінено UUID на int
        """Перелічує всі групи, активним членом яких є користувач."""
        logger.debug(f"Перелік груп для користувача ID: {user_id}, пропустити={skip}, ліміт={limit}")

        # Використовуємо метод репозиторію.
        # Репозиторійний метод get_groups_for_member не завантажує group_type, icon_file тощо.
        # Для збереження поточної деталізації відповіді, залишаємо прямий запит.
        # В майбутньому, можна додати параметр load_options в get_groups_for_member.
        stmt = select(Group).join(Group.members).where(
            GroupMembership.user_id == user_id,
            GroupMembership.is_active == True
        ).options(
            selectinload(Group.group_type),
            selectinload(Group.icon_file), # Припускаємо, що Group.icon_file це зв'язок
            selectinload(Group.created_by_user).options(noload("*"))
        ).order_by(Group.name).offset(skip).limit(limit)

        groups_db_list = (await self.db_session.execute(stmt)).scalars().unique().all()

        response_list = [GroupResponse.model_validate(g) for g in groups_db_list]
        logger.info(f"Отримано {len(response_list)} груп для користувача ID '{user_id}'.")
        return response_list

    async def get_group_activity_report(self, group_id: int) -> Dict[str, Any]:  # Заглушка, Змінено UUID на int
        """Генерує звіт про активність групи (заглушка)."""
        logger.info(f"Генерація звіту активності для групи ID: {group_id} (Заглушка)")
        # i18n
        return {"group_id": group_id, "status": "Генерація звіту ще не реалізована."}


logger.debug(f"{GroupService.__name__} (сервіс груп) успішно визначено.")
