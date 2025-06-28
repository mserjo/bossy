# backend/app/src/services/auth/user_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `UserService` для управління користувачами.
Він інкапсулює бізнес-логіку, пов'язану зі створенням, отриманням,
оновленням та видаленням користувачів, а також управлінням їх профілями,
паролями та статусами.
"""

from typing import List, Optional, Union, Dict, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from backend.app.src.models.auth.user import UserModel
from backend.app.src.schemas.auth.user import UserCreateSchema, UserUpdateSchema, UserAdminUpdateSchema, UserSchema
from backend.app.src.repositories.auth.user_repository import UserRepository
from backend.app.src.repositories.dictionaries.status_repository import StatusRepository # Для статусів
from backend.app.src.repositories.dictionaries.user_role_repository import UserRoleRepository # Для ролей
from backend.app.src.services.base import BaseService
from backend.app.src.core.security import get_password_hash, verify_password
from backend.app.src.core.exceptions import NotFoundException, BadRequestException, ForbiddenException
from backend.app.src.core.constants import USER_TYPE_SUPERADMIN, STATUS_ACTIVE_CODE, STATUS_PENDING_EMAIL_VERIFICATION_CODE, ROLE_USER_CODE
from backend.app.src.config.logging import logger

class UserService(BaseService[UserRepository]):
    """
    Сервіс для управління користувачами.
    """
    def __init__(self, db_session: AsyncSession):
        super().__init__(UserRepository(db_session)) # Передаємо екземпляр репозиторія
        self.db_session = db_session # Зберігаємо сесію для використання в цьому сервісі
        self.status_repo = StatusRepository(db_session) # Для роботи зі статусами
        self.user_role_repo = UserRoleRepository(db_session) # Для роботи з ролями

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[UserModel]:
        user = await self.repository.get(id=user_id)
        # Не кидаємо NotFoundException тут, щоб дозволити перевірку існування
        return user

    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        return await self.repository.get_by_email(email=email)

    async def get_user_by_username(self, username: str) -> Optional[UserModel]:
        return await self.repository.get_by_username(username=username)

    async def get_user_by_identifier(self, identifier: str) -> Optional[UserModel]:
        return await self.repository.get_by_identifier(identifier=identifier)

    async def create_user(self, *, obj_in: UserCreateSchema) -> UserModel:
        logger.debug(f"Спроба створити користувача з email: {obj_in.email}")
        existing_user_email = await self.get_user_by_email(email=obj_in.email)
        if existing_user_email:
            logger.warning(f"Користувач з email {obj_in.email} вже існує.")
            raise BadRequestException(detail="Користувач з таким email вже існує.")

        if obj_in.username:
            existing_user_username = await self.get_user_by_username(username=obj_in.username)
            if existing_user_username:
                logger.warning(f"Користувач з username {obj_in.username} вже існує.")
                raise BadRequestException(detail="Користувач з таким ім'ям користувача вже існує.")

        if obj_in.phone_number:
            existing_user_phone = await self.repository.get_by_phone_number(db=self.db_session, phone_number=obj_in.phone_number)
            if existing_user_phone:
                logger.warning(f"Користувач з номером телефону {obj_in.phone_number} вже існує.")
                raise BadRequestException(detail="Користувач з таким номером телефону вже існує.")

        # Валідація пароля вже виконана на рівні схеми UserCreateSchema
        hashed_password = get_password_hash(obj_in.password)
        # Виключаємо confirm_password при створенні даних для моделі
        user_create_data = obj_in.model_dump(exclude={"password", "confirm_password"}, exclude_unset=True)
        user_create_data["hashed_password"] = hashed_password

        # Встановлення початкового статусу
        # user_type_code встановлюється за замовчуванням в схемі або передається
        if not user_create_data.get("state_id"):
            initial_status = await self.status_repo.get_by_code(code=STATUS_PENDING_EMAIL_VERIFICATION_CODE)
            if initial_status:
                user_create_data["state_id"] = initial_status.id
            else:
                logger.error(f"Початковий статус {STATUS_PENDING_EMAIL_VERIFICATION_CODE} не знайдено в довіднику! Користувач буде створений без явного статусу.")

        # Логіка для `role_id` видалена, оскільки `UserModel` не має цього поля.
        # `user_type_code` керує типом користувача (superadmin, user, bot).
        # Ролі в групах керуються через `GroupMembershipModel`.

        db_user = await self.repository.create_with_data(data=user_create_data)
        logger.info(f"Створено нового користувача: {db_user.email} (ID: {db_user.id})")
        return db_user

    async def update_user_profile(self, *, current_user: UserModel, obj_in: UserUpdateSchema) -> UserModel:
        update_data = obj_in.model_dump(exclude_unset=True)

        if "username" in update_data and update_data["username"] != current_user.username:
            existing_user_username = await self.get_user_by_username(username=update_data["username"])
            if existing_user_username and existing_user_username.id != current_user.id:
                raise BadRequestException(detail="Користувач з таким ім'ям користувача вже існує.")

        # Email не можна змінювати через цей метод, для цього має бути окремий процес з верифікацією
        if "email" in update_data:
            del update_data["email"]

        updated_user = await self.repository.update(db_obj=current_user, obj_in=update_data)
        logger.info(f"Оновлено профіль користувача {current_user.email}.")
        return updated_user

    async def admin_update_user(
        self, *, user_to_update_id: uuid.UUID, obj_in: UserAdminUpdateSchema, admin_user: UserModel
    ) -> UserModel:
        user_to_update = await self.repository.get_user_with_details(db=self.db_session, user_id=user_to_update_id)
        if not user_to_update:
            raise NotFoundException(f"Користувача з ID {user_to_update_id} не знайдено для оновлення.")

        if admin_user.user_type_code != USER_TYPE_SUPERADMIN:
            can_admin_group_user = False
            if admin_user.id == user_to_update_id: # Адмін може редагувати свій профіль (хоча для цього є update_user_profile)
                pass # Дозволено, але UserAdminUpdateSchema може містити поля, які він не може сам собі міняти

            # Перевірка, чи є admin_user адміном групи, до якої належить user_to_update
            # Завантажуємо деталі admin_user, якщо вони ще не завантажені повністю
            if not admin_user.group_memberships or not hasattr(admin_user.group_memberships[0], 'role'): # Приклад перевірки, чи завантажені деталі
                admin_user_details = await self.repository.get_user_with_details(db=self.db_session, user_id=admin_user.id)
                if not admin_user_details: # Малоймовірно, якщо admin_user передано
                     raise ForbiddenException("Не вдалося перевірити права адміністратора.")
                admin_user_group_memberships = admin_user_details.group_memberships
            else:
                admin_user_group_memberships = admin_user.group_memberships

            admin_group_ids_where_admin = {
                gm.group_id for gm in admin_user_group_memberships if gm.role and gm.role.code == ROLE_ADMIN_CODE
            }

            target_user_group_ids = {gm.group_id for gm in user_to_update.group_memberships}

            if admin_group_ids_where_admin.intersection(target_user_group_ids):
                can_admin_group_user = True

            if not can_admin_group_user:
                 raise ForbiddenException("Недостатньо прав для оновлення користувача. Адміністратор групи може оновлювати тільки користувачів своїх груп.")
            # TODO: Додати більш гранульовану перевірку: адмін групи не може підвищити/змінити роль іншого адміна,
            #       не може змінити user_type_code тощо.

        update_data = obj_in.model_dump(exclude_unset=True)

        if "email" in update_data and update_data["email"] != user_to_update.email:
            existing = await self.get_user_by_email(email=update_data["email"])
            if existing and existing.id != user_to_update.id:
                raise BadRequestException(detail="Користувач з таким email вже існує.")

        if "username" in update_data and update_data["username"] != user_to_update.username:
            existing = await self.get_user_by_username(username=update_data["username"])
            if existing and existing.id != user_to_update.id:
                raise BadRequestException(detail="Користувач з таким ім'ям користувача вже існує.")

        if "password" in update_data and update_data["password"]:
            update_data["hashed_password"] = get_password_hash(update_data["password"])
            del update_data["password"]

        if "role_code" in update_data and update_data["role_code"]:
            role = await self.user_role_repo.get_by_code(code=update_data["role_code"])
            if not role:
                raise BadRequestException(f"Роль з кодом '{update_data['role_code']}' не знайдена.")
            update_data["role_id"] = role.id
            del update_data["role_code"]

        if "state_code" in update_data and update_data["state_code"]:
            state = await self.status_repo.get_by_code(code=update_data["state_code"])
            if not state: # Малоймовірно, якщо статуси ініціалізовані
                raise BadRequestException(f"Статус з кодом '{update_data['state_code']}' не знайдено.")
            update_data["state_id"] = state.id
            del update_data["state_code"]
            # Спеціальна логіка для is_active та is_email_verified на основі state_code
            if update_data["state_code"] == STATUS_ACTIVE_CODE:
                update_data["is_active"] = True
                update_data["is_email_verified"] = True # Припускаємо, що активний означає верифікований
            # ... інші правила ...


        updated_user = await self.repository.update(db_obj=user_to_update, obj_in=update_data)
        logger.info(f"Адміністратор {admin_user.email} оновив користувача {updated_user.email}.")
        return updated_user

    async def delete_user(self, *, user_to_delete_id: uuid.UUID, soft_delete: bool = True, actor: UserModel) -> Optional[UserModel]:
        user_to_delete = await self.repository.get_user_with_details(db=self.db_session, user_id=user_to_delete_id)
        if not user_to_delete:
            raise NotFoundException(f"Користувача з ID {user_to_delete_id} не знайдено для видалення.")

        # Перевірка прав актора
        if actor.user_type_code != USER_TYPE_SUPERADMIN:
            if actor.id == user_to_delete_id:
                # Користувач може "видалити" (деактивувати) свій акаунт, якщо це дозволено
                # Це, ймовірно, має бути soft_delete і зміна статусу на "деактивований" або "заплановано видалення"
                # Поки що, якщо користувач видаляє сам себе, це буде soft_delete.
                if not soft_delete: # Користувач не може себе фізично видалити
                    raise ForbiddenException("Ви не можете фізично видалити власний обліковий запис.")
            else:
                # Перевірка, чи є actor адміном групи, до якої належить user_to_delete
                # Завантажуємо деталі actor, якщо вони ще не завантажені повністю
                if not actor.group_memberships or not hasattr(actor.group_memberships[0], 'role'):
                    actor_details = await self.repository.get_user_with_details(db=self.db_session, user_id=actor.id)
                    if not actor_details:
                        raise ForbiddenException("Не вдалося перевірити права адміністратора.")
                    actor_group_memberships = actor_details.group_memberships
                else:
                    actor_group_memberships = actor.group_memberships

                admin_group_ids_where_admin = {
                    gm.group_id for gm in actor_group_memberships if gm.role and gm.role.code == ROLE_ADMIN_CODE
                }
                target_user_group_ids = {gm.group_id for gm in user_to_delete.group_memberships}

                can_admin_delete_user = False
                if admin_group_ids_where_admin.intersection(target_user_group_ids):
                    # Перевірка, чи не намагається адмін групи видалити іншого адміна тієї ж групи
                    # або користувача з вищим user_type_code (наприклад, superadmin)
                    if user_to_delete.user_type_code == USER_TYPE_SUPERADMIN:
                        raise ForbiddenException("Адміністратор групи не може видалити супер-адміністратора.")

                    is_target_also_admin_in_common_groups = False
                    for gm_target in user_to_delete.group_memberships:
                        if gm_target.group_id in admin_group_ids_where_admin and \
                           gm_target.role and gm_target.role.code == ROLE_ADMIN_CODE:
                            is_target_also_admin_in_common_groups = True
                            break
                    if is_target_also_admin_in_common_groups and user_to_delete.id != actor.id : # Адмін не може видалити іншого адміна спільної групи
                        raise ForbiddenException("Адміністратор групи не може видалити іншого адміністратора цієї ж групи.")

                    can_admin_delete_user = True

                if not can_admin_delete_user:
                    raise ForbiddenException("Недостатньо прав для видалення цього користувача. Адміністратор групи може видаляти тільки звичайних користувачів своїх груп.")

        # Супер-адмін може видаляти будь-кого (крім, можливо, себе, якщо є така логіка)
        if actor.user_type_code == USER_TYPE_SUPERADMIN and actor.id == user_to_delete_id and not soft_delete:
            raise ForbiddenException("Супер-адміністратор не може фізично видалити сам себе.")


        if soft_delete:
            deleted_user = await self.repository.soft_delete(db_obj=user_to_delete)
            logger.info(f"Користувача {user_to_delete.email} м'яко видалено користувачем {actor.email}.")
            return deleted_user
        else: # Hard delete
            if actor.user_type_code != USER_TYPE_SUPERADMIN:
                raise ForbiddenException("Лише супер-адміністратор може фізично видаляти користувачів.")
            # Зберігаємо email перед видаленням для логування, оскільки об'єкт буде видалено
            user_email_before_delete = user_to_delete.email
            await self.repository.delete(id=user_to_delete_id)
            logger.info(f"Користувача {user_email_before_delete} фізично видалено супер-адміністратором {actor.email}.")
            return user_to_delete # Повертаємо об'єкт перед видаленням

    async def get_active_user_by_id_for_auth(self, user_id: uuid.UUID) -> UserModel:
        """
        Отримує активного користувача за ID з деталями, необхідними для автентифікації.
        Кидає винятки, якщо користувач не знайдений, видалений, неактивний або має невідповідний статус.
        """
        user = await self.repository.get_user_with_details(db=self.db_session, user_id=user_id)
        if not user:
            raise NotFoundException(detail="Користувача не знайдено.")
        if user.is_deleted: # Перевірка "м'якого" видалення
            logger.warning(f"Спроба автентифікації для видаленого користувача: {user.email}")
            raise ForbiddenException(detail="Обліковий запис користувача видалено.")

        # UserModel має поле is_active, яке успадковано від BaseMainModel (default=False).
        # Це поле повинно встановлюватися в True, коли користувач стає активним (наприклад, після верифікації email).
        # Поки що, якщо state_id є, і статус ACTIVE, то is_active теж має бути True.
        # Якщо user.is_active є, то використовуємо його.
        # У UserModel немає is_active, воно є в BaseMainModel.
        # Потрібно переконатися, що is_active коректно встановлюється.
        # Припускаємо, що `user.state.code == STATUS_ACTIVE_CODE` є головним критерієм активності.

        if not user.state:
            logger.error(f"У користувача {user.email} відсутній об'єкт статусу (state is None). Вважаємо неактивним.")
            raise ForbiddenException(detail="Статус облікового запису невизначений. Вхід заборонено.")

        if user.state.code != STATUS_ACTIVE_CODE:
            logger.warning(f"Спроба автентифікації для користувача {user.email} зі статусом '{user.state.code}' ('{user.state.name}').")
            raise ForbiddenException(detail=f"Обліковий запис має статус '{user.state.name}'. Вхід заборонено.")

        # Додаткова перевірка на is_email_verified, якщо це вимога для входу
        # if not user.is_email_verified:
        #     logger.warning(f"Спроба входу для користувача {user.email} з непідтвердженим email.")
        #     raise ForbiddenException(detail="Email не підтверджено. Будь ласка, підтвердіть свій email.")

        logger.debug(f"Користувач {user_id} ({user.email}) пройшов перевірку активності для автентифікації.")
        return user

    async def change_user_password(self, *, user: UserModel, old_password: str, new_password: str) -> bool:
        from backend.app.src.core.validators import is_strong_password

        if not verify_password(old_password, user.hashed_password):
            logger.warning(f"Невдала спроба зміни пароля для користувача {user.email}: неправильний старий пароль.")
            raise BadRequestException(detail="Неправильний поточний пароль.")

        if old_password == new_password:
            raise BadRequestException(detail="Новий пароль не може співпадати зі старим.")

        is_strong_password(new_password) # Кине ValueError, якщо пароль не відповідає вимогам

        user.hashed_password = get_password_hash(new_password)
        await self.repository.update(db_obj=user, obj_in={"hashed_password": user.hashed_password})
        logger.info(f"Пароль для користувача {user.email} успішно змінено.")

        # TODO: Інвалідувати всі активні сесії/refresh токени цього користувача (крім поточного, якщо можливо).
        #       Це може вимагати виклику TokenService або SessionService.
        #       Приклад: await TokenService(self.db_session).revoke_all_refresh_tokens_for_user(user.id)
        return True

    async def reset_user_password(self, *, user: UserModel, new_password: str) -> bool:
        from backend.app.src.core.validators import is_strong_password
        is_strong_password(new_password) # Кине ValueError, якщо пароль не відповідає вимогам

        user.hashed_password = get_password_hash(new_password)
        await self.repository.update(db_obj=user, obj_in={"hashed_password": user.hashed_password})
        logger.info(f"Пароль для користувача {user.email} успішно скинуто.")

        # TODO: Інвалідувати всі активні сесії/refresh токени цього користувача.
        #       Приклад: await TokenService(self.db_session).revoke_all_refresh_tokens_for_user(user.id)
        return True

    async def mark_email_as_verified(self, *, user: UserModel) -> UserModel:
        if user.is_email_verified:
            logger.info(f"Email для користувача {user.email} вже підтверджено.")
            return user

        update_data = {"is_email_verified": True}
        active_status = await self.status_repo.get_by_code(code=STATUS_ACTIVE_CODE)
        if active_status:
            update_data["state_id"] = active_status.id

        updated_user = await self.repository.update(db_obj=user, obj_in=update_data)
        logger.info(f"Email для користувача {user.email} успішно підтверджено, статус оновлено.")
        return updated_user

# Екземпляр сервісу не створюємо тут глобально.
