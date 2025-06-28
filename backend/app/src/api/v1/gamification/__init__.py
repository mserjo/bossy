# backend/app/src/api/v1/gamification/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету 'gamification' API v1.

Цей пакет містить ендпоінти для управління елементами гейміфікації
в системі через API v1. Сюди можуть входити:
- Управління рівнями (`levels.py`).
- Управління бейджами (`badges.py`).
- Відображення досягнень користувачів (`achievements.py`).
- Відображення рейтингів (`ratings.py`).

Елементи гейміфікації часто діють в контексті групи, тому цей роутер
ймовірно буде підключений з префіксом `/groups/{group_id}/gamification`.
"""

from fastapi import APIRouter

# TODO: Імпортувати окремі роутери з модулів цього пакету, коли вони будуть створені.
# from backend.app.src.api.v1.gamification.levels import router as levels_router
# from backend.app.src.api.v1.gamification.badges import router as badges_router
# from backend.app.src.api.v1.gamification.achievements import router as achievements_router
# from backend.app.src.api.v1.gamification.ratings import router as ratings_router

# Агрегуючий роутер для всіх ендпоінтів гейміфікації API v1.
router = APIRouter(tags=["v1 :: Gamification"])

# TODO: Розкоментувати та підключити окремі роутери.
# Префікси тут будуть відносні до шляху, з яким цей `router` підключається
# (наприклад, `/groups/{group_id}/gamification`).

# router.include_router(levels_router, prefix="/levels")
# router.include_router(badges_router, prefix="/badges")
# router.include_router(achievements_router, prefix="/achievements") # Або /users/{user_id}/achievements
# router.include_router(ratings_router, prefix="/ratings")


# Експорт агрегованого роутера.
__all__ = [
    "router",
]

# TODO: Узгодити назву експортованого роутера ("router") з імпортом
# в `backend.app.src.api.v1.router.py` (очікує `gamification_v1_router`).
