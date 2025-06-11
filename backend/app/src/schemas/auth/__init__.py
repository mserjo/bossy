# backend/app/src/schemas/auth/__init__.py
"""
Pydantic схеми для автентифікації та управління користувачами.

Цей пакет містить схеми Pydantic, що використовуються для валідації
даних запитів та формування відповідей API, пов'язаних з користувачами,
їх автентифікацією, токенами, сесіями та процесами відновлення паролю.
"""

# Схеми, пов'язані з користувачем
from .user import (
    UserBaseSchema,
    UserCreateSchema,
    UserUpdateSchema,
    UserSchema,
    UserPublicProfileSchema
)

# Схеми, пов'язані з токенами
from .token import (
    TokenPayload,
    TokenResponse,
    RefreshTokenRequest
)

# Схеми, пов'язані з процесом входу та відновлення паролю
from .login import (
    LoginRequest,
    PasswordResetRequestSchema,
    PasswordResetConfirmSchema
)

# Схеми, пов'язані з сесіями користувачів
from .session import SessionSchema

__all__ = [
    # User schemas
    "UserBaseSchema",
    "UserCreateSchema",
    "UserUpdateSchema",
    "UserSchema",
    "UserPublicProfileSchema",
    # Token schemas
    "TokenPayload",
    "TokenResponse",
    "RefreshTokenRequest",
    # Login/Password Reset schemas
    "LoginRequest",
    "PasswordResetRequestSchema",
    "PasswordResetConfirmSchema",
    # Session schemas
    "SessionSchema",
]
