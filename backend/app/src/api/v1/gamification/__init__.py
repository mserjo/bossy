# backend/app/src/api/v1/gamification/__init__.py
from fastapi import APIRouter

# Імпортуємо роутери з файлів цього модуля
from .levels import router as levels_router
from .badges import router as badges_router
from .achievements import router as achievements_router
from .ratings import router as ratings_router

# Створюємо агрегований роутер для всіх ендпоінтів, пов'язаних з гейміфікацією
gamification_router = APIRouter()

# Підключення роутера для рівнів
gamification_router.include_router(levels_router, prefix="/levels", tags=["Gamification - Levels"])

# Підключення роутера для бейджів (визначень)
gamification_router.include_router(badges_router, prefix="/badges", tags=["Gamification - Badges Definitions"])

# Підключення роутера для досягнень користувачів (нагороджених бейджів)
gamification_router.include_router(achievements_router, prefix="/achievements", tags=["Gamification - User Achievements"])

# Підключення роутера для рейтингів
gamification_router.include_router(ratings_router, prefix="/ratings", tags=["Gamification - Ratings & Leaderboards"])


# Експортуємо gamification_router для використання в головному v1_router (app/src/api/v1/router.py)
__all__ = ["gamification_router"]
