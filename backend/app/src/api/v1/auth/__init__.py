# backend/app/src/api/v1/auth/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету 'auth' API v1.

Цей пакет містить ендпоінти, пов'язані з автентифікацією, реєстрацією
та управлінням профілем користувача для API v1. Сюди входять:
- Логін (`login.py`) та отримання/оновлення токенів (`token.py`).
- Реєстрація нового користувача (`register.py`).
- Вихід з системи (логаут).
- Запит на скидання паролю та його зміна (`password.py`).
- Перегляд та оновлення профілю поточного користувача (`profile.py`).

Цей файл робить каталог 'auth' пакетом Python. Він також агрегує
окремі роутери з модулів цього пакету в єдиний `router`,
який потім експортується для використання в головному роутері API v1.
"""

from fastapi import APIRouter

# TODO: Імпортувати окремі роутери з модулів цього пакету, коли вони будуть створені.
# from backend.app.src.api.v1.auth.login import router as login_router
# from backend.app.src.api.v1.auth.register import router as register_router
# from backend.app.src.api.v1.auth.token import router as token_router
# from backend.app.src.api.v1.auth.password import router as password_router
# from backend.app.src.api.v1.auth.profile import router as profile_router

# Агрегуючий роутер для всіх ендпоінтів автентифікації та профілю API v1.
router = APIRouter(tags=["v1 :: Auth & Profile"])

# TODO: Розкоментувати та підключити окремі роутери, коли вони будуть готові.
# Кожен підключений роутер може мати свій префікс відносно `/auth` (якщо `/auth`
# буде префіксом для `auth_v1_router` в `v1/router.py`).
# Наприклад, якщо `auth_v1_router` підключається з префіксом `/auth`:
# router.include_router(login_router) # Ендпоінти логіну будуть доступні за /auth/login (якщо в login_router є префікс /login) або /auth/
# router.include_router(register_router, prefix="/register") # /auth/register
# router.include_router(token_router, prefix="/token")       # /auth/token (для refresh, revoke)
# router.include_router(password_router, prefix="/password") # /auth/password (для forgot, reset, change)
# router.include_router(profile_router, prefix="/me")        # /auth/me (для CRUD операцій з профілем поточного користувача)

# Експорт агрегованого роутера.
__all__ = [
    "router",
]

# TODO: Узгодити назву експортованого роутера ("router") з імпортом
# в `backend.app.src.api.v1.router.py` (там очікується `auth_v1_router`).
# Рекомендується перейменувати змінну тут на `auth_v1_router` або
# використовувати `from .auth import router as auth_v1_router` при імпорті.
# Поки що залишаю "router".
