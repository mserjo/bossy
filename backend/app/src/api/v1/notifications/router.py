# backend/app/src/api/v1/notifications/router.py
# -*- coding: utf-8 -*-
"""
Маршрутизатор для сповіщень API v1.
"""
from fastapi import APIRouter

from . import delivery, notifications, templates

notifications_router = APIRouter()

# Підключення маршрутизаторів з окремих файлів
notifications_router.include_router(notifications.router, prefix="/user", tags=["V1 Сповіщення - Користувацькі"]) # Assuming 'notifications.py' handles user-facing notifications
notifications_router.include_router(templates.router, prefix="/templates", tags=["V1 Сповіщення - Шаблони"])
notifications_router.include_router(delivery.router, prefix="/delivery-status", tags=["V1 Сповіщення - Статус доставки"])

@notifications_router.get("/ping_notifications_main", tags=["V1 Сповіщення - Health Check"])
async def ping_notifications_main():
    return {"message": "Main Notifications router is active and includes sub-routers!"}
