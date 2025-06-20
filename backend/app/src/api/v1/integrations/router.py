# backend/app/src/api/v1/integrations/router.py
# -*- coding: utf-8 -*-
"""
Маршрутизатор для інтеграцій з зовнішніми сервісами API v1.
"""
from fastapi import APIRouter

integrations_router = APIRouter()

# Тут будуть ендпоінти для налаштування інтеграцій
# (наприклад, з календарями, месенджерами).

@integrations_router.get("/ping", tags=["V1 Інтеграції"])
async def ping_integrations():
    return {"message": "Integrations router is active!"}
