# backend/app/src/api/v1/dictionaries/integration_types.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління довідником "Типи зовнішніх інтеграцій".

Наприклад: Google Calendar, Telegram Bot, Jira.
Доступ до управління - суперкористувач.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import List, Optional

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.dictionaries.integration_type import (
    IntegrationTypeSchema,
    IntegrationTypeCreateSchema,
    IntegrationTypeUpdateSchema
)
from backend.app.src.services.dictionaries.integration_type_service import IntegrationTypeService
from backend.app.src.api.dependencies import DBSession, CurrentSuperuser, CurrentActiveUser
from backend.app.src.models.auth.user import UserModel

logger = get_logger(__name__)
router = APIRouter()

@router.get(
    "",
    response_model=List[IntegrationTypeSchema],
    tags=["Dictionaries", "Integration Types"],
    summary="Отримати список всіх типів інтеграцій"
)
async def list_all_integration_types(
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentActiveUser)
):
    logger.info(f"Користувач {current_user.email} запитує список типів інтеграцій.")
    service = IntegrationTypeService(db_session)
    items = await service.get_all()
    return items

@router.post(
    "",
    response_model=IntegrationTypeSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Dictionaries", "Integration Types"],
    summary="Створити новий тип інтеграції (суперкористувач)"
)
async def create_new_integration_type(
    integration_type_in: IntegrationTypeCreateSchema,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    logger.info(f"Суперкористувач {current_user.email} створює новий тип інтеграції: {integration_type_in.name}.")
    service = IntegrationTypeService(db_session)
    try:
        new_item = await service.create(obj_in=integration_type_in)
        return new_item
    except HTTPException as e:
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при створенні типу інтеграції {integration_type_in.name}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")

@router.get(
    "/{integration_type_id}",
    response_model=IntegrationTypeSchema,
    tags=["Dictionaries", "Integration Types"],
    summary="Отримати деталі типу інтеграції за ID"
)
async def get_integration_type_details(
    integration_type_id: int,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentActiveUser)
):
    logger.info(f"Користувач {current_user.email} запитує деталі типу інтеграції ID: {integration_type_id}.")
    service = IntegrationTypeService(db_session)
    item = await service.get_by_id(obj_id=integration_type_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип інтеграції не знайдено.")
    return item

@router.put(
    "/{integration_type_id}",
    response_model=IntegrationTypeSchema,
    tags=["Dictionaries", "Integration Types"],
    summary="Оновити тип інтеграції (суперкористувач)"
)
async def update_existing_integration_type(
    integration_type_id: int,
    integration_type_in: IntegrationTypeUpdateSchema,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    logger.info(f"Суперкористувач {current_user.email} оновлює тип інтеграції ID: {integration_type_id}.")
    service = IntegrationTypeService(db_session)
    try:
        updated_item = await service.update(obj_id=integration_type_id, obj_in=integration_type_in)
        if not updated_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип інтеграції не знайдено для оновлення.")
        return updated_item
    except HTTPException as e:
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при оновленні типу інтеграції ID {integration_type_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")

@router.delete(
    "/{integration_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Dictionaries", "Integration Types"],
    summary="Видалити тип інтеграції (суперкористувач)"
)
async def delete_existing_integration_type(
    integration_type_id: int,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    logger.info(f"Суперкористувач {current_user.email} видаляє тип інтеграції ID: {integration_type_id}.")
    service = IntegrationTypeService(db_session)
    try:
        removed_item = await service.remove(obj_id=integration_type_id)
        if not removed_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип інтеграції не знайдено для видалення.")
    except HTTPException as e:
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при видаленні типу інтеграції ID {integration_type_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Роутер буде підключений в backend/app/src/api/v1/dictionaries/__init__.py
