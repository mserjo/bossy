# backend/app/src/services/auth/user.py
# -*- coding: utf-8 -*-
"""
Сервіс для управління користувачами.

Надає бізнес-логіку для створення, оновлення, отримання та управління
атрибутами користувачів, такими як ролі, статус та інше.
"""
from datetime import datetime, timezone
from typing import List, Optional, Any, Set, TYPE_CHECKING, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from backend.app.src.services.base import BaseService
from backend.app.src.models.auth.user import User
from backend.app.src.models.dictionaries.user_roles import UserRole
from backend.app.src.models.dictionaries.user_types import UserType
from backend.app.src.schemas.auth.user import (
    UserCreate, # UserCreateSchema було перейменовано на UserCreate в schemas.auth.user, це коректно
    UserUpdate, # UserUpdateSchema було перейменовано на UserUpdate в schemas.auth.user, це коректно
    UserResponse,
    UserResponseWithRoles,
)
from backend.app.src.core.security import get_password_hash
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)
from backend.app.src.config import settings  # Для доступу до DEBUG тощо
from backend.app.src.core.dicts import UserState # Імпорт UserState для фільтрації

if TYPE_CHECKING: # Умовний імпорт для TYPE_CHECKING
    pass


class UserService(BaseService):
    """
    Сервіс для управління користувачами.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("UserService ініціалізовано.")

    async def get_user_by_id(self, user_id: int, include_relations: bool = True) -> Optional[Union[UserResponse, UserResponseWithRoles]]:
        logger.debug(f"Спроба отримання користувача за ID: {user_id}, include_relations: {include_relations}")
        try:
            query = select(User)
            if include_relations:
                query = query.options(selectinload(User.roles), selectinload(User.user_type))
            stmt = query.where(User.id == user_id)
            user_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

            if user_db:
                logger.info(f"Користувача з ID '{user_id}' знайдено.")
                return UserResponseWithRoles.model_validate(user_db) if include_relations else UserResponse.model_validate(user_db)
            logger.info(f"Користувача з ID '{user_id}' не знайдено.")
            return None
        except Exception as e:
            logger.error(f"Помилка при отриманні користувача за ID {user_id}: {e}", exc_info=settings.DEBUG)
            return None

    async def get_user_by_email(self, email: str, include_relations: bool = True) -> Optional[Union[UserResponse, UserResponseWithRoles]]:
        logger.debug(f"Спроба отримання користувача за email: {email}, include_relations: {include_relations}")
        try:
            query = select(User)
            if include_relations:
                query = query.options(selectinload(User.roles), selectinload(User.user_type))
            stmt = query.where(User.email == email.lower())
            user_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

            if user_db:
                logger.info(f"Користувача з email '{email}' знайдено.")
                return UserResponseWithRoles.model_validate(user_db) if include_relations else UserResponse.model_validate(user_db)
            logger.info(f"Користувача з email '{email}' не знайдено.")
            return None
        except Exception as e:
            logger.error(f"Помилка при отриманні користувача за email {email}: {e}", exc_info=settings.DEBUG)
            return None

    async def get_user_by_username(self, username: str, include_relations: bool = True) -> Optional[Union[UserResponse, UserResponseWithRoles]]:
        logger.debug(f"Спроба отримання користувача за username: {username}, include_relations: {include_relations}")
        try:
            query = select(User)
            if include_relations:
                query = query.options(selectinload(User.roles), selectinload(User.user_type))
            stmt = query.where(User.username == username)
            user_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

            if user_db:
                logger.info(f"Користувача з username '{username}' знайдено.")
                return UserResponseWithRoles.model_validate(user_db) if include_relations else UserResponse.model_validate(user_db)
            logger.info(f"Користувача з username '{username}' не знайдено.")
            return None
        except Exception as e:
            logger.error(f"Помилка при отриманні користувача за username {username}: {e}", exc_info=settings.DEBUG)
            return None

    async def _check_existing_user(self, username: str, email: str) -> None:
        """Оптимізована перевірка існування користувача за ім'ям або email."""
        # Перевірка username
        username_exists_stmt = select(User.id).where(User.username == username)
        username_exists_result = await self.db_session.execute(username_exists_stmt)
        if username_exists_result.scalar_one_or_none():
            logger.warning(f"Ім'я користувача '{username}' вже існує.")
            raise ValueError(f"Ім'я користувача '{username}' вже існує.")  # i18n

        # Перевірка email
        email_exists_stmt = select(User.id).where(User.email == email.lower())
        email_exists_result = await self.db_session.execute(email_exists_stmt)
        if email_exists_result.scalar_one_or_none():
            logger.warning(f"Email '{email.lower()}' вже зареєстровано.")
            raise ValueError(f"Email '{email.lower()}' вже зареєстровано.")  # i18n

    async def create_user(self, user_create_data: UserCreate,
                          user_type_code: str = "USER",
                          role_codes: Optional[List[str]] = None,
                          is_superuser_creation: bool = False
                           ) -> UserResponseWithRoles:
        logger.debug(
            f"Спроба створення нового користувача: {user_create_data.username}, is_superuser: {is_superuser_creation}")

        await self._check_existing_user(user_create_data.username, user_create_data.email)

        hashed_password = get_password_hash(user_create_data.password)

        type_stmt = select(UserType).where(UserType.code == user_type_code)
        user_type_db_result = await self.db_session.execute(type_stmt)
        user_type_db = user_type_db_result.scalar_one_or_none()
        if not user_type_db:
            logger.error(f"UserType з кодом '{user_type_code}' не знайдено.")
            raise ValueError(f"Тип користувача '{user_type_code}' не знайдено.")  # i18n

        new_user_data = user_create_data.model_dump(exclude={"password"})
        new_user_data.update({
            "hashed_password": hashed_password,
            "user_type_id": user_type_db.id,
            "email": user_create_data.email.lower(),
            "is_superuser": is_superuser_creation,
            "is_active": True,  # Згідно technical_task.txt
            "is_verified": False, # Згідно technical_task.txt
            # created_at буде встановлено автоматично, якщо модель використовує TimestampedMixin
        })
        # Якщо TimestampedMixin не використовується або потрібно явне встановлення:
        # if 'created_at' not in new_user_data:
        #    new_user_data['created_at'] = datetime.now(timezone.utc)

        new_user_db = User(**new_user_data)

        if role_codes:
            roles_stmt = select(UserRole).where(UserRole.code.in_(role_codes)) # type: ignore
            user_roles_db_result = await self.db_session.execute(roles_stmt)
            user_roles_db = list(user_roles_db_result.scalars().all())

            if len(user_roles_db) != len(set(role_codes)):
                found_role_codes = {role.code for role in user_roles_db}
                missing_codes = set(role_codes) - found_role_codes
                logger.error(
                    f"Не знайдено ролі з кодами: {missing_codes} для нового користувача '{user_create_data.username}'.")
                raise ValueError( # i18n
                    f"Не вдалося створити користувача: не знайдено ролі з кодами: {missing_codes}.")
            new_user_db.roles = user_roles_db

        self.db_session.add(new_user_db)
        try:
            await self.commit()
            await self.db_session.refresh(new_user_db, attribute_names=['roles', 'user_type'])
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності: {e}", exc_info=settings.DEBUG)
            # ... (попередня логіка обробки IntegrityError залишається)
            err_detail = str(e.orig).lower() if hasattr(e, 'orig') and e.orig is not None else str(e).lower()
            if "users_username_key" in err_detail or "unique_username" in err_detail or "constraint failed: users.username" in err_detail:
                raise ValueError(f"Ім'я користувача '{user_create_data.username}' вже існує.")  # i18n
            if "users_email_key" in err_detail or "unique_email" in err_detail or "constraint failed: users.email" in err_detail:
                raise ValueError(f"Email '{user_create_data.email}' вже зареєстровано.")  # i18n
            raise ValueError(f"Не вдалося створити користувача через конфлікт даних: {e}")  # i18n

        logger.info(f"Користувача '{new_user_db.username}' (ID: {new_user_db.id}) успішно створено.")
        return UserResponseWithRoles.model_validate(new_user_db)

    async def update_user(self, user_id: int, user_update_data: UserUpdate,
                          # TODO: Розглянути передачу об'єкта поточного користувача (current_user) або його детальних прав
                          # для більш гранульованої перевірки дозволів на оновлення певних полів,
                          # замість простого прапорця current_user_is_admin.
                          current_user_is_admin: bool = False
                          ) -> Optional[UserResponseWithRoles]:
        logger.debug(f"Спроба оновлення користувача ID: {user_id}")
        user_db = await self._get_user_model_by_id(user_id)
        if not user_db:
            logger.warning(f"Користувача ID '{user_id}' не знайдено для оновлення.")
            return None

        update_data = user_update_data.model_dump(exclude_unset=True)

        if 'email' in update_data and update_data['email'].lower() != user_db.email:
            new_email = update_data['email'].lower()
            existing_email_user_stmt = select(User.id).where(User.email == new_email, User.id != user_id)
            if (await self.db_session.execute(existing_email_user_stmt)).scalar_one_or_none():
                raise ValueError(f"Email '{new_email}' вже зареєстровано іншим користувачем.")  # i18n
            user_db.email = new_email
            # Згідно technical_task.txt, зміна email завжди скидає верифікацію.
            user_db.is_verified = False
            user_db.verified_at = None  # Також скидаємо дату верифікації
            logger.info(f"Email користувача ID '{user_id}' змінено. Статус верифікації скинуто.")

        # Поля, які може оновлювати сам користувач:
        user_allowed_fields: Set[str] = {"first_name", "last_name", "middle_name", "phone_number"}
        # Поля, які може оновлювати адміністратор (додатково до user_allowed_fields):
        admin_allowed_fields: Set[str] = {"username", "is_active", "is_verified", "is_superuser",
                                          "user_type_id"}  # email вже оброблено

        current_allowed_fields = user_allowed_fields
        if current_user_is_admin:  # Тут має бути перевірка ролей/прав поточного користувача
            current_allowed_fields = current_allowed_fields.union(admin_allowed_fields)

        # `user_type_id` та `roles` оновлюються окремими методами, не тут.
        # `is_superuser` теж має бути дуже захищеним полем.

        for field, value in update_data.items():
            if field == 'email': continue  # Вже оброблено

            if field in current_allowed_fields:
                if field == 'username' and value != user_db.username:  # Потрібна перевірка унікальності для username
                    existing_username_stmt = select(User.id).where(User.username == value, User.id != user_id)
                    if (await self.db_session.execute(existing_username_stmt)).scalar_one_or_none():
                        raise ValueError(f"Ім'я користувача '{value}' вже використовується.")  # i18n

                # Спеціальна обробка для is_verified, якщо воно є в update_data і current_user_is_admin
                if field == 'is_verified' and current_user_is_admin:
                    # Якщо адміністратор явно встановлює is_verified, оновлюємо verified_at
                    user_db.is_verified = value
                    user_db.verified_at = datetime.now(timezone.utc) if value else None
                    logger.info(f"Адміністратор оновив is_verified на {value} для ID {user_id}. verified_at оновлено.")
                    continue  # Переходимо до наступного поля

                setattr(user_db, field, value)
            else:
                logger.warning(f"Поле '{field}' не дозволено для оновлення або не існує для ID '{user_id}'. Пропуск.")

        user_db.updated_at = datetime.now(timezone.utc)  # Явно оновлюємо updated_at
        self.db_session.add(user_db)
        await self.commit()
        await self.db_session.refresh(user_db, attribute_names=['roles', 'user_type'])
        logger.info(f"Користувача ID '{user_id}' успішно оновлено.")
        return UserResponseWithRoles.model_validate(user_db)

    async def _get_user_model_by_id(self, user_id: int) -> Optional[User]:
        stmt = select(User).options(selectinload(User.roles), selectinload(User.user_type)).where(User.id == user_id)
        return (await self.db_session.execute(stmt)).scalar_one_or_none()

    async def _manage_user_roles(self, user_id: int, role_codes: List[str], action: str) -> Optional[
        UserResponseWithRoles]:
        # ... (попередня реалізація _manage_user_roles залишається)
        user_db = await self._get_user_model_by_id(user_id)
        if not user_db:
            logger.warning(f"Користувача ID '{user_id}' не знайдено для оновлення ролей.")
            return None

        made_changes = False
        if not role_codes:  # Якщо список кодів порожній
            if action == "replace_add":  # Замінити всі ролі на порожній список
                if user_db.roles:  # Якщо були ролі, то зміни відбулись
                    made_changes = True
                user_db.roles = []
            else:  # Для "assign" або "remove" порожній список кодів не призводить до змін
                logger.info(f"Список кодів ролей порожній для дії '{action}' для ID '{user_id}'. Змін не відбулося.")
                return UserResponseWithRoles.model_validate(user_db)
        else:
            roles_to_process_db: List[UserRole] = []
            roles_stmt = select(UserRole).where(UserRole.code.in_(role_codes))
            roles_to_process_db = (await self.db_session.execute(roles_stmt)).scalars().all()

            if len(roles_to_process_db) != len(set(role_codes)) and action != "remove":
                # Якщо не всі вказані коди ролей знайдено (і це не операція видалення, де неіснуючі коди ігноруються)
                found_codes = {r.code for r in roles_to_process_db}
                missing_codes = set(role_codes) - found_codes
                logger.error(f"Не знайдено ролі з кодами: {missing_codes} для ID '{user_id}'.")
                raise ValueError(f"Не знайдено ролі: {missing_codes}.")  # i18n

            current_role_ids = {role.id for role in user_db.roles}
            if action == "assign":
                for role in roles_to_process_db:
                    if role.id not in current_role_ids:
                        user_db.roles.append(role)
                        made_changes = True
            elif action == "remove":
                ids_to_remove = {r.id for r in roles_to_process_db}
                initial_len = len(user_db.roles)
                user_db.roles = [role for role in user_db.roles if role.id not in ids_to_remove]
                if len(user_db.roles) < initial_len:
                    made_changes = True
            elif action == "replace_add":
                # Перевірка, чи новий набір ролей відрізняється від поточного
                if set(r.id for r in roles_to_process_db) != current_role_ids:
                    made_changes = True
                user_db.roles = roles_to_process_db

        if made_changes:
            user_db.updated_at = datetime.now(timezone.utc)
            self.db_session.add(user_db)
            await self.commit()
            await self.db_session.refresh(user_db, attribute_names=['roles', 'user_type'])
            logger.info(f"Ролі для ID '{user_id}' оновлено ({action}). Поточні: {[r.code for r in user_db.roles]}.")
        else:
            logger.info(f"Змін у ролях для ID '{user_id}' не відбулося (дія: {action}).")

        return UserResponseWithRoles.model_validate(user_db)

    async def assign_roles_to_user(self, user_id: int, role_codes: List[str], replace_existing: bool = False) -> \
    Optional[UserResponseWithRoles]:
        logger.debug(f"Призначення ролей {role_codes} ID {user_id}. Заміна: {replace_existing}")
        action = "replace_add" if replace_existing else "assign"
        return await self._manage_user_roles(user_id, role_codes, action)

    async def remove_roles_from_user(self, user_id: int, role_codes: List[str]) -> Optional[UserResponseWithRoles]:
        logger.debug(f"Видалення ролей {role_codes} в ID {user_id}")
        return await self._manage_user_roles(user_id, role_codes, "remove")

    async def set_user_active_status(self, user_id: int, is_active: bool) -> Optional[UserResponseWithRoles]:
        logger.info(f"Встановлення is_active={is_active} для ID: {user_id}")
        user_db = await self._get_user_model_by_id(user_id)
        if not user_db:
            logger.warning(f"Користувача ID '{user_id}' не знайдено.")
            return None

        if user_db.is_active != is_active:
            user_db.is_active = is_active
            user_db.updated_at = datetime.now(timezone.utc)
            self.db_session.add(user_db)
            await self.commit()
            await self.db_session.refresh(user_db, attribute_names=['roles', 'user_type'])
            logger.info(f"is_active для ID '{user_id}' змінено на {is_active}.")
        else:
            logger.info(f"is_active для ID '{user_id}' вже {is_active}. Змін немає.")
        return UserResponseWithRoles.model_validate(user_db)

    async def set_user_verification_status(self, user_id: int, is_verified: bool) -> Optional[UserResponseWithRoles]:
        logger.info(f"Встановлення is_verified={is_verified} для ID: {user_id}")
        user_db = await self._get_user_model_by_id(user_id)
        if not user_db:
            logger.warning(f"Користувача ID '{user_id}' не знайдено.")
            return None

        if user_db.is_verified != is_verified:
            user_db.is_verified = is_verified
            # Згідно technical_task.txt, оновлюємо verified_at
            user_db.verified_at = datetime.now(timezone.utc) if is_verified else None
            user_db.updated_at = datetime.now(timezone.utc)
            self.db_session.add(user_db)
            await self.commit()
            await self.db_session.refresh(user_db, attribute_names=['roles', 'user_type'])
            logger.info(f"is_verified для ID '{user_id}' змінено на {is_verified}, verified_at оновлено.")
        else:
            logger.info(f"is_verified для ID '{user_id}' вже {is_verified}. Змін немає.")
        return UserResponseWithRoles.model_validate(user_db)

    async def list_users(self, skip: int = 0, limit: int = 100,
                         is_active: Optional[bool] = None,
                         user_type_code: Optional[str] = None,
                         role_code: Optional[str] = None,
                         sort_by: Optional[str] = "username",
                         sort_order: Optional[str] = "asc"
                         ) -> List[UserResponseWithRoles]:
        """
        Перелічує користувачів з можливістю фільтрації та сортування.

        :param skip: Кількість записів для пропуску (пагінація).
        :param limit: Максимальна кількість записів для повернення.
        :param is_active: Фільтр за статусом активності користувача.
        :param user_type_code: Фільтр за кодом типу користувача.
        :param role_code: Фільтр за кодом ролі користувача.
        :param sort_by: Поле для сортування (наприклад, "username", "created_at").
                        Допустимі значення: "username", "email", "created_at", "updated_at", "last_login_at", "first_name", "last_name".
                        За замовчуванням "username".
        :param sort_order: Порядок сортування ("asc" або "desc"). За замовчуванням "asc".
        :return: Список об'єктів UserResponseWithRoles.
        """
        logger.debug(
            f"Перелік користувачів: skip={skip}, limit={limit}, is_active={is_active}, "
            f"type={user_type_code}, role={role_code}, sort_by='{sort_by}', sort_order='{sort_order}'")
        stmt = select(User).options(selectinload(User.roles), selectinload(User.user_type))

        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
        if user_type_code:
            stmt = stmt.join(User.user_type).where(UserType.code == user_type_code)
        if role_code:
            # join(User.roles) використовує таблицю зв'язку user_x_user_roles
            stmt = stmt.join(User.roles).where(UserRole.code == role_code)

        # Логіка сортування
        ALLOWED_SORT_FIELDS = ["username", "email", "created_at", "updated_at", "last_login_at", "first_name", "last_name"]

        validated_sort_by = sort_by if sort_by in ALLOWED_SORT_FIELDS else "username"
        if sort_by is not None and sort_by not in ALLOWED_SORT_FIELDS:
            logger.warning(f"Недопустиме поле для сортування '{sort_by}'. Використовується 'username'.") # i18n

        validated_sort_order = sort_order.lower() if sort_order and sort_order.lower() in ["asc", "desc"] else "asc"
        if sort_order and sort_order.lower() not in ["asc", "desc"]:
            logger.warning(f"Недопустимий порядок сортування '{sort_order}'. Використовується 'asc'.") # i18n

        sort_attribute = getattr(User, validated_sort_by, User.username) # User.username як fallback

        if validated_sort_order == "desc":
            stmt = stmt.order_by(sort_attribute.desc())
        else:
            stmt = stmt.order_by(sort_attribute.asc())

        stmt = stmt.offset(skip).limit(limit)

        users_db = (await self.db_session.execute(
            stmt)).scalars().unique().all()  # .unique() для уникнення дублікатів через join

        response_list = [UserResponseWithRoles.model_validate(user) for user in users_db]
        logger.info(f"Отримано {len(response_list)} користувачів.")
        return response_list


logger.debug("UserService клас визначено та завантажено.")
