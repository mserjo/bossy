# backend/app/src/api/v1/auth/__init__.py
# -*- coding: utf-8 -*-
"""
Агрегований роутер для всіх ендпоінтів, пов'язаних з автентифікацією та профілем користувача.

Цей модуль імпортує окремі роутери для логіну, реєстрації, управління токенами,
паролями та профілем користувача, та об'єднує їх в один `auth_router`.
Префікси для під-роутерів (наприклад, `/token`, `/password`, `/profile`) встановлюються тут.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from fastapi import APIRouter

from backend.app.src.api.v1.auth.login import router as login_router
from backend.app.src.api.v1.auth.register import router as register_router
from backend.app.src.api.v1.auth.token import router as token_router
from backend.app.src.api.v1.auth.password import router as password_router
from backend.app.src.api.v1.auth.profile import router as profile_router
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

auth_router = APIRouter()

# Ендпоінти з login.py (наприклад, /login, /refresh_token, /logout) будуть безпосередньо під префіксом auth_router (наприклад, /api/v1/auth)
auth_router.include_router(login_router, tags=["Автентифікація та Сесії"]) # i18n tag

# Ендпоінт з register.py (наприклад, /register) буде безпосередньо під префіксом auth_router
auth_router.include_router(register_router, tags=["Реєстрація"]) # i18n tag

# Ендпоінти з token.py (наприклад, /verify-email-token) будуть під /auth/token
auth_router.include_router(token_router, prefix="/token", tags=["Управління Токенами"]) # i18n tag

# Ендпоінти з password.py (наприклад, /change, /forgot, /reset) будуть під /auth/password
auth_router.include_router(password_router, prefix="/password", tags=["Управління Паролями"]) # i18n tag

# Ендпоінти з profile.py (наприклад, /me, /users/{user_id}) будуть під /auth/profile або /users (залежно від структури)
# Якщо /profile/me, то префікс тут. Якщо /users/me, то це може бути в іншому роутері.
# Поки що, згідно з файлом profile.py, припускаємо /auth/profile.
auth_router.include_router(profile_router, prefix="/profile", tags=["Профіль Користувача"]) # i18n tag


# Коментар щодо тегів:
# Головний v1_router, який включатиме цей auth_router, може додати загальний тег, наприклад, "Автентифікація v1".
# Окремі роутери (login.py, тощо) в ідеалі повинні мати свої специфічні теги, як показано вище.
# FastAPI зазвичай комбінує теги з APIRouter(tags=...) та app.include_router(..., tags=...).

__all__ = [
    "auth_router",
]

logger.info("Роутер для автентифікації (`auth_router`) зібрано та готовий до підключення до API v1.")
