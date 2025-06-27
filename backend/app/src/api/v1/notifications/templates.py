# backend/app/src/api/v1/notifications/templates.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління шаблонами сповіщень API v1 (адміністративні).

Цей модуль надає API для адміністраторів системи для:
- Створення нових шаблонів сповіщень (для різних типів подій, мов).
- Перегляду списку існуючих шаблонів.
- Отримання деталей конкретного шаблону.
- Оновлення існуючого шаблону.
- Видалення шаблону.
"""

from fastapi import APIRouter, Depends, status
from typing import List
from backend.app.src.config.logging import get_logger
# TODO: Імпортувати схеми (NotificationTemplateSchema, ...CreateSchema, ...UpdateSchema)
# TODO: Імпортувати сервіс NotificationTemplateService
# TODO: Імпортувати залежності (DBSession, CurrentSuperuser)

logger = get_logger(__name__)
router = APIRouter()

# Ендпоінти будуть мати префікс /notifications/templates (глобально для системи)

@router.post(
    "", # Тобто /notifications/templates
    # response_model=NotificationTemplateSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Notifications", "Notification Templates (Admin)"],
    summary="Створити новий шаблон сповіщення (адмін) (заглушка)"
    # dependencies=[Depends(CurrentSuperuser)]
)
async def create_notification_template(
    # template_in: NotificationTemplateCreateSchema
):
    logger.info(f"Адміністратор (ID TODO) створює новий шаблон сповіщення (заглушка).")
    # TODO: Реалізувати логіку створення шаблону
    return {"template_id": "tpl_notify_abc", "name": "Шаблон 'Нове завдання'", "message": "Шаблон створено"}

@router.get(
    "",
    # response_model=List[NotificationTemplateSchema],
    tags=["Notifications", "Notification Templates (Admin)"],
    summary="Отримати список шаблонів сповіщень (адмін) (заглушка)"
    # dependencies=[Depends(CurrentSuperuser)]
)
async def list_notification_templates():
    logger.info(f"Запит списку шаблонів сповіщень (адмін) (заглушка).")
    # TODO: Реалізувати логіку отримання списку шаблонів
    return [
        {"template_id": "tpl_notify_abc", "name": "Шаблон 'Нове завдання'", "subject_template": "Нове завдання в групі {{group_name}}!"},
        {"template_id": "tpl_notify_xyz", "name": "Шаблон 'Завдання виконано'", "subject_template": "Завдання '{{task_name}}' виконано"}
    ]

@router.get(
    "/{template_id}",
    # response_model=NotificationTemplateSchema,
    tags=["Notifications", "Notification Templates (Admin)"],
    summary="Отримати деталі шаблону сповіщення (адмін) (заглушка)"
    # dependencies=[Depends(CurrentSuperuser)]
)
async def get_notification_template_details(
    template_id: str # Або int
):
    logger.info(f"Запит деталей шаблону сповіщення ID: {template_id} (адмін) (заглушка).")
    # TODO: Реалізувати логіку
    return {"template_id": template_id, "name": "Деталі шаблону", "body_template_uk": "Привіт, {{user_name}}..."}


@router.put(
    "/{template_id}",
    # response_model=NotificationTemplateSchema,
    tags=["Notifications", "Notification Templates (Admin)"],
    summary="Оновити шаблон сповіщення (адмін) (заглушка)"
    # dependencies=[Depends(CurrentSuperuser)]
)
async def update_notification_template(
    template_id: str, # Або int
    # template_in: NotificationTemplateUpdateSchema
):
    logger.info(f"Адміністратор (ID TODO) оновлює шаблон сповіщення ID: {template_id} (заглушка).")
    # TODO: Реалізувати логіку оновлення шаблону
    return {"template_id": template_id, "message": "Шаблон оновлено"}

@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Notifications", "Notification Templates (Admin)"],
    summary="Видалити шаблон сповіщення (адмін) (заглушка)"
    # dependencies=[Depends(CurrentSuperuser)]
)
async def delete_notification_template(
    template_id: str # Або int
):
    logger.info(f"Адміністратор (ID TODO) видаляє шаблон сповіщення ID: {template_id} (заглушка).")
    # TODO: Реалізувати логіку видалення шаблону
    return

# Роутер буде підключений в backend/app/src/api/v1/notifications/__init__.py
