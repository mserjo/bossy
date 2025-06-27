# backend/app/src/api/v1/dictionaries/bonus_types.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління довідником "Типи бонусів".

Наприклад: бонуси, бали, зірочки.
Цей довідник налаштовується суперкористувачем, а потім
адміністратор групи може обрати один з типів для своєї групи.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import List, Optional

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.dictionaries.bonus_type import BonusTypeSchema, BonusTypeCreateSchema, BonusTypeUpdateSchema
from backend.app.src.services.dictionaries.bonus_type_service import BonusTypeService
from backend.app.src.api.dependencies import DBSession, CurrentSuperuser, CurrentActiveUser
from backend.app.src.models.auth.user import UserModel

logger = get_logger(__name__)
router = APIRouter()

@router.get(
    "",
    response_model=List[BonusTypeSchema],
    tags=["Dictionaries", "Bonus Types"],
    summary="Отримати список всіх типів бонусів"
)
async def list_all_bonus_types(
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentActiveUser)
):
    logger.info(f"Користувач {current_user.email} запитує список типів бонусів.")
    service = BonusTypeService(db_session)
    items = await service.get_all() # Використовуємо get_all з BaseDictService
    return items

@router.post(
    "",
    response_model=BonusTypeSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Dictionaries", "Bonus Types"],
    summary="Створити новий тип бонусу (суперкористувач)"
)
async def create_new_bonus_type(
    bonus_type_in: BonusTypeCreateSchema,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    logger.info(f"Суперкористувач {current_user.email} створює новий тип бонусу: {bonus_type_in.name}.")
    service = BonusTypeService(db_session)
    try:
        new_item = await service.create(obj_in=bonus_type_in)
        return new_item
    except HTTPException as e:
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при створенні типу бонусу {bonus_type_in.name}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")

@router.get(
    "/{bonus_type_id}",
    response_model=BonusTypeSchema,
    tags=["Dictionaries", "Bonus Types"],
    summary="Отримати деталі типу бонусу за ID"
)
async def get_bonus_type_details(
    bonus_type_id: int,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentActiveUser)
):
    logger.info(f"Користувач {current_user.email} запитує деталі типу бонусу ID: {bonus_type_id}.")
    service = BonusTypeService(db_session)
    item = await service.get_by_id(obj_id=bonus_type_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип бонусу не знайдено.")
    return item

@router.put(
    "/{bonus_type_id}",
    response_model=BonusTypeSchema,
    tags=["Dictionaries", "Bonus Types"],
    summary="Оновити тип бонусу (суперкористувач)"
)
async def update_existing_bonus_type(
    bonus_type_id: int,
    bonus_type_in: BonusTypeUpdateSchema,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    logger.info(f"Суперкористувач {current_user.email} оновлює тип бонусу ID: {bonus_type_id}.")
    service = BonusTypeService(db_session)
    try:
        updated_item = await service.update(obj_id=bonus_type_id, obj_in=bonus_type_in)
        if not updated_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип бонусу не знайдено для оновлення.")
        return updated_item
    except HTTPException as e:
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при оновленні типу бонусу ID {bonus_type_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")

@router.delete(
    "/{bonus_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Dictionaries", "Bonus Types"],
    summary="Видалити тип бонусу (суперкористувач)"
)
async def delete_existing_bonus_type(
    bonus_type_id: int,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    logger.info(f"Суперкористувач {current_user.email} видаляє тип бонусу ID: {bonus_type_id}.")
    service = BonusTypeService(db_session)
    try:
        removed_item = await service.remove(obj_id=bonus_type_id)
        if not removed_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип бонусу не знайдено для видалення.")
    except HTTPException as e:
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при видаленні типу бонусу ID {bonus_type_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Роутер буде підключений в backend/app/src/api/v1/dictionaries/__init__.py
