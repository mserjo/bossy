# backend/app/src/api/v1/integrations/router.py
# -*- coding: utf-8 -*-
"""
Маршрутизатор для інтеграцій з зовнішніми сервісами API v1.
"""
from fastapi import APIRouter

from . import calendars, messengers

integrations_router = APIRouter()

# Підключення маршрутизаторів з окремих файлів
integrations_router.include_router(calendars.router, prefix="/calendars", tags=["V1 Інтеграції - Календарі"])
integrations_router.include_router(messengers.router, prefix="/messengers", tags=["V1 Інтеграції - Месенджери"])

@integrations_router.get("/ping_integrations_main", tags=["V1 Інтеграції - Health Check"])
async def ping_integrations_main():
    return {"message": "Main Integrations router is active and includes sub-routers!"}
