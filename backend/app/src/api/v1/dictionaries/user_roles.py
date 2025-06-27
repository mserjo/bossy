# backend/app/src/api/v1/dictionaries/user_roles.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління довідником "Ролі користувачів".

Цей модуль надає API для CRUD операцій з довідником ролей користувачів
(наприклад, 'superadmin', 'admin', 'user').

Доступ до управління зазвичай має лише суперкористувач.
Перегляд може бути доступний ширшому колу.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response # Додано Response
from typing import List # Optional не потрібен для List[UserRoleSchema]

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.dictionaries.user_role import UserRoleSchema, UserRoleCreateSchema, UserRoleUpdateSchema
from backend.app.src.services.dictionaries.user_role_service import UserRoleService
from backend.app.src.api.dependencies import DBSession, CurrentSuperuser, CurrentActiveUser
from backend.app.src.models.auth.user import UserModel # Для type hint current_user

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "", # Шлях тепер визначається в __init__.py пакету dictionaries
    response_model=List[UserRoleSchema],
    tags=["Dictionaries", "User Roles"],
    summary="Отримати список всіх ролей користувачів"
)
async def list_all_user_roles(
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentActiveUser)
):
    logger.info(f"Користувач {current_user.email} запитує список ролей користувачів.")
    role_service = UserRoleService(db_session)
    roles = await role_service.get_all_user_roles() # Або get_all, якщо успадковується від BaseDictService
    return roles

@router.post(
    "",
    response_model=UserRoleSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Dictionaries", "User Roles"],
    summary="Створити нову роль користувача",
)
async def create_new_user_role(
    role_data: UserRoleCreateSchema,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    logger.info(f"Користувач {current_user.email} створює нову роль: {role_data.name}.")
    role_service = UserRoleService(db_session)
    try:
        new_role = await role_service.create_user_role(role_in=role_data) # Або create
        return new_role
    except HTTPException as e:
        logger.warning(f"Помилка створення ролі '{role_data.code}': {e.detail}")
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при створенні ролі {role_data.name}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")


@router.get(
    "/{role_id}",
    response_model=UserRoleSchema,
    tags=["Dictionaries", "User Roles"],
    summary="Отримати деталі конкретної ролі користувача"
)
async def get_user_role_details(
    role_id: int,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentActiveUser)
):
    logger.info(f"Користувач {current_user.email} запитує деталі ролі ID: {role_id}.")
    role_service = UserRoleService(db_session)
    role = await role_service.get_by_id(obj_id=role_id) # Використовуємо get_by_id
    if not role:
        logger.warning(f"Роль ID {role_id} не знайдено (запит від {current_user.email}).")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Роль не знайдено")
    return role

@router.put(
    "/{role_id}",
    response_model=UserRoleSchema,
    tags=["Dictionaries", "User Roles"],
    summary="Оновити існуючу роль користувача",
)
async def update_existing_user_role(
    role_id: int,
    role_data: UserRoleUpdateSchema,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    logger.info(f"Користувач {current_user.email} оновлює роль ID: {role_id}.")
    role_service = UserRoleService(db_session)
    try:
        updated_role = await role_service.update(obj_id=role_id, obj_in=role_data)
        if not updated_role:
            logger.warning(f"Роль ID {role_id} не знайдено для оновлення (запит від {current_user.email}).")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Роль не знайдено для оновлення")
        return updated_role
    except HTTPException as e:
        logger.warning(f"Помилка оновлення ролі ID {role_id}: {e.detail}")
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при оновленні ролі ID {role_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Dictionaries", "User Roles"],
    summary="Видалити роль користувача",
)
async def delete_existing_user_role(
    role_id: int,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    logger.info(f"Користувач {current_user.email} видаляє роль ID: {role_id}.")
    role_service = UserRoleService(db_session)
    try:
        removed_role = await role_service.remove(obj_id=role_id) # remove може кидати виняток, якщо не можна видалити
        if not removed_role: # Якщо remove повертає None при не знайденому об'єкті
             logger.warning(f"Роль ID {role_id} не знайдено для видалення (запит від {current_user.email}).")
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Роль не знайдено для видалення")
    except HTTPException as e:
        logger.warning(f"Помилка видалення ролі ID {role_id}: {e.detail}")
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при видаленні ролі ID {role_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Роутер буде підключений в backend/app/src/api/v1/dictionaries/__init__.py
