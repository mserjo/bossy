# backend/app/src/api/v1/notifications/templates.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління шаблонами сповіщень API v1 (адміністративні).

Цей модуль надає API для адміністраторів системи для:
- Створення нових шаблонів сповіщень (для різних типів подій, мов, каналів).
- Перегляду списку існуючих шаблонів з фільтрацією та пагінацією.
- Отримання деталей конкретного шаблону.
- Оновлення існуючого шаблону.
- Видалення шаблону.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query, Response
from typing import List, Optional

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.notifications.template import (
    NotificationTemplateSchema,
    NotificationTemplateCreateSchema,
    NotificationTemplateUpdateSchema
)
from backend.app.src.services.notifications.notification_template_service import NotificationTemplateService
from backend.app.src.api.dependencies import DBSession, CurrentSuperuser
from backend.app.src.models.auth.user import UserModel
from backend.app.src.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE

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
    logger.info(f"Суперкористувач {current_user.email} створює новий шаблон сповіщення: {template_in.name} ({template_in.template_code}).")
    service = NotificationTemplateService(db_session)
    try:
        new_template = await service.create_template(
            template_create_data=template_in,
            creator_id=current_user.id
        )
        return new_template
    except ValueError as ve: # Наприклад, якщо шаблон з таким кодом + мова + канал вже існує
        logger.warning(f"Помилка валідації при створенні шаблону '{template_in.name}': {str(ve)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e_gen:
        logger.error(f"Помилка створення шаблону сповіщення '{template_in.name}': {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при створенні шаблону.")


@router.get(
    "",
    response_model=List[NotificationTemplateSchema], # Або схема з пагінацією
    tags=["Notifications", "Notification Templates (Admin)"],
    summary="Отримати список всіх шаблонів сповіщень (суперкористувач)"
)
async def list_all_notification_templates(
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser),
    page: int = Query(DEFAULT_PAGE, ge=1, description="Номер сторінки"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100, description="Розмір сторінки"),
    template_code: Optional[str] = Query(None, description="Фільтр за кодом шаблону"),
    language_code: Optional[str] = Query(None, description="Фільтр за кодом мови (напр., 'uk', 'en')"),
    channel_type: Optional[str] = Query(None, description="Фільтр за типом каналу (напр., 'EMAIL', 'SMS')"),
    is_active: Optional[bool] = Query(None, description="Фільтр за активністю шаблону")
):
    logger.info(
        f"Суперкористувач {current_user.email} запитує список шаблонів сповіщень "
        f"(стор: {page}, розм: {page_size}, код: {template_code}, мова: {language_code}, "
        f"канал: {channel_type}, активний: {is_active})."
    )
    service = NotificationTemplateService(db_session)
    templates_data = await service.get_all_templates_paginated(
        skip=(page - 1) * page_size,
        limit=page_size,
        template_code=template_code,
        language_code=language_code,
        channel_type=channel_type,
        is_active=is_active
    )
    # Припускаємо, що сервіс повертає {"templates": [], "total": 0}
    if isinstance(templates_data, dict):
        templates = templates_data.get("templates", [])
        # total_templates = templates_data.get("total", 0) # Для заголовків пагінації
    else: # Якщо сервіс повертає просто список (стара версія)
        templates = templates_data
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
        if not updated_template: # Сервіс може повернути None або кинути помилку, якщо не знайдено
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Шаблон сповіщення не знайдено для оновлення.")
        return updated_template
    except ValueError as ve: # Наприклад, конфлікт унікальності коду
        logger.warning(f"Помилка валідації при оновленні шаблону ID {template_id}: {str(ve)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e_gen:
        logger.error(f"Помилка оновлення шаблону сповіщення ID {template_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при оновленні шаблону.")

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
    except ValueError as ve: # Наприклад, якщо шаблон використовується і не може бути видалений
        logger.warning(f"Помилка видалення шаблону ID {template_id}: {str(ve)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e_gen:
        logger.error(f"Помилка видалення шаблону сповіщення ID {template_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при видаленні шаблону.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
