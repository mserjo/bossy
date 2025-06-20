# backend/app/src/api/v1/users/router.py
# -*- coding: utf-8 -*-
"""
Маршрутизатор для операцій з користувачами API v1.
(Зазвичай для адміністративних дій або перегляду профілів)
"""
from fastapi import APIRouter

users_router = APIRouter()

# Тут будуть ендпоінти для CRUD операцій над користувачами (якщо доступно),
# отримання списків користувачів, перегляд профілів тощо.

@users_router.get("/ping", tags=["V1 Користувачі"])
async def ping_users():
    return {"message": "Users router is active!"}
