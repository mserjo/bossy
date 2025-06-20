# backend/app/src/api/v1/auth/router.py
# -*- coding: utf-8 -*-
"""
Маршрутизатор для функцій автентифікації API v1.
"""
from fastapi import APIRouter

auth_router = APIRouter()

# Тут будуть ендпоінти для /login, /register, /refresh-token, /password-recovery тощо.

# Приклад простого ендпоінта для перевірки
@auth_router.get("/ping", tags=["V1 Автентифікація"])
async def ping_auth():
    return {"message": "Auth router is active!"}
