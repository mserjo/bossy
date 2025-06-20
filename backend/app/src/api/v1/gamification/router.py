# backend/app/src/api/v1/gamification/router.py
# -*- coding: utf-8 -*-
"""
Маршрутизатор для функцій гейміфікації API v1.
"""
from fastapi import APIRouter

from . import achievements, badges, levels, ratings

gamification_router = APIRouter()

# Підключення маршрутизаторів з окремих файлів
gamification_router.include_router(levels.router, prefix="/levels", tags=["V1 Гейміфікація - Рівні"])
gamification_router.include_router(badges.router, prefix="/badges", tags=["V1 Гейміфікація - Бейджі"])
gamification_router.include_router(achievements.router, prefix="/achievements", tags=["V1 Гейміфікація - Досягнення"])
gamification_router.include_router(ratings.router, prefix="/ratings", tags=["V1 Гейміфікація - Рейтинги"])

@gamification_router.get("/ping_gamification_main", tags=["V1 Гейміфікація - Health Check"])
async def ping_gamification_main():
    return {"message": "Main Gamification router is active and includes sub-routers!"}
