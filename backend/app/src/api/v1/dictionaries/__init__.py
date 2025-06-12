# backend/app/src/api/v1/dictionaries/__init__.py
# -*- coding: utf-8 -*-
"""
Агрегований роутер для всіх ендпоінтів, пов'язаних з довідниками системи.

Цей модуль імпортує окремі роутери для кожного типу довідника
(наприклад, статуси, ролі користувачів, типи груп тощо) та об'єднує їх
в один загальний `dictionaries_router`. Кожен під-роутер має свій префікс.
"""
from fastapi import APIRouter

# Повні шляхи імпорту (відносно поточного пакету)
from . import statuses
from . import user_roles
from . import user_types
from . import group_types
from . import task_types
from . import bonus_types
from . import calendars
from . import messengers

from backend.app.src.config.logging import logger # Централізований логер

# Головний роутер для всіх довідників
dictionaries_router = APIRouter()

# Підключення всіх роутерів довідників з відповідними префіксами та тегами
dictionaries_router.include_router(statuses.router, prefix="/statuses", tags=["Довідник - Статуси"]) # i18n tag
dictionaries_router.include_router(user_roles.router, prefix="/user-roles", tags=["Довідник - Ролі користувачів"]) # i18n tag
dictionaries_router.include_router(user_types.router, prefix="/user-types", tags=["Довідник - Типи користувачів"]) # i18n tag
dictionaries_router.include_router(group_types.router, prefix="/group-types", tags=["Довідник - Типи груп"]) # i18n tag
dictionaries_router.include_router(task_types.router, prefix="/task-types", tags=["Довідник - Типи завдань"]) # i18n tag
dictionaries_router.include_router(bonus_types.router, prefix="/bonus-types", tags=["Довідник - Типи бонусів"]) # i18n tag
dictionaries_router.include_router(calendars.router, prefix="/calendar-providers", tags=["Довідник - Постачальники календарів"]) # i18n tag
dictionaries_router.include_router(messengers.router, prefix="/messenger-platforms", tags=["Довідник - Платформи месенджерів"]) # i18n tag

__all__ = [
    "dictionaries_router", # Експортуємо головний роутер довідників
]

logger.info("Роутер для довідників (`dictionaries_router`) зібрано та готовий до підключення до API v1.")
