# backend/app/src/api/v1/dictionaries/__init__.py
# -*- coding: utf-8 -*-
"""
Агрегований роутер для всіх ендпоінтів, пов'язаних з довідниками системи.

Цей модуль імпортує окремі роутери для кожного типу довідника
(наприклад, статуси, ролі користувачів, типи груп тощо) та об'єднує їх
в один загальний `dictionaries_router`. Кожен під-роутер має свій префікс.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from fastapi import APIRouter

# Оновлені повні шляхи імпорту для під-роутерів
from backend.app.src.api.v1.dictionaries.statuses import router as statuses_router
from backend.app.src.api.v1.dictionaries.user_roles import router as user_roles_router
from backend.app.src.api.v1.dictionaries.user_types import router as user_types_router
from backend.app.src.api.v1.dictionaries.group_types import router as group_types_router
from backend.app.src.api.v1.dictionaries.task_types import router as task_types_router
from backend.app.src.api.v1.dictionaries.bonus_types import router as bonus_types_router
from backend.app.src.api.v1.dictionaries.calendars import router as calendars_router
from backend.app.src.api.v1.dictionaries.messengers import router as messengers_router

from backend.app.src.config.logging import logger # Централізований логер

# Головний роутер для всіх довідників
dictionaries_router = APIRouter()

# Підключення всіх роутерів довідників з відповідними префіксами та тегами
dictionaries_router.include_router(statuses_router, prefix="/statuses", tags=["Довідник - Статуси"])
dictionaries_router.include_router(user_roles_router, prefix="/user-roles", tags=["Довідник - Ролі користувачів"])
dictionaries_router.include_router(user_types_router, prefix="/user-types", tags=["Довідник - Типи користувачів"])
dictionaries_router.include_router(group_types_router, prefix="/group-types", tags=["Довідник - Типи груп"])
dictionaries_router.include_router(task_types_router, prefix="/task-types", tags=["Довідник - Типи завдань"])
dictionaries_router.include_router(bonus_types_router, prefix="/bonus-types", tags=["Довідник - Типи бонусів"])
dictionaries_router.include_router(calendars_router, prefix="/calendar-providers", tags=["Довідник - Постачальники календарів"])
dictionaries_router.include_router(messengers_router, prefix="/messenger-platforms", tags=["Довідник - Платформи месенджерів"])

__all__ = [
    "dictionaries_router", # Експортуємо головний роутер довідників
]

logger.info("Роутер для довідників (`dictionaries_router`) зібрано та готовий до підключення до API v1.")
