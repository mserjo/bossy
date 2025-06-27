# backend/app/src/api/v1/router.py
# -*- coding: utf-8 -*-
"""
Головний роутер для API версії 1 (v1).

Цей файл відповідає за створення екземпляру `APIRouter` для версії v1 API
та підключення до нього всіх роутерів, що відповідають за окремі
групи ендпоінтів (наприклад, автентифікація, користувачі, групи, завдання тощо).

Цей `router` потім імпортується та підключається до головного API роутера
(в `backend.app.src.api.router.py`) з префіксом `/v1`.
"""

from fastapi import APIRouter

# Імпортуємо агреговані роутери для модулів
from backend.app.src.api.v1.system import system_router
from backend.app.src.api.v1.auth import auth_router
from backend.app.src.api.v1.dictionaries import dictionaries_router
from backend.app.src.api.v1.users import users_router # Адміністративне управління користувачами
from backend.app.src.api.v1.groups import groups_router # Управління групами
from backend.app.src.api.v1.tasks import tasks_router # Управління завданнями
from backend.app.src.api.v1.teams import teams_router # Управління командами
from backend.app.src.api.v1.bonuses import bonuses_router # Управління бонусами
from backend.app.src.api.v1.gamification import gamification_router # Управління гейміфікацією
from backend.app.src.api.v1.notifications import notifications_router # Управління сповіщеннями
from backend.app.src.api.v1.files import files_router # Управління файлами
from backend.app.src.api.v1.integrations import integrations_router # Управління інтеграціями
from backend.app.src.api.v1.reports import reports_router # Звіти

# TODO: Імпортувати роутери для окремих сутностей API v1, коли вони будуть створені.
# Приклади:
# from backend.app.src.api.v1.dictionaries import statuses_router, user_roles_router
# ... і так далі для всіх підкаталогів, визначених у structure-claude-v3.md

# Роутер для API версії 1
router = APIRouter()

# Підключення системного роутера
router.include_router(system_router, prefix="/system", tags=["System API v1"])

# Підключення роутера автентифікації та профілю
router.include_router(auth_router, prefix="/auth", tags=["Auth & Profile API v1"])

# Підключення роутера довідників
router.include_router(dictionaries_router, prefix="/dictionaries", tags=["Dictionaries API v1"])

# Підключення роутера для адміністративного управління користувачами
router.include_router(users_router, prefix="/users", tags=["Users (Admin) API v1"])

# Підключення роутера для управління групами
router.include_router(groups_router, prefix="/groups", tags=["Groups API v1"])

# Підключення роутера для управління завданнями (в контексті групи)
# Шляхи в tasks_router будуть відносні до цього префіксу,
# наприклад, /groups/{group_id}/tasks/ або /groups/{group_id}/tasks/{task_id}/assignments
router.include_router(tasks_router, prefix="/groups/{group_id}/tasks", tags=["Tasks API v1"])

# Підключення роутера для управління командами (в контексті групи)
# Шляхи в teams_router будуть відносні до цього префіксу,
# наприклад, /groups/{group_id}/teams/ або /groups/{group_id}/teams/{team_id}/members
router.include_router(teams_router, prefix="/groups/{group_id}/teams", tags=["Teams API v1"])

# Підключення роутера для управління бонусами (в контексті групи)
# Шляхи в bonuses_router будуть відносні до цього префіксу
router.include_router(bonuses_router, prefix="/groups/{group_id}", tags=["Bonuses API v1"])

# Підключення роутера для гейміфікації (в контексті групи)
router.include_router(gamification_router, prefix="/groups/{group_id}/gamification", tags=["Gamification API v1"])

# Підключення роутера для сповіщень
router.include_router(notifications_router, prefix="/notifications", tags=["Notifications API v1"])

# Підключення роутера для файлів
router.include_router(files_router, prefix="/files", tags=["Files API v1"])

# Підключення роутера для інтеграцій
# Можливі префікси: "/integrations" або "/users/me/integrations"
router.include_router(integrations_router, prefix="/integrations", tags=["Integrations API v1"])

# Підключення роутера для звітів
router.include_router(reports_router, prefix="/reports", tags=["Reports API v1"])


# Підключення роутерів для окремих сутностей (приклад)
# Зауважте, що /auth/users/me обробляється auth_router.

# TODO: Додати підключення всіх запланованих роутерів для v1,
# як тільки вони будуть створені у відповідних підкаталогах.
# Наприклад:


# Приклад простого ендпоінту на кореневому рівні API v1 (наприклад, /api/v1/)
@router.get("/", tags=["API v1 Root"])
async def read_api_v1_root():
    """
    Кореневий ендпоінт для API версії 1.
    Надає базову інформацію про доступні ресурси v1.
    """
    return {
        "message": "Ласкаво просимо до API версії 1!",
        "documentation": "/docs",  # Відносно поточного роутера, тобто /api/v1/docs
        "redoc": "/redoc"          # Відносно поточного роутера, тобто /api/v1/redoc
        # TODO: Можна додати список основних доступних категорій ендпоінтів
    }

# Цей роутер буде імпортований в backend/app/src/api/router.py
# і підключений до головного api_router.
# from backend.app.src.api.v1.router import router as v1_router
# api_router.include_router(v1_router, prefix="/v1", tags=["API v1"])

# Також, цей роутер може бути використаний для додавання специфічних для v1
# обробників винятків або залежностей, якщо це необхідно, хоча
# глобальні обробники в backend/app/src/api/exceptions.py зазвичай кращі.
# from backend.app.src.api.exceptions import register_exception_handlers
# register_exception_handlers(router) # Якщо потрібні специфічні для v1 обробники
