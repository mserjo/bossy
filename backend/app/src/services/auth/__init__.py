# backend/app/src/services/auth/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет сервісів для автентифікації та управління користувачами.

Включає:
- `UserService`: для CRUD операцій з користувачами та управління профілями.
- `AuthService`: для логіки автентифікації (логін, токени, реєстрація).
- `TokenService` (або як частина AuthService): для генерації та валідації токенів.
"""

from .user_service import UserService  # Імпортуємо тільки клас UserService
from .auth_service import AuthService  # Імпортуємо тільки клас AuthService
# from .token_service import TokenService, token_service # Якщо буде окремим

__all__ = [
    "UserService",  # Експортуємо тільки клас UserService
    "AuthService",  # Експортуємо тільки клас AuthService
    # "auth_service", # Видаляємо екземпляр
    # "TokenService",
    # "token_service",
]

from backend.app.src.config.logging import logger
logger.debug("Пакет 'services.auth' ініціалізовано.")
