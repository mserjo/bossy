# backend/app/src/api/v1/teams/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету 'teams' API v1.

Цей пакет містить ендпоінти для управління командами в системі через API v1.
Команди зазвичай створюються в контексті певної групи.

Операції можуть включати:
- Створення, перегляд, редагування та видалення команд (`team.py`).
- Управління членством в команді (`membership.py`).

Шляхи до ендпоінтів команд часто є вкладеними в групи:
`/groups/{group_id}/teams/...`

Цей файл робить каталог 'teams' пакетом Python та експортує
агрегований роутер `router` для всіх ендпоінтів команд.
Цей `router` призначений для підключення в контексті конкретної групи.
"""

from fastapi import APIRouter

# TODO: Імпортувати окремі роутери з модулів цього пакету, коли вони будуть створені.
# from backend.app.src.api.v1.teams.team import router as crud_teams_router
# from backend.app.src.api.v1.teams.membership import router as team_membership_router

# Агрегуючий роутер для всіх ендпоінтів команд API v1.
router = APIRouter(tags=["v1 :: Teams"])

# TODO: Розкоментувати та підключити окремі роутери.
# Приклад структури підключення:

# Основні CRUD операції з командами (наприклад, /groups/{group_id}/teams/, /groups/{group_id}/teams/{team_id})
# router.include_router(crud_teams_router) # Шляхи визначаються всередині crud_teams_router

# Членство в команді (наприклад, /groups/{group_id}/teams/{team_id}/members)
# router.include_router(team_membership_router, prefix="/{team_id}/members")


# Експорт агрегованого роутера.
__all__ = [
    "router",
]

# TODO: Узгодити назву експортованого роутера ("router") з імпортом
# в `backend.app.src.api.v1.router.py` (очікує `teams_v1_router`) або
# в `backend.app.src.api.v1.groups.__init__.py` (якщо підключається там).
# TODO: Переконатися, що шляхи та префікси коректно обробляють `group_id` та `team_id`.
