# backend/app/src/api/v1/auth/__init__.py
from fastapi import APIRouter

from .login import router as login_router
from .register import router as register_router
from .token import router as token_router
from .password import router as password_router
from .profile import router as profile_router

auth_router = APIRouter()

# Endpoints from login.py (e.g., /login, /refresh, /logout) will be directly under /auth
auth_router.include_router(login_router)
# Endpoint from register.py (e.g., /register) will be directly under /auth
auth_router.include_router(register_router)
# Endpoints from token.py (e.g., /verify) will be under /auth/token
auth_router.include_router(token_router, prefix="/token")
# Endpoints from password.py (e.g., /change, /forgot, /reset) will be under /auth/password
auth_router.include_router(password_router, prefix="/password")
# Endpoints from profile.py (e.g., /me) will be under /auth/profile
auth_router.include_router(profile_router, prefix="/profile")

# The main inclusion in v1/router.py will use tags=["V1 Authentication"]
# Individual routers (login.py, etc.) should ideally have their own specific tags.
# For example, in login.py: router = APIRouter(tags=["Session Management"])
# This way, an endpoint like /auth/login would get tags from both levels if FastAPI supports that,
# or primarily the tags from the v1_router.include_router call.
# FastAPI typically combines tags from `APIRouter(tags=...)` and `app.include_router(..., tags=...)`.

__all__ = ["auth_router"]
