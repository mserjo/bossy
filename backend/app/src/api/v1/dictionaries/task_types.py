# backend/app/src/api/v1/dictionaries/task_types.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління довідником "Типи завдань".

Наприклад: завдання, підзавдання, подія, штраф.
Доступ до управління - суперкористувач.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import List, Optional

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.dictionaries.task_type import TaskTypeSchema, TaskTypeCreateSchema, TaskTypeUpdateSchema
from backend.app.src.services.dictionaries.task_type_service import TaskTypeService
from backend.app.src.api.dependencies import DBSession, CurrentSuperuser, CurrentActiveUser
from backend.app.src.models.auth.user import UserModel

logger = get_logger(__name__)
router = APIRouter()

@router.get(
    "",
    response_model=List[TaskTypeSchema],
    tags=["Dictionaries", "Task Types"],
    summary="Отримати список всіх типів завдань"
)
async def list_all_task_types(
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentActiveUser)
):
    logger.info(f"Користувач {current_user.email} запитує список типів завдань.")
    service = TaskTypeService(db_session)
    items = await service.get_all()
    return items

@router.post(
    "",
    response_model=TaskTypeSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Dictionaries", "Task Types"],
    summary="Створити новий тип завдання (суперкористувач)"
)
async def create_new_task_type(
    task_type_in: TaskTypeCreateSchema,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    logger.info(f"Суперкористувач {current_user.email} створює новий тип завдання: {task_type_in.name}.")
    service = TaskTypeService(db_session)
    try:
        new_item = await service.create(obj_in=task_type_in)
        return new_item
    except HTTPException as e:
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при створенні типу завдання {task_type_in.name}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")

@router.get(
    "/{task_type_id}",
    response_model=TaskTypeSchema,
    tags=["Dictionaries", "Task Types"],
    summary="Отримати деталі типу завдання за ID"
)
async def get_task_type_details(
    task_type_id: int,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentActiveUser)
):
    logger.info(f"Користувач {current_user.email} запитує деталі типу завдання ID: {task_type_id}.")
    service = TaskTypeService(db_session)
    item = await service.get_by_id(obj_id=task_type_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип завдання не знайдено.")
    return item

@router.put(
    "/{task_type_id}",
    response_model=TaskTypeSchema,
    tags=["Dictionaries", "Task Types"],
    summary="Оновити тип завдання (суперкористувач)"
)
async def update_existing_task_type(
    task_type_id: int,
    task_type_in: TaskTypeUpdateSchema,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    logger.info(f"Суперкористувач {current_user.email} оновлює тип завдання ID: {task_type_id}.")
    service = TaskTypeService(db_session)
    try:
        updated_item = await service.update(obj_id=task_type_id, obj_in=task_type_in)
        if not updated_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип завдання не знайдено для оновлення.")
        return updated_item
    except HTTPException as e:
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при оновленні типу завдання ID {task_type_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")

@router.delete(
    "/{task_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Dictionaries", "Task Types"],
    summary="Видалити тип завдання (суперкористувач)"
)
async def delete_existing_task_type(
    task_type_id: int,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    logger.info(f"Суперкористувач {current_user.email} видаляє тип завдання ID: {task_type_id}.")
    service = TaskTypeService(db_session)
    try:
        removed_item = await service.remove(obj_id=task_type_id)
        if not removed_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип завдання не знайдено для видалення.")
    except HTTPException as e:
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при видаленні типу завдання ID {task_type_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Роутер буде підключений в backend/app/src/api/v1/dictionaries/__init__.py
