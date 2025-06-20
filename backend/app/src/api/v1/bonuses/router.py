# backend/app/src/api/v1/bonuses/router.py
# -*- coding: utf-8 -*-
"""
Маршрутизатор для бонусів, рахунків та винагород API v1.
"""
from fastapi import APIRouter

bonuses_router = APIRouter()

# Тут будуть ендпоінти для управління правилами нарахування бонусів,
# перегляду рахунків користувачів, отримання винагород тощо.

@bonuses_router.get("/ping", tags=["V1 Бонуси та Винагороди"])
async def ping_bonuses():
    return {"message": "Bonuses router is active!"}
