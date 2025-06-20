# backend/app/src/schemas/auth/__init__.py
# -*- coding: utf-8 -*-
"""Pydantic схеми для автентифікації та управління користувачами.

Цей пакет містить схеми Pydantic, що використовуються для валідації
даних запитів та формування відповідей API, пов'язаних з користувачами,
їхньою автентифікацією, токенами (доступу та оновлення), сесіями,
процесами входу, реєстрації та відновлення паролю.

Основні категорії схем:
- Схеми для даних користувача (`user.py`): `UserBaseSchema`, `UserCreateSchema`, `UserUpdateSchema`, `UserResponseSchema`.
- Схеми для токенів (`token.py`): `TokenResponseSchema`, `RefreshTokenRequestSchema`, `TokenDataSchema`.
- Схеми для процесу входу (`login.py`): `LoginRequestSchema`, `PasswordResetRequestSchema`, `PasswordResetConfirmSchema`, `TwoFactorAuthRequestSchema`.
- Схеми для сесій (`session.py`): `UserSessionSchema`.
"""

# Імпорт централізованого логера
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Схеми, пов'язані з користувачем
# Припускаємо, що класи в user.py будуть перейменовані/визначені як *Schema
from backend.app.src.schemas.auth.user import (
    UserBaseSchema,
    UserCreateSchema,
    UserUpdateSchema,
    UserResponseSchema, # Очікувана назва для відповіді з даними користувача
    UserPublicProfileSchema
)

# Схеми, пов'язані з токенами
from backend.app.src.schemas.auth.token import (
    TokenPayload,    # Схема для даних всередині токена (раніше TokenDataSchema)
    TokenResponse,  # Схема для відповіді з токенами
    RefreshTokenRequestSchema,
    RefreshTokenCreateSchema
)

# Схеми, пов'язані з процесом входу та відновлення паролю
from backend.app.src.schemas.auth.login import (
    LoginRequestSchema,
    PasswordResetRequestSchema,
    PasswordResetConfirmSchema
    # TwoFactorAuthRequestSchema # Видалено, оскільки схема не визначена в login.py
)

# Схеми, пов'язані з сесіями користувачів
from backend.app.src.schemas.auth.session import UserSessionResponse, UserSessionCreate

# Визначаємо, які символи будуть експортовані при використанні `from backend.app.src.schemas.auth import *`.
__all__ = [
    # User schemas
    "UserBaseSchema",
    "UserCreateSchema",
    "UserUpdateSchema",
    "UserResponseSchema",
    "UserPublicProfileSchema",
    # Token schemas
    "TokenPayload",
    "TokenResponse",
    "RefreshTokenRequestSchema",
    "RefreshTokenCreateSchema",
    # Login/Password Reset schemas
    "LoginRequestSchema",
    "PasswordResetRequestSchema",
    "PasswordResetConfirmSchema",
    # "TwoFactorAuthRequestSchema",
    # Session schemas
    "UserSessionResponse",
    "UserSessionCreate",
]

logger.debug("Ініціалізація пакету схем Pydantic `auth`...")
