# backend/app/src/api/v1/auth/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету ендпоінтів автентифікації та профілю API v1.

Цей пакет містить роутери, пов'язані з:
- Автентифікацією користувачів (логін, логаут, оновлення токенів).
- Реєстрацією нових користувачів.
- Управлінням профілем поточного користувача (перегляд, оновлення, зміна паролю).
- Відновленням паролю (буде додано пізніше, якщо потрібно).

Кожен модуль (наприклад, `login.py`, `register.py`, `profile.py`) визначає свій `APIRouter`,
які агрегуються тут для подальшого підключення до головного роутера API v1.
"""

from fastapi import APIRouter

from backend.app.src.api.v1.auth.login import router as login_router
from backend.app.src.api.v1.auth.register import router as register_router
from backend.app.src.api.v1.auth.profile import router as profile_router
# TODO: Імпортувати роутери для password.py (відновлення паролю) та token.py (якщо будуть окремі ендпоінти),
# коли вони будуть створені.

# Агрегуючий роутер для всіх ендпоінтів автентифікації та профілю
auth_router = APIRouter()

auth_router.include_router(login_router, tags=["Auth & Profile"]) # Теги вже є в login_router
auth_router.include_router(register_router, tags=["Auth & Profile"]) # Теги вже є в register_router
auth_router.include_router(profile_router, prefix="/users", tags=["Auth & Profile"]) # Додаємо префікс /users для /me

# TODO: Додати інші роутери з цього пакету, коли вони будуть готові:
# auth_router.include_router(password_router, prefix="/password", tags=["Auth & Profile"])
# auth_router.include_router(token_router, prefix="/token", tags=["Auth & Profile"])


__all__ = (
    "auth_router",
)
