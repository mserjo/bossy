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

from fastapi import APIRouter, Depends, HTTPException, status, Path, Response
from typing import List

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.groups.template import GroupTemplateSchema, GroupTemplateCreateSchema, GroupTemplateUpdateSchema
from backend.app.src.services.groups.group_template_service import GroupTemplateService
from backend.app.src.api.dependencies import DBSession, CurrentSuperuser, CurrentActiveUser
from backend.app.src.models.auth.user import UserModel

logger = get_logger(__name__)
router = APIRouter()

# Префікс /templates вже встановлено в groups/__init__.py

@router.post(
    "", # Відповідає /groups/templates
    response_model=GroupTemplateSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Groups", "Group Templates"],
    summary="Створити новий шаблон групи (суперкористувач)"
)
async def create_group_template_endpoint(
    template_in: GroupTemplateCreateSchema,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser) # Лише суперюзер
):
    logger.info(f"Суперкористувач {current_user.email} створює новий шаблон групи: {template_in.name}.")
    service = GroupTemplateService(db_session)
    try:
        # creator_id може бути потрібен сервісу
        new_template = await service.create_template(template_create_data=template_in, creator_id=current_user.id)
        return new_template
    except HTTPException as e:
        raise e
    except Exception as e_gen:
        logger.error(f"Помилка створення шаблону групи '{template_in.name}': {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")


@router.get(
    "",
    response_model=List[GroupTemplateSchema],
    tags=["Groups", "Group Templates"],
    summary="Отримати список всіх шаблонів груп"
)
async def list_all_group_templates(
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentActiveUser) # Будь-який активний користувач може бачити список
):
    logger.info(f"Користувач {current_user.email} запитує список шаблонів груп.")
    service = GroupTemplateService(db_session)
    templates = await service.get_all_templates()
    return templates

@router.get(
    "/{template_id}",
    response_model=GroupTemplateSchema,
    tags=["Groups", "Group Templates"],
    summary="Отримати деталі шаблону групи за ID"
)
async def get_group_template_details_endpoint(
    template_id: int = Path(..., description="ID шаблону групи"),
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentActiveUser)
):
    logger.info(f"Користувач {current_user.email} запитує деталі шаблону групи ID: {template_id}.")
    service = GroupTemplateService(db_session)
    template = await service.get_template_by_id(template_id=template_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Шаблон групи не знайдено.")
    return template

@router.put(
    "/{template_id}",
    response_model=GroupTemplateSchema,
    tags=["Groups", "Group Templates"],
    summary="Оновити шаблон групи (суперкористувач)"
)
async def update_group_template_endpoint(
    template_id: int = Path(..., description="ID шаблону групи"),
    template_in: GroupTemplateUpdateSchema,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    logger.info(f"Суперкористувач {current_user.email} оновлює шаблон групи ID: {template_id}.")
    service = GroupTemplateService(db_session)
    try:
        updated_template = await service.update_template(
            template_id=template_id,
            template_update_data=template_in
        )
        if not updated_template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Шаблон групи не знайдено для оновлення.")
        return updated_template
    except HTTPException as e:
        raise e
    except Exception as e_gen:
        logger.error(f"Помилка оновлення шаблону групи ID {template_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")

@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Groups", "Group Templates"],
    summary="Видалити шаблон групи (суперкористувач)"
)
async def delete_group_template_endpoint(
    template_id: int = Path(..., description="ID шаблону групи"),
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    logger.info(f"Суперкористувач {current_user.email} видаляє шаблон групи ID: {template_id}.")
    service = GroupTemplateService(db_session)
    try:
        success = await service.delete_template(template_id=template_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Шаблон групи не знайдено або не вдалося видалити.")
    except HTTPException as e: # Якщо сервіс кидає помилку (напр. шаблон використовується)
        raise e
    except Exception as e_gen:
        logger.error(f"Помилка видалення шаблону групи ID {template_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Роутер буде підключений в backend/app/src/api/v1/groups/__init__.py
# з префіксом /templates
