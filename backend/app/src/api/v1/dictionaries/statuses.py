# backend/app/src/api/v1/dictionaries/statuses.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління довідником "Статуси".

Цей модуль надає API для CRUD (Create, Read, Update, Delete) операцій
з довідником статусів, які можуть використовуватися для різних сутностей
в системі (наприклад, статус завдання, статус користувача тощо).

Доступ до управління довідниками зазвичай має лише суперкористувач.
Перегляд може бути доступний ширшому колу користувачів.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response # Додано Response
from typing import List, Optional

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.dictionaries.status import StatusSchema, StatusCreateSchema, StatusUpdateSchema
from backend.app.src.services.dictionaries.status_service import StatusService
from backend.app.src.api.dependencies import DBSession, CurrentSuperuser, CurrentActiveUser # Реальні залежності
from backend.app.src.models.auth.user import UserModel # Для type hint current_user

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "", # Шлях тепер визначається в __init__.py пакету dictionaries
    response_model=List[StatusSchema],
    tags=["Dictionaries", "Statuses"],
    summary="Отримати список всіх статусів"
)
async def list_all_statuses(
    entity_type: Optional[str] = None,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentActiveUser) # Доступ для читання може бути ширшим
):
    """
    Повертає список всіх налаштованих статусів.
    Може бути відфільтровано за `entity_type` (наприклад, 'task', 'user').
    """
    logger.info(
        f"Користувач {current_user.email} запитує список статусів (entity_type: {entity_type})."
    )
    status_service = StatusService(db_session)
    statuses = await status_service.get_all_statuses(entity_type=entity_type)
    return statuses

@router.post(
    "",
    response_model=StatusSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Dictionaries", "Statuses"],
    summary="Створити новий статус",
)
async def create_new_status(
    status_data: StatusCreateSchema,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser) # Лише суперюзер може створювати
):
    """
    Створює новий статус в довіднику.
    Потребує прав суперкористувача.
    """
    logger.info(f"Користувач {current_user.email} створює новий статус: {status_data.name}.")
    status_service = StatusService(db_session)
    try:
        # StatusService.create_status повинен обробляти унікальність (code + entity_type)
        new_status = await status_service.create_status(status_in=status_data)
        return new_status
    except HTTPException as e: # Якщо сервіс кидає помилку (напр. дублікат)
        logger.warning(f"Помилка створення статусу '{status_data.code}': {e.detail}")
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка під час створення статусу {status_data.name}: {e_gen}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка сервера під час створення статусу."
        )


@router.get(
    "/{status_id}",
    response_model=StatusSchema,
    tags=["Dictionaries", "Statuses"],
    summary="Отримати деталі конкретного статусу"
)
async def get_status_details(
    status_id: int,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentActiveUser)
):
    """
    Повертає детальну інформацію про вказаний статус.
    """
    logger.info(f"Користувач {current_user.email} запитує деталі статусу ID: {status_id}.")
    status_service = StatusService(db_session)
    status_obj = await status_service.get_by_id(obj_id=status_id) # Використовуємо get_by_id з BaseDictService
    if not status_obj:
        logger.warning(f"Статус з ID {status_id} не знайдено (запит від {current_user.email}).")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статус не знайдено")
    return status_obj

@router.put(
    "/{status_id}",
    response_model=StatusSchema,
    tags=["Dictionaries", "Statuses"],
    summary="Оновити існуючий статус",
)
async def update_existing_status(
    status_id: int,
    status_data: StatusUpdateSchema,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    """
    Оновлює параметри існуючого статусу.
    Потребує прав суперкористувача.
    """
    logger.info(f"Користувач {current_user.email} оновлює статус ID: {status_id}.")
    status_service = StatusService(db_session)
    try:
        # StatusService.update повинен приймати id та схему оновлення
        updated_status = await status_service.update(obj_id=status_id, obj_in=status_data)
        if not updated_status: # Малоймовірно, якщо сервіс кидає виняток при неіснуючому ID
            logger.warning(f"Статус з ID {status_id} не знайдено для оновлення (запит від {current_user.email}).")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статус не знайдено для оновлення")
        return updated_status
    except HTTPException as e:
        logger.warning(f"Помилка оновлення статусу ID {status_id}: {e.detail}")
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка під час оновлення статусу ID {status_id}: {e_gen}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка сервера під час оновлення статусу."
        )

@router.delete(
    "/{status_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Dictionaries", "Statuses"],
    summary="Видалити статус",
)
async def delete_existing_status(
    status_id: int,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    """
    Видаляє існуючий статус з довідника.
    Потребує прав суперкористувача.
    **Увага:** Переконайтеся, що статус не використовується перед видаленням.
    """
    logger.info(f"Користувач {current_user.email} видаляє статус ID: {status_id}.")
    status_service = StatusService(db_session)

    # StatusService.remove повинен повертати видалений об'єкт або кидати виняток
    removed_status = await status_service.remove(obj_id=status_id)
    if not removed_status: # Малоймовірно, якщо сервіс кидає виняток
        logger.warning(f"Статус з ID {status_id} не знайдено для видалення (запит від {current_user.email}).")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статус не знайдено для видалення")

    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Роутер буде підключений в backend/app/src/api/v1/dictionaries/__init__.py
