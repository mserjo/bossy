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

        # TODO: Додати перевірку унікальності phone_number, якщо він використовується.

        hashed_password = get_password_hash(obj_in.password)
        user_create_data = obj_in.model_dump(exclude={"password"}, exclude_unset=True)
        user_create_data["hashed_password"] = hashed_password

        # Встановлення початкового статусу та ролі
        if not user_create_data.get("state_id"):
            initial_status = await self.status_repo.get_by_code(code=STATUS_PENDING_EMAIL_VERIFICATION_CODE)
            if initial_status:
                user_create_data["state_id"] = initial_status.id
            else: # Fallback, якщо статус не знайдено (малоймовірно при правильній ініціалізації)
                logger.error(f"Початковий статус {STATUS_PENDING_EMAIL_VERIFICATION_CODE} не знайдено в довіднику!")

        if not user_create_data.get("role_id") and not obj_in.role_code: # Якщо ні ID, ні код ролі не передано
            default_role = await self.user_role_repo.get_by_code(code=ROLE_USER_CODE)
            if default_role:
                user_create_data["role_id"] = default_role.id
            else:
                logger.error(f"Дефолтна роль {ROLE_USER_CODE} не знайдена в довіднику!")
        elif obj_in.role_code and not user_create_data.get("role_id"): # Якщо передано код ролі
            role_obj = await self.user_role_repo.get_by_code(code=obj_in.role_code)
            if role_obj:
                user_create_data["role_id"] = role_obj.id
            else:
                logger.warning(f"Роль з кодом {obj_in.role_code} не знайдена, не вдалося встановити роль для нового користувача.")


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
        if admin_user.user_type_code != USER_TYPE_SUPERADMIN:
            # TODO: Додати перевірку, чи може адмін групи змінювати користувачів своєї групи
            raise ForbiddenException("Недостатньо прав для оновлення користувача.")

        user_to_update = await self.get_user_by_id(user_id=user_to_update_id)
        if not user_to_update: # get_user_by_id вже кидає NotFoundException
            raise NotFoundException(f"Користувача з ID {user_to_update_id} не знайдено для оновлення.")

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
        # Перевірка прав актора (наприклад, чи може він видаляти цього користувача)
        if actor.user_type_code != USER_TYPE_SUPERADMIN and actor.id != user_to_delete_id:
             # TODO: Додати логіку, чи може адмін групи видаляти користувачів
            raise ForbiddenException("Недостатньо прав для видалення цього користувача.")

        user_to_delete = await self.get_user_by_id(user_id=user_to_delete_id)
        if not user_to_delete:
            raise NotFoundException(f"Користувача з ID {user_to_delete_id} не знайдено для видалення.")

        if soft_delete:
            deleted_user = await self.repository.soft_delete(db_obj=user_to_delete)
            logger.info(f"Користувача {user_to_delete.email} м'яко видалено користувачем {actor.email}.")
            return deleted_user
        else: # Hard delete
            if actor.user_type_code != USER_TYPE_SUPERADMIN:
                raise ForbiddenException("Лише супер-адміністратор може фізично видаляти користувачів.")
            await self.repository.delete(id=user_to_delete_id)
            logger.info(f"Користувача {user_to_delete.email} фізично видалено супер-адміністратором {actor.email}.")
            return user_to_delete # Повертаємо об'єкт перед видаленням

    async def get_active_user_by_id_for_auth(self, user_id: uuid.UUID) -> UserModel:
        user = await self.repository.get_active_user_with_details(id=user_id) # Репозиторій має завантажити state та role
        if not user:
            raise NotFoundException(detail="Користувача не знайдено.")
        if user.is_deleted:
            raise ForbiddenException(detail="Обліковий запис користувача видалено.")
        if not user.is_active: # Це поле може дублювати логіку state_id
            raise ForbiddenException(detail="Обліковий запис користувача неактивний.")

        # Перевірка статусу через state.code, якщо state завантажено
        if user.state and user.state.code != STATUS_ACTIVE_CODE:
            logger.warning(f"Спроба автентифікації для користувача {user.email} зі статусом '{user.state.code}'.")
            raise ForbiddenException(detail=f"Обліковий запис має статус '{user.state.name}'. Вхід заборонено.")

        logger.debug(f"Користувач {user_id} пройшов перевірку активності для автентифікації.")
        return user

    async def change_user_password(self, *, user: UserModel, old_password: str, new_password: str) -> bool:
        if not verify_password(old_password, user.hashed_password):
            logger.warning(f"Невдала спроба зміни пароля для користувача {user.email}: неправильний старий пароль.")
            raise BadRequestException(detail="Неправильний поточний пароль.")

        if old_password == new_password:
            raise BadRequestException(detail="Новий пароль не може співпадати зі старим.")
        # TODO: Додати перевірку складності нового пароля згідно налаштувань системи

        user.hashed_password = get_password_hash(new_password)
        await self.repository.update(db_obj=user, obj_in={"hashed_password": user.hashed_password})
        logger.info(f"Пароль для користувача {user.email} успішно змінено.")
        # TODO: Інвалідувати всі активні сесії/токени цього користувача (крім поточного, якщо можливо)
        return True

    async def reset_user_password(self, *, user: UserModel, new_password: str) -> bool:
        # TODO: Додати перевірку складності нового пароля
        user.hashed_password = get_password_hash(new_password)
        await self.repository.update(db_obj=user, obj_in={"hashed_password": user.hashed_password})
        logger.info(f"Пароль для користувача {user.email} успішно скинуто.")
        # TODO: Інвалідувати всі активні сесії/токени
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
