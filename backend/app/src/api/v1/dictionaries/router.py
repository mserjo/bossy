# backend/app/src/api/v1/dictionaries/router.py
# -*- coding: utf-8 -*-
"""
Маршрутизатор для довідників API v1.
"""
from fastapi import APIRouter

dictionaries_router = APIRouter()

# Тут будуть ендпоінти для доступу до різних довідників системи
# (наприклад, статуси, типи завдань, ролі користувачів).

@dictionaries_router.get("/ping", tags=["V1 Довідники"])
async def ping_dictionaries():
    return {"message": "Dictionaries router is active!"}
