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

from fastapi import APIRouter, Depends, HTTPException, status, Path, Response
from typing import List

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.notifications.template import (
    NotificationTemplateSchema,
    NotificationTemplateCreateSchema,
    NotificationTemplateUpdateSchema
)
from backend.app.src.services.notifications.notification_template_service import NotificationTemplateService
from backend.app.src.api.dependencies import DBSession, CurrentSuperuser # Лише суперюзери керують шаблонами
from backend.app.src.models.auth.user import UserModel

logger = get_logger(__name__)
router = APIRouter()

# Префікс /templates вже встановлено в notifications/__init__.py

@router.post(
    "",
    response_model=NotificationTemplateSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Notifications", "Notification Templates (Admin)"],
    summary="Створити новий шаблон сповіщення (суперкористувач)"
)
async def create_notification_template_endpoint(
    template_in: NotificationTemplateCreateSchema,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    logger.info(f"Суперкористувач {current_user.email} створює новий шаблон сповіщення: {template_in.name}.")
    service = NotificationTemplateService(db_session)
    try:
        # creator_id може бути потрібен сервісу для аудиту
        new_template = await service.create_template(
            template_create_data=template_in,
            creator_id=current_user.id
        )
        return new_template
    except HTTPException as e: # Наприклад, якщо шаблон з таким кодом вже існує
        raise e
    except Exception as e_gen:
        logger.error(f"Помилка створення шаблону сповіщення '{template_in.name}': {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")


@router.get(
    "",
    response_model=List[NotificationTemplateSchema],
    tags=["Notifications", "Notification Templates (Admin)"],
    summary="Отримати список всіх шаблонів сповіщень (суперкористувач)"
)
async def list_all_notification_templates(
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    logger.info(f"Суперкористувач {current_user.email} запитує список шаблонів сповіщень.")
    service = NotificationTemplateService(db_session)
    templates = await service.get_all_templates()
    return templates

@router.get(
    "/{template_id}",
    response_model=NotificationTemplateSchema,
    tags=["Notifications", "Notification Templates (Admin)"],
    summary="Отримати деталі шаблону сповіщення за ID (суперкористувач)"
)
async def get_notification_template_details_endpoint(
    template_id: int = Path(..., description="ID шаблону сповіщення"),
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    logger.info(f"Суперкористувач {current_user.email} запитує деталі шаблону сповіщення ID: {template_id}.")
    service = NotificationTemplateService(db_session)
    template = await service.get_template_by_id(template_id=template_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Шаблон сповіщення не знайдено.")
    return template


@router.put(
    "/{template_id}",
    response_model=NotificationTemplateSchema,
    tags=["Notifications", "Notification Templates (Admin)"],
    summary="Оновити шаблон сповіщення (суперкористувач)"
)
async def update_notification_template_endpoint(
    template_id: int = Path(..., description="ID шаблону сповіщення"),
    template_in: NotificationTemplateUpdateSchema,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    logger.info(f"Суперкористувач {current_user.email} оновлює шаблон сповіщення ID: {template_id}.")
    service = NotificationTemplateService(db_session)
    try:
        updated_template = await service.update_template(
            template_id=template_id,
            template_update_data=template_in
        )
        if not updated_template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Шаблон сповіщення не знайдено для оновлення.")
        return updated_template
    except HTTPException as e: # Наприклад, якщо новий код шаблону вже існує
        raise e
    except Exception as e_gen:
        logger.error(f"Помилка оновлення шаблону сповіщення ID {template_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")

@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Notifications", "Notification Templates (Admin)"],
    summary="Видалити шаблон сповіщення (суперкористувач)"
)
async def delete_notification_template_endpoint(
    template_id: int = Path(..., description="ID шаблону сповіщення"),
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    logger.info(f"Суперкористувач {current_user.email} видаляє шаблон сповіщення ID: {template_id}.")
    service = NotificationTemplateService(db_session)
    try:
        success = await service.delete_template(template_id=template_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Шаблон сповіщення не знайдено або не вдалося видалити.")
    except HTTPException as e: # Якщо сервіс кидає помилку (напр. шаблон використовується)
        raise e
    except Exception as e_gen:
        logger.error(f"Помилка видалення шаблону сповіщення ID {template_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Роутер буде підключений в backend/app/src/api/v1/notifications/__init__.py
# з префіксом /templates
