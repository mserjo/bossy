# backend/app/src/repositories/auth/user.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `UserModel`.
Надає методи для взаємодії з таблицею користувачів в базі даних,
включаючи специфічні методи пошуку користувачів.
"""

from typing import Optional, List, Dict, Any
import uuid
from sqlalchemy import select, update # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload # type: ignore

from backend.app.src.models.auth.user import UserModel
from backend.app.src.schemas.auth.user import UserCreateSchema, UserUpdateSchema, UserAdminUpdateSchema # Використовуємо різні схеми для оновлення
from backend.app.src.repositories.base import BaseRepository
from backend.app.src.core.constants import USER_TYPE_SUPERADMIN # Для перевірки is_superuser

class UserRepository(BaseRepository[UserModel, UserCreateSchema, UserAdminUpdateSchema]): # UpdateSchema тут - UserAdminUpdateSchema для повноти
    """
    Репозиторій для роботи з моделлю користувачів (`UserModel`).
    Успадковує базові CRUD-операції від `BaseRepository`.
    """

    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[UserModel]:
        """
        Отримує користувача за його електронною поштою.

        :param db: Асинхронна сесія бази даних.
        :param email: Електронна пошта користувача.
        :return: Об'єкт UserModel або None, якщо користувача не знайдено.
        """
        statement = select(self.model).where(self.model.email == email)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_phone_number(self, db: AsyncSession, *, phone_number: str) -> Optional[UserModel]:
        """
        Отримує користувача за його номером телефону.

        :param db: Асинхронна сесія бази даних.
        :param phone_number: Номер телефону користувача.
        :return: Об'єкт UserModel або None, якщо користувача не знайдено.
        """
        statement = select(self.model).where(self.model.phone_number == phone_number)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_identifier(self, db: AsyncSession, *, identifier: str) -> Optional[UserModel]:
        """
        Отримує користувача за ідентифікатором, який може бути email або номером телефону.

        :param db: Асинхронна сесія бази даних.
        :param identifier: Ідентифікатор (email або номер телефону).
        :return: Об'єкт UserModel або None, якщо користувача не знайдено.
        """
        # TODO: Додати валідацію identifier, щоб визначити, чи це email, чи телефон,
        #       або покладатися на те, що пошук по обох полях буде коректним.
        #       Поки що простий пошук по обох полях через OR.
        statement = select(self.model).where(
            (self.model.email == identifier) | (self.model.phone_number == identifier)
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def is_superuser(self, user: UserModel) -> bool:
        """
        Перевіряє, чи є користувач супер-адміністратором.

        :param user: Об'єкт UserModel.
        :return: True, якщо користувач є супер-адміністратором, інакше False.
        """
        return user.user_type_code == USER_TYPE_SUPERADMIN

    async def update_user_auth_details(
        self, db: AsyncSession, *, user: UserModel,
        hashed_password: Optional[str] = None,
        is_2fa_enabled: Optional[bool] = None,
        otp_secret_encrypted: Optional[str] = None, # Може бути None для вимкнення 2FA
        otp_backup_codes_hashed: Optional[str] = None # Може бути None
    ) -> UserModel:
        """
        Оновлює специфічні для автентифікації деталі користувача.
        """
        update_data = {}
        if hashed_password is not None:
            update_data["hashed_password"] = hashed_password
        if is_2fa_enabled is not None:
            update_data["is_2fa_enabled"] = is_2fa_enabled
        if otp_secret_encrypted is not None or (is_2fa_enabled == False and user.is_2fa_enabled): # Дозволити скидання секрету при вимкненні 2FA
            update_data["otp_secret_encrypted"] = otp_secret_encrypted
        if otp_backup_codes_hashed is not None or (is_2fa_enabled == False and user.is_2fa_enabled):
            update_data["otp_backup_codes_hashed"] = otp_backup_codes_hashed

        if not update_data:
            return user # Нічого оновлювати

        return await self.update(db, db_obj=user, obj_in=update_data)

    # TODO: Додати метод для отримання користувача з усіма пов'язаними даними (групи, ролі в групах),
    #       якщо це часто потрібно (наприклад, для формування JWT з розширеними claims).
    #       Це може вимагати складних JOIN'ів або кількох запитів.
    #       Приклад:
    # async def get_user_with_details(self, db: AsyncSession, id: uuid.UUID) -> Optional[UserModel]:
    #     statement = select(self.model).where(self.model.id == id).options(
    #         selectinload(self.model.group_memberships).selectinload(GroupMembershipModel.role),
    #         selectinload(self.model.group_memberships).selectinload(GroupMembershipModel.group),
    #         selectinload(self.model.state) # Якщо є зв'язок state
    #     )
    #     result = await db.execute(statement)
    #     return result.scalar_one_or_none()

    # TODO: Розглянути, чи потрібен метод `authenticate` тут, чи це логіка сервісу.
    #       Зазвичай, репозиторій лише отримує дані, а сервіс перевіряє пароль.
    #       Тому `authenticate` краще залишити для `AuthService`.

    # TODO: Для `UserAdminUpdateSchema` та `UserUpdateSchema` (якщо вони будуть різними
    #       для параметра `UpdateSchemaType` в `BaseRepository.update`),
    #       можливо, знадобляться окремі методи оновлення або більш гнучкий `update`.
    #       Поточний `BaseRepository.update` приймає `Union[UpdateSchemaType, Dict]`.
    #       Якщо `UserAdminUpdateSchema` є типом для `UpdateSchemaType` тут, то це ОК.
    #       Для оновлення користувачем власного профілю (менше полів) може бути окремий метод
    #       або сервіс буде використовувати `UserUpdateSchema` і передавати словник в `update`.
    #       Це нормально.

user_repository = UserRepository(UserModel)

# Все виглядає добре.
# `get_by_identifier` - корисний метод.
# `is_superuser` - проста перевірка поля.
# `update_user_auth_details` - специфічний метод для оновлення чутливих даних.
# Зв'язки з `BaseRepository` та типами схем встановлені.
# Подальші специфічні методи (наприклад, пошук з пагінацією та фільтрами по певних полях користувача)
# можуть бути додані за потреби, або ж використовуватиметься `get_multi` / `get_paginated`
# з `BaseRepository` з відповідними фільтрами.
