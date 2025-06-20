# backend/app/src/api/v1/gamification/router.py
# -*- coding: utf-8 -*-
"""
Маршрутизатор для функцій гейміфікації API v1.
"""
from fastapi import APIRouter

gamification_router = APIRouter()

# Тут будуть ендпоінти для рівнів, бейджів, рейтингів,
# досягнень користувачів тощо.

@gamification_router.get("/ping", tags=["V1 Гейміфікація"])
async def ping_gamification():
    return {"message": "Gamification router is active!"}
