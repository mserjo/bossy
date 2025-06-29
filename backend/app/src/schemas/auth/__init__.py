# backend/app/src/schemas/auth/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету схем автентифікації та користувачів (`auth`).

Цей файл робить доступними основні схеми, пов'язані з автентифікацією та користувачами,
для імпорту з пакету `backend.app.src.schemas.auth`.

Приклад імпорту:
from backend.app.src.schemas.auth import UserSchema, UserCreateSchema, TokenResponseSchema

Також цей файл може використовуватися для визначення змінної `__all__`,
яка контролює, що саме експортується при використанні `from . import *`.
"""

# Імпорт конкретних схем автентифікації та користувачів
from backend.app.src.schemas.auth.user import (
    UserSchema,
    UserPublicSchema,
    UserCreateSchema,
    UserUpdateSchema,
    UserPasswordUpdateSchema,
    UserAdminUpdateSchema,
)
from backend.app.src.schemas.auth.token import (
    TokenResponseSchema,
    RefreshTokenSchema,
    RefreshTokenRequestSchema,
)
from backend.app.src.schemas.auth.login import (
    LoginRequestSchema,
    PasswordResetRequestSchema,
    PasswordResetConfirmSchema,
    EmailVerificationRequestSchema,
    ResendEmailVerificationSchema,
)
from backend.app.src.schemas.auth.session import (
    SessionSchema,
)

# Визначення змінної `__all__` для контролю публічного API пакету.
__all__ = [
    # User Schemas
    "UserSchema",
    "UserPublicSchema",
    "UserCreateSchema",
    "UserUpdateSchema",
    "UserPasswordUpdateSchema",
    "UserAdminUpdateSchema",

    # Token Schemas
    "TokenResponseSchema",
    "RefreshTokenSchema",
    "RefreshTokenRequestSchema",

    # Login/Password/Verification Schemas
    "LoginRequestSchema",
    "PasswordResetRequestSchema",
    "PasswordResetConfirmSchema",
    "EmailVerificationRequestSchema",
    "ResendEmailVerificationSchema",

    # Session Schemas
    "SessionSchema",
]

# TODO: Переконатися, що всі необхідні схеми з цього пакету створені та включені до `__all__`.
# На даний момент включені всі схеми, заплановані для створення в цьому пакеті.
# Це забезпечує централізований доступ до схем, пов'язаних з автентифікацією та користувачами.
#
# Важливо також пам'ятати про необхідність оновлення зв'язків у схемах
# (наприклад, `UserSchema` може містити поле `sessions: List[SessionSchema]`),
# що може вимагати використання `ForwardRef` або `model_rebuild()`
# для уникнення циклічних залежностей під час ініціалізації.
# Pydantic v2 покращив обробку `ForwardRef`, тому це має бути простіше.
# Наприклад, в `UserSchema`:
#   `sessions: Optional[List['SessionSchema']] = None`
# І в `SessionSchema`:
#   `user: Optional['UserPublicSchema'] = None`
# Потім, після визначення всіх схем, можна викликати `UserSchema.model_rebuild()` та `SessionSchema.model_rebuild()`.
# Або ж, якщо файли імпортуються в правильному порядку (менш залежні першими),
# то `ForwardRef` може не знадобитися.
# Поки що залишаю без явних `ForwardRef` та `model_rebuild` в цьому `__init__.py`,
# припускаючи, що це буде оброблено в самих файлах схем, якщо потрібно,
# або що порядок імпорту буде достатнім.
# Головне - це експорт назв схем.

# Виклик model_rebuild для схем, що містять ForwardRef
# (UserSchema може посилатися на багато інших, тому її варто оновити)
# UserSchema.model_rebuild() # Перенесено до глобального __init__.py
# RefreshTokenSchema.model_rebuild() # Перенесено до глобального __init__.py
# SessionSchema.model_rebuild() # Перенесено до глобального __init__.py
# Інші схеми в цьому пакеті (Create/Update) зазвичай не мають складних ForwardRef.
