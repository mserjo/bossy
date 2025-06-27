# backend/app/src/api/v1/groups/templates.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління шаблонами груп API v1.

Цей модуль надає API для суперкористувачів (або спеціально призначених ролей) для:
- Створення нових шаблонів груп.
- Перегляду списку доступних шаблонів груп.
- Отримання деталей конкретного шаблону.
- Оновлення існуючого шаблону групи.
- Видалення шаблону групи.

Шаблони груп містять передвизначені налаштування, типи завдань, нагороди тощо,
для швидкого розгортання нових схожих груп.
"""

from fastapi import APIRouter, Depends, status
from typing import List
from backend.app.src.config.logging import get_logger
# TODO: Імпортувати схеми (GroupTemplateSchema, GroupTemplateCreateSchema тощо).
# TODO: Імпортувати сервіс GroupTemplateService.
# TODO: Імпортувати залежності (DBSession, CurrentSuperuser).

logger = get_logger(__name__)
router = APIRouter()

@router.post(
    "/templates",
    # response_model=GroupTemplateSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Groups", "Group Templates"],
    summary="Створити новий шаблон групи (заглушка)"
    # dependencies=[Depends(CurrentSuperuser)]
)
async def create_group_template(
    # template_data: GroupTemplateCreateSchema
):
    logger.info(f"Суперкористувач (ID TODO) створює новий шаблон групи (заглушка).")
    # TODO: Реалізувати логіку створення шаблону
    return {"template_id": "tpl_123", "name": "Шаблон 'Робоча команда'", "message": "Шаблон створено"}

@router.get(
    "/templates",
    # response_model=List[GroupTemplateSchema],
    tags=["Groups", "Group Templates"],
    summary="Отримати список всіх шаблонів груп (заглушка)"
    # dependencies=[Depends(CurrentActiveUser)] # Можливо, всі активні користувачі можуть бачити шаблони
)
async def list_group_templates():
    logger.info(f"Запит списку шаблонів груп (заглушка).")
    # TODO: Реалізувати логіку отримання списку шаблонів
    return [
        {"template_id": "tpl_123", "name": "Шаблон 'Робоча команда'", "description": "Для проектних груп"},
        {"template_id": "tpl_456", "name": "Шаблон 'Сім'я'", "description": "Для сімейних завдань та бонусів"}
    ]

@router.get(
    "/templates/{template_id}",
    # response_model=GroupTemplateSchema,
    tags=["Groups", "Group Templates"],
    summary="Отримати деталі шаблону групи (заглушка)"
    # dependencies=[Depends(CurrentActiveUser)]
)
async def get_group_template_details(
    template_id: str # Або int
):
    logger.info(f"Запит деталей шаблону групи ID: {template_id} (заглушка).")
    # TODO: Реалізувати логіку отримання деталей шаблону
    if template_id == "tpl_123":
        return {"template_id": "tpl_123", "name": "Шаблон 'Робоча команда'", "description": "Для проектних груп", "settings": {"default_currency": "бали"}}
    return {"message": "Шаблон не знайдено"}, 404

@router.put(
    "/templates/{template_id}",
    # response_model=GroupTemplateSchema,
    tags=["Groups", "Group Templates"],
    summary="Оновити шаблон групи (заглушка)"
    # dependencies=[Depends(CurrentSuperuser)]
)
async def update_group_template(
    template_id: str, # Або int
    # template_update_data: GroupTemplateUpdateSchema
):
    logger.info(f"Суперкористувач (ID TODO) оновлює шаблон групи ID: {template_id} (заглушка).")
    # TODO: Реалізувати логіку оновлення шаблону
    return {"template_id": template_id, "name": "Оновлений Шаблон 'Робоча команда'", "message": "Шаблон оновлено"}

@router.delete(
    "/templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Groups", "Group Templates"],
    summary="Видалити шаблон групи (заглушка)"
    # dependencies=[Depends(CurrentSuperuser)]
)
async def delete_group_template(
    template_id: str # Або int
):
    logger.info(f"Суперкористувач (ID TODO) видаляє шаблон групи ID: {template_id} (заглушка).")
    # TODO: Реалізувати логіку видалення шаблону
    return

# Роутер буде підключений в backend/app/src/api/v1/groups/__init__.py
