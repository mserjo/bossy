# backend/app/src/api/v1/notifications/router.py
# -*- coding: utf-8 -*-
"""
Маршрутизатор для сповіщень API v1.
"""
from fastapi import APIRouter

notifications_router = APIRouter()

# Тут будуть ендпоінти для перегляду сповіщень,
# налаштування переваг сповіщень, відправки (якщо потрібно) тощо.

@notifications_router.get("/ping", tags=["V1 Сповіщення"])
async def ping_notifications():
    return {"message": "Notifications router is active!"}
