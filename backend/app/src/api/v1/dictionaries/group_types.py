# backend/app/src/api/v1/dictionaries/group_types.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління довідником "Типи груп".

Наприклад: сім'я, відділ, організація.
Доступ до управління - суперкористувач.
"""

from fastapi import APIRouter
from backend.app.src.config.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# TODO: Реалізувати CRUD ендпоінти для довідника "Типи груп".
# По аналогії з statuses.py або user_roles.py.
# Потрібні будуть схеми GroupTypeSchema, GroupTypeCreateSchema, GroupTypeUpdateSchema
# та сервіс GroupTypeService.

@router.get("/group-types", tags=["Dictionaries", "Group Types"], summary="Отримати список типів груп (заглушка)")
async def list_group_types():
    logger.info("Запит на отримання списку типів груп (заглушка).")
    return [{"id": 1, "code": "FAMILY", "name": "Сім'я"}, {"id": 2, "code": "DEPARTMENT", "name": "Відділ"}]

# Роутер буде підключений в backend/app/src/api/v1/dictionaries/__init__.py
