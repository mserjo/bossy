# backend/app/src/api/v1/users/users.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для адміністративного управління користувачами API v1.

Цей модуль надає API для суперкористувачів (або адміністраторів системи)
для виконання CRUD операцій над усіма користувачами системи, а також
для управління їх атрибутами (ролі, статус активності тощо).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from typing import List, Optional

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.auth.user import (
    UserSchema,         # Для представлення користувача (можливо, більш детальна, ніж UserPublicSchema)
    UserCreateSchema,   # Може бути така ж, як для реєстрації, або спеціальна адмінська
    UserUpdateSchema,   # Схема для оновлення користувача адміністратором
    UserAdminCreateSchema, # Спеціальна схема для створення адміном (якщо відрізняється)
    UserAdminUpdateSchema  # Спеціальна схема для оновлення адміном (якщо відрізняється)
)
from backend.app.src.services.auth.user_service import UserService
from backend.app.src.api.dependencies import DBSession, CurrentSuperuser
from backend.app.src.models.auth.user import UserModel # Для type hint current_user та інших
from backend.app.src.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE # Для пагінації

logger = get_logger(__name__)
router = APIRouter()

# Припускаємо, що UserSchema - це детальна схема для адміна,
# UserAdminCreateSchema - для створення адміном (може включати is_active, is_superuser, роль),
# UserAdminUpdateSchema - для оновлення адміном.

@router.get(
    "", # Шлях визначається префіксом "/users" в головному роутері v1
    response_model=List[UserSchema], # Повертаємо список користувачів
    tags=["Users (Admin)"],
    summary="Отримати список всіх користувачів (адміністративний)"
)
async def list_all_users(
    db_session: DBSession = Depends(),
    current_admin: UserModel = Depends(CurrentSuperuser),
    page: int = Query(DEFAULT_PAGE, ge=1, description="Номер сторінки"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100, description="Розмір сторінки"),
    # TODO: Додати фільтри, якщо потрібно (наприклад, за email, username, is_active)
    # email: Optional[str] = Query(None, description="Фільтр за email (часткове співпадіння)"),
    # username: Optional[str] = Query(None, description="Фільтр за ім'ям користувача (часткове співпадіння)"),
    # is_active: Optional[bool] = Query(None, description="Фільтр за статусом активності"),
):
    """
    Повертає список всіх користувачів системи з пагінацією.
    Доступно лише суперкористувачам.
    """
    logger.info(
        f"Адміністратор {current_admin.email} запитує список користувачів "
        f"(сторінка: {page}, розмір: {page_size})."
    )
    user_service = UserService(db_session)
    # Сервіс повинен підтримувати пагінацію та фільтрацію
    # users_data = await user_service.get_multi(
    #     skip=(page - 1) * page_size,
    #     limit=page_size,
    #     filters={"email": email, "username": username, "is_active": is_active} # Приклад фільтрів
    # )
    # users = users_data.get("users", [])
    # total_users = users_data.get("total", 0)

    # Заглушка для get_multi, оскільки він ще не реалізований в заглушці UserService
    users = await user_service.get_all_users_paginated( # Потрібно додати цей метод до UserService
        skip=(page - 1) * page_size,
        limit=page_size
    )
    # total_users = await user_service.count_all_users() # І цей

    # TODO: Додати заголовки для пагінації у відповідь (X-Total-Count, X-Page, X-Page-Size)
    # response.headers["X-Total-Count"] = str(total_users)
    # response.headers["X-Page"] = str(page)
    # response.headers["X-Page-Size"] = str(page_size)

    return users


@router.post(
    "",
    response_model=UserSchema, # Повертаємо повну схему створеного користувача
    status_code=status.HTTP_201_CREATED,
    tags=["Users (Admin)"],
    summary="Створити нового користувача (адміністративний)"
)
async def create_user_by_admin(
    user_in: UserAdminCreateSchema, # Використовуємо спеціальну схему для створення адміном
    db_session: DBSession = Depends(),
    current_admin: UserModel = Depends(CurrentSuperuser)
):
    """
    Створює нового користувача з вказаними даними.
    Дозволяє адміністратору встановлювати додаткові параметри, такі як роль,
    статус активності, чи є суперкористувачем.
    Доступно лише суперкористувачам.
    """
    logger.info(
        f"Адміністратор {current_admin.email} створює нового користувача: {user_in.email} "
        f"(username: {user_in.username or 'не вказано'})."
    )
    user_service = UserService(db_session)
    try:
        # UserService.create_user_by_admin повинен приймати UserAdminCreateSchema
        # та обробляти унікальність email/username
        new_user = await user_service.create_user_by_admin(user_create_data=user_in)
        if not new_user: # Малоймовірно, якщо сервіс кидає винятки
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не вдалося створити користувача")
        logger.info(f"Користувач {new_user.email} успішно створений адміністратором {current_admin.email}.")
        return new_user
    except HTTPException as e: # Якщо сервіс кидає помилку (напр. дублікат)
        logger.warning(f"Помилка створення користувача {user_in.email} адміністратором: {e.detail}")
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при створенні користувача {user_in.email} адміністратором: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")


