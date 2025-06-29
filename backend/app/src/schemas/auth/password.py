# backend/app/src/schemas/auth/password.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми, пов'язані з управлінням паролями,
такі як запит на скидання пароля та підтвердження скидання пароля.
"""

from pydantic import Field, EmailStr, field_validator # Додано field_validator

from backend.app.src.schemas.base import BaseSchema
from backend.app.src.core.validators import is_strong_password


class PasswordResetRequestSchema(BaseSchema):
    """
    Схема для запиту на скидання пароля.
    Очікує email користувача, якому потрібно скинути пароль.
    """
    email: EmailStr = Field(..., description="Електронна пошта користувача для скидання пароля.")


class PasswordResetConfirmSchema(BaseSchema):
    """
    Схема для підтвердження скидання пароля.
    Очікує токен скидання та новий пароль.
    """
    token: str = Field(..., description="Токен для скидання пароля, отриманий на email.")
    new_password: str = Field(..., min_length=8, description="Новий пароль користувача.")
    confirm_new_password: str = Field(..., description="Підтвердження нового пароля.")

    @field_validator('new_password') # Виправлено на field_validator
    @classmethod
    def validate_new_password_strength(cls, value: str) -> str:
        is_strong_password(value) # Валідатор кине ValueError, якщо пароль не надійний
        return value

    # Для валідації confirm_new_password, яка залежить від new_password, краще використовувати model_validator
    # @field_validator('confirm_new_password')
    # @classmethod
    # def passwords_match(cls, value: str, values: dict) -> str: # values тут не працюватиме як очікується для field_validator
    #     # Потрібен model_validator для доступу до інших полів
    #     # if 'new_password' in values.data and value != values.data['new_password']:
    #     #     raise ValueError('Новий пароль та його підтвердження не співпадають.')
    #     return value
    # Замість цього, використаємо model_validator:
    from pydantic import model_validator

    @model_validator(mode='after')
    def check_passwords_match(cls, data: 'PasswordResetConfirmSchema') -> 'PasswordResetConfirmSchema':
        if data.new_password is not None and data.confirm_new_password is not None:
            if data.new_password != data.confirm_new_password:
                raise ValueError('Новий пароль та його підтвердження не співпадають.')
        return data

# Існуюча схема UserPasswordUpdateSchema (для зміни поточного пароля) знаходиться в user.py
# class PasswordChangeSchema(BaseSchema):
#     current_password: str = Field(..., description="Поточний пароль користувача.")
#     new_password: str = Field(..., min_length=8, description="Новий пароль.")
#     confirm_new_password: str = Field(..., description="Підтвердження нового пароля.")

#     @field_validator('new_password')
#     @classmethod
#     def validate_new_password_strength(cls, value: str) -> str:
#         is_strong_password(value)
#         return value

#     @model_validator(mode='after')
#     def check_passwords_match_and_different(cls, data: 'PasswordChangeSchema') -> 'PasswordChangeSchema':
#         if data.new_password != data.confirm_new_password:
#             raise ValueError("Новий пароль та його підтвердження не співпадають.")
#         if data.new_password == data.current_password:
#             raise ValueError("Новий пароль не може бути таким же, як поточний.")
#         return data

# PasswordResetRequestSchema.model_rebuild() # Закоментовано
# PasswordResetConfirmSchema.model_rebuild() # Закоментовано
