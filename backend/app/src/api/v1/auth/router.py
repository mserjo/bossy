# backend/app/src/api/v1/auth/router.py
# -*- coding: utf-8 -*-
"""
Маршрутизатор для функцій автентифікації API v1.
"""
from fastapi import APIRouter

from . import login, password, profile, register, token

auth_router = APIRouter()

# Підключення маршрутизаторів з окремих файлів
auth_router.include_router(login.router, prefix="/login", tags=["V1 Автентифікація - Логін"])
auth_router.include_router(register.router, prefix="/register", tags=["V1 Автентифікація - Реєстрація"])
auth_router.include_router(token.router, prefix="/token", tags=["V1 Автентифікація - Токени"])
auth_router.include_router(password.router, prefix="/password", tags=["V1 Автентифікація - Пароль"])
auth_router.include_router(profile.router, prefix="/profile", tags=["V1 Автентифікація - Профіль"])


# Тестовий ендпоінт можна залишити або видалити, якщо він більше не потрібен.
# Він може бути корисним для швидкої перевірки, що сам auth_router працює.
@auth_router.get("/ping_auth_main", tags=["V1 Автентифікація - Health Check"])
async def ping_auth_main():
    return {"message": "Main Auth router is active and includes sub-routers!"}
