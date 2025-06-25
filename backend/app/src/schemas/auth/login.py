# backend/app/src/schemas/auth/login.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для процесу входу користувача (логіну).
"""

from pydantic import BaseModel as PydanticBaseModel, Field, EmailStr
from typing import Optional, Union

from backend.app.src.schemas.base import BaseSchema

# --- Схема для запиту на вхід (логін) ---
class LoginRequestSchema(BaseSchema):
    """
    Схема для даних, що надходять від користувача при спробі входу.
    Користувач може увійти за допомогою email або номера телефону.
    """
    # Використовуємо Union для username, щоб дозволити або email, або телефон.
    # Або можна зробити два окремі поля і валідувати, що хоча б одне заповнене.
    # Краще мати одне поле `username` і на сервісному рівні визначати, чи це email, чи телефон.
    # Або ж, якщо API чітко розрізняє, то можна мати:
    # email: Optional[EmailStr] = None
    # phone_number: Optional[str] = None
    # І валідатор, що хоча б одне з них є.
    #
    # Поки що зробимо простіше: одне поле `identifier`, яке може бути email або телефоном.
    identifier: str = Field(..., description="Ідентифікатор користувача для входу (email або номер телефону)")
    password: str = Field(..., description="Пароль користувача")

    # Додаткові поля, які можуть бути корисними
    # client_fingerprint: Optional[str] = Field(None, description="Відбиток клієнта для безпеки сесії")
    # remember_me: bool = Field(default=False, description="Чи запам'ятати користувача (впливає на час життя refresh токена)")

    @field_validator('identifier')
    @classmethod
    def identifier_must_be_email_or_phone(cls, value: str) -> str:
        # Проста перевірка, чи це схоже на email або телефон.
        # Більш строга валідація - на сервісному рівні при пошуку користувача.
        if "@" not in value:
            # Якщо не email, перевіряємо, чи схоже на телефон (цифри, можливо +)
            cleaned_phone = value.lstrip('+')
            if not cleaned_phone.isdigit():
                raise ValueError("Ідентифікатор має бути email адресою або номером телефону.")
        # Якщо "@" є, Pydantic EmailStr (якщо б використовували) перевірив би формат email.
        # Тут ми не використовуємо EmailStr для identifier, щоб дозволити телефон.
        return value

# --- Схема для запиту на скидання пароля (перший крок - запит на email/телефон) ---
class PasswordResetRequestSchema(BaseSchema):
    email_or_phone: str = Field(..., description="Email або номер телефону користувача для скидання пароля")

    @field_validator('email_or_phone')
    @classmethod
    def identifier_must_be_email_or_phone(cls, value: str) -> str: # Назва та сама, але для іншого поля
        if "@" not in value:
            cleaned_phone = value.lstrip('+')
            if not cleaned_phone.isdigit():
                raise ValueError("Ідентифікатор має бути email адресою або номером телефону.")
        return value

# --- Схема для підтвердження скидання пароля (другий крок - з токеном та новим паролем) ---
class PasswordResetConfirmSchema(BaseSchema):
    reset_token: str = Field(..., description="Токен скидання пароля, отриманий користувачем")
    new_password: str = Field(..., min_length=8, description="Новий пароль")
    confirm_new_password: str = Field(..., description="Підтвердження нового пароля")

    @model_validator(mode='after')
    def check_passwords_match(cls, data: 'PasswordResetConfirmSchema') -> 'PasswordResetConfirmSchema':
        if data.new_password != data.confirm_new_password:
            raise ValueError("Новий пароль та його підтвердження не співпадають.")
        # TODO: Додати більш складну валідацію надійності пароля (is_strong_password з core.validators)
        if len(data.new_password) < 8: # Базова перевірка, вже є в min_length
             raise ValueError("Новий пароль повинен містити щонайменше 8 символів.")
        return data

# --- Схема для запиту на підтвердження email ---
class EmailVerificationRequestSchema(BaseSchema):
    verification_token: str = Field(..., description="Токен підтвердження email")

# --- Схема для запиту на повторну відправку листа підтвердження email ---
class ResendEmailVerificationSchema(BaseSchema):
    email: EmailStr = Field(..., description="Email адреса для повторної відправки листа підтвердження")


# TODO: Перевірити відповідність `technical-task.md`:
# - "авторизація, реєстрація за поштою/телефоном та інше, нагадування пароль, відновлення пароля"
#   - `LoginRequestSchema` для авторизації.
#   - `PasswordResetRequestSchema` та `PasswordResetConfirmSchema` для відновлення пароля.
#   - `EmailVerificationRequestSchema` та `ResendEmailVerificationSchema` для підтвердження email.
#   - Реєстрація - `UserCreateSchema` з `user.py`.
#
# `LoginRequestSchema.identifier` - гнучке поле для email або телефону.
# Сервісний шар буде розбирати, що саме передано.
# Можна додати валідатор для `identifier`, щоб перевірити, чи це валідний email або телефонний номер (хоча б приблизно).
#
# Схеми для скидання пароля та підтвердження email покривають основні сценарії.
# Валідація надійності нового пароля в `PasswordResetConfirmSchema` важлива.
#
# Все виглядає узгоджено з базовими потребами автентифікації.
# Поля `client_fingerprint` та `remember_me` в `LoginRequestSchema` (закоментовані)
# можуть бути додані для розширення функціоналу безпеки та зручності.
# Наприклад, `remember_me` може впливати на `expires_at` для `RefreshTokenModel`.
# `client_fingerprint` може зберігатися в `SessionModel` або `RefreshTokenModel`
# для додаткової перевірки безпеки.
# Поки що залишаю базові версії схем.