@router.get(
    "/{user_id}",
    response_model=UserSchema,
    tags=["Users (Admin)"],
    summary="Отримати інформацію про користувача за ID (адміністративний)"
)
async def get_user_by_id_admin(
    user_id: int,
    db_session: DBSession = Depends(),
    current_admin: UserModel = Depends(CurrentSuperuser)
):
    """
    Повертає детальну інформацію про конкретного користувача за його ID.
    Доступно лише суперкористувачам.
    """
    logger.info(f"Адміністратор {current_admin.email} запитує інформацію про користувача ID: {user_id}.")
    user_service = UserService(db_session)
    user = await user_service.get_user_by_id(user_id=user_id)
    if not user:
        logger.warning(f"Користувача з ID {user_id} не знайдено (запит від {current_admin.email}).")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Користувача не знайдено")
    return user


@router.put(
    "/{user_id}",
    response_model=UserSchema,
    tags=["Users (Admin)"],
    summary="Оновити інформацію про користувача (адміністративний)"
)
async def update_user_by_admin(
    user_id: int,
    user_in: UserAdminUpdateSchema, # Спеціальна схема для оновлення адміном
    db_session: DBSession = Depends(),
    current_admin: UserModel = Depends(CurrentSuperuser)
):
    """
    Оновлює інформацію про існуючого користувача.
    Дозволяє адміністратору змінювати різні атрибути користувача.
    Доступно лише суперкористувачам.
    """
    logger.info(f"Адміністратор {current_admin.email} оновлює інформацію для користувача ID: {user_id}.")
    user_service = UserService(db_session)
    try:
        # UserService.update_user_by_admin повинен приймати user_id та UserAdminUpdateSchema
        updated_user = await user_service.update_user_by_admin(user_id=user_id, user_update_data=user_in)
        if not updated_user:
            logger.warning(f"Користувача з ID {user_id} не знайдено для оновлення (запит від {current_admin.email}).")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Користувача не знайдено для оновлення")
        logger.info(f"Інформація користувача ID {user_id} успішно оновлена адміністратором {current_admin.email}.")
        return updated_user
    except HTTPException as e:
        logger.warning(f"Помилка оновлення користувача ID {user_id} адміністратором: {e.detail}")
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при оновленні користувача ID {user_id} адміністратором: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Users (Admin)"],
    summary="Видалити користувача (адміністративний)"
)
async def delete_user_by_admin(
    user_id: int,
    db_session: DBSession = Depends(),
    current_admin: UserModel = Depends(CurrentSuperuser)
):
    """
    Видаляє користувача з системи (або позначає як видаленого).
    **Увага:** Ця дія може бути незворотною. Суперкористувач не може видалити сам себе.
    Доступно лише суперкористувачам.
    """
    if current_admin.id == user_id:
        logger.warning(f"Адміністратор {current_admin.email} спробував видалити сам себе.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Суперкористувач не може видалити сам себе.")

    logger.info(f"Адміністратор {current_admin.email} видаляє користувача ID: {user_id}.")
    user_service = UserService(db_session)

    # UserService.delete_user_by_id повинен повертати boolean або кидати виняток
    deleted_user_id = await user_service.delete_user_by_id(user_id=user_id) # Припускаємо, що повертає ID або None/Exception

    if not deleted_user_id: # Або якщо сервіс повертає False/None при невдачі
        logger.warning(f"Користувача з ID {user_id} не знайдено для видалення (запит від {current_admin.email}).")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Користувача не знайдено для видалення")

    logger.info(f"Користувач ID {user_id} успішно видалений адміністратором {current_admin.email}.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Роутер буде підключений в backend/app/src/api/v1/users/__init__.py
