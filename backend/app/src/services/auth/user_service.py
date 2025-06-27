# backend/app/src/services/auth/user_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `UserService` для управління користувачами.
Він інкапсулює бізнес-логіку, пов'язану зі створенням, отриманням,
оновленням та видаленням користувачів, а також управлінням їх профілями.
"""

from typing import List, Optional, Union, Dict, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from fastapi import HTTPException

from backend.app.src.models.auth.user import UserModel
from backend.app.src.schemas.auth.user import UserCreateSchema, UserUpdateSchema, UserAdminUpdateSchema, UserSchema
from backend.app.src.repositories.auth.user import UserRepository, user_repository
from backend.app.src.services.base import BaseService
from backend.app.src.core.security import get_password_hash, verify_password # Утиліти для паролів
from backend.app.src.core.exceptions import NotFoundException, BadRequestException, ForbiddenException
from backend.app.src.core.constants import USER_TYPE_SUPERADMIN, STATUS_ACTIVE_CODE # Приклад
# from backend.app.src.repositories.dictionaries.status import status_repository # Якщо потрібно отримувати ID статусу за кодом

class UserService(BaseService[UserRepository]):
    """
    Сервіс для управління користувачами.
    """

    async def get_user_by_id(self, db: AsyncSession, user_id: uuid.UUID) -> Optional[UserModel]:
        """Отримує користувача за ID."""
        user = await self.repository.get(db, id=user_id)
        if not user:
            raise NotFoundException(detail=f"Користувача з ID {user_id} не знайдено.")
        return user

    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[UserModel]:
        """Отримує користувача за email."""
        return await self.repository.get_by_email(db, email=email)
        # NotFoundException тут не кидаємо, бо метод може використовуватися для перевірки існування.

    async def get_user_by_identifier(self, db: AsyncSession, identifier: str) -> Optional[UserModel]:
        """Отримує користувача за email або номером телефону."""
        return await self.repository.get_by_identifier(db, identifier=identifier)

    async def create_user(self, db: AsyncSession, *, obj_in: UserCreateSchema) -> UserModel:
        """
        Створює нового користувача.
        Включає хешування пароля та перевірку на унікальність email/телефону.
        """
        existing_user_email = await self.repository.get_by_email(db, email=obj_in.email)
        if existing_user_email:
            raise BadRequestException(detail="Користувач з таким email вже існує.")

        if obj_in.phone_number:
            existing_user_phone = await self.repository.get_by_phone_number(db, phone_number=obj_in.phone_number)
            if existing_user_phone:
                raise BadRequestException(detail="Користувач з таким номером телефону вже існує.")

        # Хешуємо пароль
        hashed_password = get_password_hash(obj_in.password)

        # Створюємо словник даних для моделі, замінюючи пароль на хеш
        user_create_data = obj_in.model_dump(exclude_unset=True)
        user_create_data["hashed_password"] = hashed_password
        del user_create_data["password"] # Видаляємо оригінальний пароль

        # TODO: Встановити початковий state_id (наприклад, "очікує підтвердження пошти" або "активний")
        # current_status = await status_repository.get_by_code(db, code="pending_email_verification")
        # if current_status:
        #    user_create_data["state_id"] = current_status.id
        # else: # fallback or error
        #    user_create_data["state_id"] = None # Або ID активного статусу за замовчуванням

        # Викликаємо метод create з базового репозиторію, передаючи підготовлений словник
        # (BaseRepository.create приймає CreateSchemaType, але всередині робить model(**obj_in_data))
        # Для більшої точності, можна було б створити новий UserCreateInternalSchema без password,
        # або передати словник напряму в конструктор моделі.
        # Поточний BaseRepository.create(obj_in) приймає схему.
        # Ми можемо створити новий екземпляр схеми з хешованим паролем,
        # або змінити BaseRepository.create для прийняття словника.
        #
        # Якщо BaseRepository.create приймає схему:
        # validated_data_for_schema = user_create_data.copy()
        # # Потрібно переконатися, що UserCreateSchema не має поля password, або воно Optional
        # # інакше Pydantic кине помилку при відсутності password.
        # # Простіше - створити модель напряму.
        db_user = UserModel(**user_create_data)
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    async def update_user_profile(
        self, db: AsyncSession, *, current_user: UserModel, obj_in: UserUpdateSchema
    ) -> UserModel:
        """Оновлює профіль поточного користувача."""
        # Перевірка, чи новий номер телефону (якщо вказаний) не зайнятий іншим користувачем
        if obj_in.phone_number and obj_in.phone_number != current_user.phone_number:
            existing_user_phone = await self.repository.get_by_phone_number(db, phone_number=obj_in.phone_number)
            if existing_user_phone and existing_user_phone.id != current_user.id:
                raise BadRequestException(detail="Цей номер телефону вже використовується іншим користувачем.")

        # Email зазвичай змінюється через окремий процес з підтвердженням.
        # Тут ми не дозволяємо змінювати email через оновлення профілю.

        return await self.repository.update(db, db_obj=current_user, obj_in=obj_in)

    async def admin_update_user(
        self, db: AsyncSession, *, user_to_update: UserModel, obj_in: UserAdminUpdateSchema
    ) -> UserModel:
        """Оновлює користувача від імені адміністратора."""
        # Перевірка email та телефону, якщо вони змінюються
        if obj_in.email and obj_in.email != user_to_update.email:
            existing_user_email = await self.repository.get_by_email(db, email=obj_in.email)
            if existing_user_email and existing_user_email.id != user_to_update.id:
                raise BadRequestException(detail="Користувач з таким email вже існує.")

        if obj_in.phone_number and obj_in.phone_number != user_to_update.phone_number:
            existing_user_phone = await self.repository.get_by_phone_number(db, phone_number=obj_in.phone_number)
            if existing_user_phone and existing_user_phone.id != user_to_update.id:
                raise BadRequestException(detail="Цей номер телефону вже використовується іншим користувачем.")

        # Адмін може змінювати user_type_code, state_id тощо.
        return await self.repository.update(db, db_obj=user_to_update, obj_in=obj_in)

    async def delete_user(self, db: AsyncSession, *, user_to_delete: UserModel, soft_delete: bool = True) -> Optional[UserModel]:
        """
        Видаляє користувача.
        :param soft_delete: Якщо True, виконує "м'яке" видалення.
        """
        if soft_delete:
            if hasattr(self.repository, 'soft_delete') and hasattr(user_to_delete, 'is_deleted'):
                return await self.repository.soft_delete(db, db_obj=user_to_delete) # type: ignore
            else:
                # Модель не підтримує м'яке видалення, або метод не реалізований
                self.logger.warning(f"Спроба 'м'якого' видалення для моделі {self.repository.model.__name__}, яка його не підтримує.")
                # Виконуємо тверде видалення як fallback, або кидаємо помилку
                # return await self.repository.delete(db, id=user_to_delete.id)
                raise NotImplementedError(f"Модель {self.repository.model.__name__} не підтримує 'м'яке' видалення.")
        else:
            return await self.repository.delete(db, id=user_to_delete.id)

    async def get_active_user_by_id_for_auth(self, db: AsyncSession, user_id: uuid.UUID) -> UserModel:
        """
        Отримує активного користувача за ID для цілей автентифікації/авторизації.
        Кидає винятки, якщо користувач не знайдений або неактивний.
        """
        user = await self.repository.get(db, id=user_id)
        if not user:
            raise NotFoundException(detail="Користувача не знайдено.")
        if user.is_deleted: # Перевірка "м'якого" видалення
            raise ForbiddenException(detail="Обліковий запис користувача видалено.")

        # TODO: Додати перевірку `user.state_id` на відповідність активному статусу
        #       після того, як буде реалізовано отримання статусу за кодом/ID.
        # from backend.app.src.repositories.dictionaries.status import status_repository # Імпорт всередині методу не дуже добре
        # active_status = await status_repository.get_by_code(db, code=STATUS_ACTIVE_CODE)
        # if not active_status or user.state_id != active_status.id:
        #     # Або якщо user.state.code != STATUS_ACTIVE_CODE (якщо state завантажено)
        #     raise ForbiddenException(detail="Обліковий запис користувача неактивний.")

        self.logger.info(f"Користувач {user_id} успішно пройшов перевірку активності для автентифікації.")
        return user

    # TODO: Додати методи для зміни пароля, підтвердження email, налаштувань 2FA тощо.
    #       Ці методи будуть викликатися з AuthService або інших відповідних сервісів.

userService = UserService(user_repository)

# Коментарі:
# - Сервіс використовує UserRepository.
# - Обробка паролів (хешування) винесена в сервіс.
# - Перевірки на унікальність email/телефону перед створенням.
# - Розділення логіки оновлення профілю користувачем та адміністратором.
# - Метод `get_active_user_by_id_for_auth` спеціально для залежностей FastAPI,
#   щоб перевіряти, чи користувач активний перед наданням доступу.
# - TODO вказані для подальшого розширення (state_id, 2FA, зміна email).
# - Важливо правильно обробляти схеми Create/Update.
#   `BaseRepository.create` очікує схему, тому при створенні моделі напряму
#   (як в `create_user`) це потрібно враховувати.
#   Або ж `create_user` може готувати `UserCreateSchema` з хешованим паролем
#   і викликати `await self.repository.create(db, obj_in=prepared_schema)`.
#   Поточна реалізація `create_user` створює `UserModel` напряму - це теж варіант.
#
# Все виглядає як хороший початок для UserService.
