# backend/app/src/api/v1/auth/__init__.py
from fastapi import APIRouter

from .login import router as login_router
from .register import router as register_router
from .token import router as token_router
from .password import router as password_router
from .profile import router as profile_router

auth_router = APIRouter()

# Ендпоінти з login.py (наприклад, /login, /refresh, /logout) будуть безпосередньо під /auth
auth_router.include_router(login_router)
# Ендпоінт з register.py (наприклад, /register) буде безпосередньо під /auth
auth_router.include_router(register_router)
# Ендпоінти з token.py (наприклад, /verify) будуть під /auth/token
auth_router.include_router(token_router, prefix="/token")
# Ендпоінти з password.py (наприклад, /change, /forgot, /reset) будуть під /auth/password
auth_router.include_router(password_router, prefix="/password")
# Ендпоінти з profile.py (наприклад, /me) будуть під /auth/profile
auth_router.include_router(profile_router, prefix="/profile")

# Основне включення в v1/router.py буде використовувати tags=["V1 Authentication"]
# Окремі роутери (login.py, тощо) в ідеалі повинні мати свої специфічні теги.
# Наприклад, у login.py: router = APIRouter(tags=["Управління сесіями"])
# Таким чином, ендпоінт на кшталт /auth/login отримає теги з обох рівнів, якщо FastAPI це підтримує,
# або переважно теги з виклику v1_router.include_router.
# FastAPI зазвичай комбінує теги з APIRouter(tags=...) та app.include_router(..., tags=...).

__all__ = ["auth_router"]
