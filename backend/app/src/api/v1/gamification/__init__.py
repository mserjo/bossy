# backend/app/src/api/v1/gamification/__init__.py
# -*- coding: utf-8 -*-
# TODO: Файл 'user_level.py' та відповідний 'user_level_router' для управління рівнями користувачів наразі відсутні.
# Необхідно створити цей модуль або видалити посилання на нього, якщо функціонал не планується.
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

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from fastapi import APIRouter

# Оновлені повні шляхи імпорту для під-роутерів
from backend.app.src.api.v1.gamification.levels import router as levels_router
# from backend.app.src.api.v1.gamification.user_level import router as user_level_router # TODO: Файл user_level.py відсутній або ще не створений
from backend.app.src.api.v1.gamification.badges import router as badges_router
from backend.app.src.api.v1.gamification.achievements import router as achievements_router
from backend.app.src.api.v1.gamification.ratings import router as ratings_router

from backend.app.src.config.logging import logger # Централізований логер

# Створюємо агрегований роутер для всіх ендпоінтів, пов'язаних з гейміфікацією
gamification_router = APIRouter()

# Підключення роутера для визначень рівнів
gamification_router.include_router(levels_router, prefix="/levels", tags=["Гейміфікація - Визначення Рівнів"])

# Підключення роутера для рівнів користувачів
# gamification_router.include_router(user_level_router, prefix="/user-levels", tags=["Гейміфікація - Рівні Користувачів"]) # TODO: Відновити, коли user_level.py буде додано

# Підключення роутера для визначень бейджів
gamification_router.include_router(badges_router, prefix="/badges", tags=["Гейміфікація - Визначення Бейджів"])

# Підключення роутера для досягнень користувачів (нагороджених бейджів)
gamification_router.include_router(achievements_router, prefix="/achievements", tags=["Гейміфікація - Досягнення Користувачів"])

# Підключення роутера для рейтингів
gamification_router.include_router(ratings_router, prefix="/ratings", tags=["Гейміфікація - Рейтинги та Лідерборди"])


# Експортуємо gamification_router для використання в головному v1_router
__all__ = [
    "gamification_router",
]

logger.info("Роутер для гейміфікації (`gamification_router`) зібрано та готовий до підключення до API v1.")
