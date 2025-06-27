# backend/app/src/api/v1/groups/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету ендпоінтів управління групами API v1.

Цей пакет містить роутери для операцій, пов'язаних з групами:
- Основне управління групами (CRUD).
- Налаштування групи.
- Членство в групі.
- Запрошення до групи.
- Шаблони груп.
- Опитування/голосування.
- Звіти по групі.
"""

from fastapi import APIRouter

from backend.app.src.api.v1.groups.groups import router as main_groups_router
from backend.app.src.api.v1.groups.settings import router as group_settings_router
from backend.app.src.api.v1.groups.membership import router as group_membership_router
from backend.app.src.api.v1.groups.invitation import router as group_invitation_router
from backend.app.src.api.v1.groups.templates import router as group_templates_router
from backend.app.src.api.v1.groups.polls import router as group_polls_router
from backend.app.src.api.v1.groups.reports import router as group_reports_router

# Агрегуючий роутер для всіх ендпоінтів, пов'язаних з групами
groups_router = APIRouter()

# Основні операції з групами (створення, список, деталі, оновлення, видалення)
# Ці ендпоінти будуть доступні за префіксом, визначеним для groups_router (наприклад, /api/v1/groups)
groups_router.include_router(main_groups_router, tags=["Groups"]) # Теги вже є в main_groups_router

# Специфічні операції, що стосуються конкретної групи,
# зазвичай мають префікс /{group_id}/ у своїх шляхах.
# Тому тут для них не додаємо префікс.
groups_router.include_router(group_settings_router, tags=["Groups"]) # Теги вже є в settings.py
groups_router.include_router(group_membership_router, tags=["Groups"])
groups_router.include_router(group_invitation_router, tags=["Groups"])
groups_router.include_router(group_polls_router, tags=["Groups"])
groups_router.include_router(group_reports_router, tags=["Groups"])

# Шаблони груп можуть мати власний префікс, якщо вони не прив'язані до конкретної group_id
# Наприклад, /api/v1/groups/templates
groups_router.include_router(group_templates_router, prefix="/templates", tags=["Groups"]) # Теги вже є в templates.py


__all__ = (
    "groups_router",
)
