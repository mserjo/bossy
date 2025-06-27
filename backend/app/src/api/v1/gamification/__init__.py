# backend/app/src/api/v1/gamification/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету ендпоінтів гейміфікації API v1.

Цей пакет містить роутери для управління елементами гейміфікації:
- Рівні (`levels.py`): налаштування рівнів та перегляд рівня користувача.
- Бейджі (`badges.py`): CRUD операції з бейджами.
- Досягнення (`achievements.py`): перегляд зароблених користувачами бейджів.
- Рейтинги (`ratings.py`): перегляд рейтингів користувачів.

Ендпоінти зазвичай прив'язані до конкретної групи: `/groups/{group_id}/gamification/...`
"""

from fastapi import APIRouter

from backend.app.src.api.v1.gamification.levels import router as levels_router
from backend.app.src.api.v1.gamification.badges import router as badges_router
from backend.app.src.api.v1.gamification.achievements import router as achievements_router
from backend.app.src.api.v1.gamification.ratings import router as ratings_router

# Агрегуючий роутер для всіх ендпоінтів гейміфікації.
gamification_router = APIRouter()

gamification_router.include_router(levels_router, prefix="/levels", tags=["Gamification"])
gamification_router.include_router(badges_router, prefix="/badges", tags=["Gamification"])
gamification_router.include_router(achievements_router, prefix="/achievements", tags=["Gamification"])
gamification_router.include_router(ratings_router, prefix="/ratings", tags=["Gamification"])

__all__ = (
    "gamification_router",
)
