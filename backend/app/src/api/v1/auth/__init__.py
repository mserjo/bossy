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

from backend.app.src.api.v1.auth.login import router as login_router
from backend.app.src.api.v1.auth.register import router as register_router
# from backend.app.src.api.v1.auth.token import router as token_router # token.py поки не використовується активно
from backend.app.src.api.v1.auth.password import router as password_router
from backend.app.src.api.v1.auth.profile import router as profile_router

# Агрегуючий роутер для всіх ендпоінтів автентифікації та профілю API v1.
# Тег "Auth" вже встановлено в кожному під-роутері, тому тут можна не дублювати
# або встановити більш загальний тег для всієї групи /auth.
# Я залишу тег, визначений в v1/router.py при підключенні auth_v1_router.
auth_v1_router = APIRouter()

# Підключення окремих роутерів.
# Префікси тут не потрібні, якщо вони вже визначені в v1/router.py для auth_v1_router (наприклад, /auth)
# або якщо ендпоінти в під-роутерах мають унікальні шляхи.
# Для кращої організації, шляхи в під-роутерах визначені відносно їх "кореня".
# Наприклад, login_router має /login, /refresh-token, /logout.
# register_router має /register.
# profile_router має /me, /me/change-password.
# password_router має /forgot-password, /reset-password.
auth_v1_router.include_router(login_router)
auth_v1_router.include_router(register_router)
auth_v1_router.include_router(profile_router)
auth_v1_router.include_router(password_router)
# auth_v1_router.include_router(token_router) # Поки не активний

# Експорт агрегованого роутера.
__all__ = [
    "auth_v1_router",
]
