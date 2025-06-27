# backend/app/src/api/v1/teams/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету ендпоінтів управління командами API v1.

Цей пакет містить роутери для:
- Основного управління командами (CRUD операції з командами).
- Управління членством у командах.
"""

from fastapi import APIRouter

from backend.app.src.api.v1.teams.teams import router as main_teams_router
from backend.app.src.api.v1.teams.members import router as team_members_router

# Агрегуючий роутер для всіх ендпоінтів, пов'язаних з командами.
# Цей роутер буде підключатися до головного роутера API v1 з префіксом,
# що включає group_id, наприклад, /groups/{group_id}/teams
teams_router = APIRouter()

# Основні операції з командами
teams_router.include_router(main_teams_router) # Без додаткового префіксу тут

# Вкладений роутер для управління учасниками команди (під /groups/{group_id}/teams/{team_id}/members)
team_specific_router = APIRouter()
team_specific_router.include_router(team_members_router, prefix="/{team_id}/members", tags=["Teams"])

teams_router.include_router(team_specific_router)

__all__ = (
    "teams_router",
)
