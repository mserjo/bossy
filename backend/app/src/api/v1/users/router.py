# backend/app/src/api/v1/users/router.py
# -*- coding: utf-8 -*-
"""
Маршрутизатор для операцій з користувачами API v1.
(Зазвичай для адміністративних дій або перегляду профілів)
"""
from fastapi import APIRouter

from . import users # Assuming users.py contains a router instance for user management

users_router = APIRouter()

# Підключення маршрутизатора з users.py
# Оскільки це основний файл для користувачів, можливо, він не потребує додаткового префіксу тут,
# або префікс буде "/users" вже на рівні v1_router.
# Якщо users.py визначає шляхи типу "/{user_id}", то префікс не потрібен.
# Якщо шляхи в users.py типу "/", "/all", то префікс тут теж не потрібен.
users_router.include_router(users.router, tags=["V1 Користувачі - Управління"])


@users_router.get("/ping_users_main", tags=["V1 Користувачі - Health Check"])
async def ping_users_main():
    return {"message": "Main Users router is active and includes sub-routers!"}
