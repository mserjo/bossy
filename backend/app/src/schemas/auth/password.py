# backend/app/src/schemas/auth/password.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми, пов'язані з управлінням паролями,
такі як запит на скидання пароля та підтвердження скидання пароля.
"""

from pydantic import Field, EmailStr

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

    @Field.validator('new_password')
    @classmethod
    def validate_new_password_strength(cls, value: str) -> str:
        is_strong_password(value) # Валідатор кине ValueError, якщо пароль не надійний
        return value

    @Field.validator('confirm_new_password')
    @classmethod
    def passwords_match(cls, value: str, values: dict) -> str:
        if 'new_password' in values.data and value != values.data['new_password']:
            raise ValueError('Новий пароль та його підтвердження не співпадають.')
        return value

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

PasswordResetRequestSchema.model_rebuild()
PasswordResetConfirmSchema.model_rebuild()
