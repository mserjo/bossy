# backend/app/src/services/auth/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет сервісів для автентифікації та управління користувачами.

Включає:
- `UserService`: для CRUD операцій з користувачами та управління профілями.
- `AuthService`: для логіки автентифікації (логін, токени, реєстрація).
- `TokenService` (або як частина AuthService): для генерації та валідації токенів.
"""

from .user_service import UserService, user_service
from .auth_service import AuthService, auth_service
# from .token_service import TokenService, token_service # Якщо буде окремим

__all__ = [
    "UserService",
    "user_service",
    "AuthService",
    "auth_service",
    # "TokenService",
    # "token_service",
]

from backend.app.src.config.logging import logger
logger.debug("Пакет 'services.auth' ініціалізовано.")
