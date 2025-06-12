# backend/app/src/api/v1/groups/__init__.py
# -*- coding: utf-8 -*-
"""
Агрегований роутер для всіх ендпоінтів, пов'язаних з управлінням групами.

Цей модуль імпортує та об'єднує окремі роутери для CRUD операцій над групами,
налаштувань груп, управління членством, запрошеннями та звітами.
Загальний префікс для всіх цих шляхів (наприклад, `/groups`) буде встановлено
при підключенні `groups_router` до роутера версії API (`v1_router`).
"""
from fastapi import APIRouter

# Повні шляхи імпорту (відносно поточного пакету)
from .groups import router as crud_groups_router
from .settings import router as group_settings_router
from .membership import router as group_membership_router
from .invitation import router as group_invitation_router
from .reports import router as group_reports_router

from backend.app.src.config.logging import logger # Централізований логер

# Створюємо агрегований роутер для всіх ендпоінтів, пов'язаних з групами
groups_router = APIRouter()

# Підключення роутера для CRUD операцій з групами (наприклад, /groups/, /groups/{group_id})
groups_router.include_router(crud_groups_router, tags=["Групи - Основні операції"]) # i18n tag

# Підключення роутера для налаштувань групи (наприклад, /groups/{group_id}/settings)
groups_router.include_router(group_settings_router, tags=["Групи - Налаштування"]) # i18n tag

# Підключення роутера для членства в групі (наприклад, /groups/{group_id}/members)
groups_router.include_router(group_membership_router, tags=["Групи - Членство"]) # i18n tag

# Підключення роутера для запрошень до групи
# Маршрути в group_invitation_router (наприклад, /{group_id}/invitations та /accept/{invitation_code})
# будуть доступні відносно префікса, з яким groups_router підключено до v1_router.
# Наприклад, /groups/{group_id}/invitations та /groups/invitations/accept/{invitation_code}
# Теги для group_invitation_router визначаються всередині самого модуля invitation.py
groups_router.include_router(group_invitation_router)

# Підключення роутера для звітів по групі
# Наприклад, /groups/{group_id}/reports/activity
groups_router.include_router(
    group_reports_router,
    prefix="/{group_id}/reports", # Додаємо group_id до шляху для ендпоінтів звітів
    tags=["Групи - Звіти"] # i18n tag
)

# Експортуємо groups_router для використання в головному v1_router
__all__ = [
    "groups_router",
]

logger.info("Роутер для груп (`groups_router`) зібрано та готовий до підключення до API v1.")
