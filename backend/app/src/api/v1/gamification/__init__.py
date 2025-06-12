# backend/app/src/api/v1/gamification/__init__.py
# -*- coding: utf-8 -*-
"""
Агрегований роутер для всіх ендпоінтів, пов'язаних з гейміфікацією.

Цей модуль імпортує та об'єднує окремі роутери для:
- Управління визначеннями рівнів (`levels.py`)
- Управління рівнями користувачів (`user_level.py`)
- Управління визначеннями значків (бейджів) (`badges.py`)
- Управління досягненнями користувачів (нагородженими бейджами) (`achievements.py`)
- Перегляду рейтингів та таблиць лідерів (`ratings.py`)

Загальний префікс для всіх цих шляхів (наприклад, `/gamification`) буде встановлено
при підключенні `gamification_router` до роутера версії API (`v1_router`).
"""
from fastapi import APIRouter

# Повні шляхи імпорту (відносно поточного пакету)
from .levels import router as levels_router
from .user_level import router as user_level_router # Додано роутер для рівнів користувачів
from .badges import router as badges_router
from .achievements import router as achievements_router
from .ratings import router as ratings_router

from backend.app.src.config.logging import logger # Централізований логер

# Створюємо агрегований роутер для всіх ендпоінтів, пов'язаних з гейміфікацією
gamification_router = APIRouter()

# Підключення роутера для визначень рівнів
gamification_router.include_router(levels_router, prefix="/levels", tags=["Гейміфікація - Визначення Рівнів"]) # i18n tag

# Підключення роутера для рівнів користувачів
gamification_router.include_router(user_level_router, prefix="/user-levels", tags=["Гейміфікація - Рівні Користувачів"]) # i18n tag

# Підключення роутера для визначень бейджів
gamification_router.include_router(badges_router, prefix="/badges", tags=["Гейміфікація - Визначення Бейджів"]) # i18n tag

# Підключення роутера для досягнень користувачів (нагороджених бейджів)
gamification_router.include_router(achievements_router, prefix="/achievements", tags=["Гейміфікація - Досягнення Користувачів"]) # i18n tag

# Підключення роутера для рейтингів
gamification_router.include_router(ratings_router, prefix="/ratings", tags=["Гейміфікація - Рейтинги та Лідерборди"]) # i18n tag


# Експортуємо gamification_router для використання в головному v1_router
__all__ = [
    "gamification_router",
]

logger.info("Роутер для гейміфікації (`gamification_router`) зібрано та готовий до підключення до API v1.")
