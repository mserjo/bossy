# backend/app/src/api/admin/admin_router.py
# -*- coding: utf-8 -*-
"""
Маршрутизатор для адміністративних функцій API.
"""
from fastapi import APIRouter

admin_router = APIRouter()

# Тут будуть ендпоінти для адміністрування системи,
# доступні, наприклад, тільки суперюзерам.

@admin_router.get("/ping", tags=["Admin"])
async def ping_admin():
    return {"message": "Admin router is active!"}
