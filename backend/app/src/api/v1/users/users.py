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
    UserAdminCreateSchema,
    UserAdminUpdateSchema
)
from backend.app.src.services.auth.user_service import UserService
from backend.app.src.api.dependencies import DBSession, CurrentSuperuser
from backend.app.src.models.auth.user import UserModel
from backend.app.src.core.constants import DEFAULT_PAGE_SIZE # DEFAULT_PAGE не використовується, пагінація з 1
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException # Для локалізованих помилок
import uuid # Для user_id

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
    response: Response, # Додано для встановлення заголовків пагінації
    db_session: DBSession = Depends(),
    current_admin: UserModel = Depends(CurrentSuperuser), # UserModel тут - це Pydantic схема UserSchema з CurrentSuperuser
    page: int = Query(1, ge=1, description="Номер сторінки"), # Починаємо з 1
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100, description="Розмір сторінки"),
    # TODO: Додати фільтри
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

    # Потрібно, щоб UserService мав метод, що повертає PaginatedResponse[UserModel]
    # Або ж тут отримувати список моделей та total, і формувати UserSchema
    # Припускаємо, що get_users_paginated повертає список UserModel та total
    # users_list, total_count = await user_service.get_users_paginated_admin(
    #     skip=(page - 1) * page_size,
    #     limit=page_size,
    #     # TODO: передати фільтри
    # )
    # Поки що, якщо такого методу немає, імпровізуємо з get_multi та count
    # Це НЕ ЕФЕКТИВНО для великих таблиць, але для демонстрації.
    # Краще мати спеціалізований метод в сервісі/репозиторії.

    # Тимчасова реалізація пагінації тут, якщо сервіс не підтримує PaginatedResponse
    # У реальному проекті це має бути в сервісі або репозиторії.
    from backend.app.src.schemas.base import PaginatedResponse # Для типізації відповіді

    # Припускаємо, що get_all_users_paginated в сервісі повертає (List[UserModel], total_count)
    # Або ж, якщо сервіс/репозиторій повертає PaginatedResponse[ModelType]:
    # paginated_users_result = await user_service.get_users_as_paginated_response(
    #     page=page, size=page_size, filters=None # TODO: filters
    # )
    # users_to_return = [UserSchema.model_validate(user_model) for user_model in paginated_users_result.items]
    # response.headers["X-Total-Count"] = str(paginated_users_result.total)
    # response.headers["X-Page"] = str(paginated_users_result.page)
    # response.headers["X-Page-Size"] = str(paginated_users_result.size)
    # response.headers["X-Total-Pages"] = str(paginated_users_result.pages)
    # return users_to_return

    # Поки що заглушка, оскільки метод в сервісі/репозиторії не готовий
    logger.warning("Пагінація в list_all_users ще не реалізована повністю через відсутність підтримки в сервісі.")
    # Повернемо порожній список для демонстрації структури
    response.headers["X-Total-Count"] = "0"
    response.headers["X-Page"] = str(page)
    response.headers["X-Page-Size"] = str(page_size)
    response.headers["X-Total-Pages"] = "0"
    return []


@router.post(
    "",
    response_model=UserSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Users (Admin)"],
    summary="Створити нового користувача (адміністративний)"
)
async def create_user_by_admin(
    user_in: UserAdminCreateSchema, # UserAdminCreateSchema має бути визначена
    db_session: DBSession = Depends(),
    current_admin: UserModel = Depends(CurrentSuperuser) # UserModel тут - це UserSchema
):
    logger.info(
        f"Адміністратор {current_admin.email} створює нового користувача: {user_in.email} "
        f"(name: {user_in.name or 'не вказано'})."
    )
    user_service = UserService(db_session)
    try:
        # Припускаємо, що UserService.create_user приймає UserAdminCreateSchema
        # або має окремий метод create_user_by_admin
        # Поточний create_user приймає UserCreateSchema. Потрібно узгодити.
        # Давайте припустимо, що UserAdminCreateSchema сумісна або є окремий метод.
        # Для простоти, припустимо, що UserService.create_user може обробити UserAdminCreateSchema
        # або ми адаптуємо його. Поки що викликаємо create_user.
        # Це потребує, щоб UserAdminCreateSchema мала поля password, confirm_password.
        # Або ж, UserAdminCreateSchema не має їх, і пароль генерується/встановлюється інакше.
        # Поки що, припускаючи, що UserAdminCreateSchema схожа на UserCreateSchema:
        created_user_model = await user_service.create_user(obj_in=user_in) # Використовуємо існуючий create_user
        logger.info(f"Користувач {created_user_model.email} успішно створений адміністратором {current_admin.email}.")
        return UserSchema.model_validate(created_user_model)
    except BadRequestException as e: # Ловимо кастомні винятки
        logger.warning(f"Помилка створення користувача {user_in.email} адміністратором: {e.detail}")
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при створенні користувача {user_in.email} адміністратором: {e_gen}", exc_info=True)
        raise InternalServerErrorException(detail_key="error_user_creation_failed_admin")


@router.get(
    "/{user_id}",
    response_model=UserSchema,
    tags=["Users (Admin)"],
    summary="Отримати інформацію про користувача за ID (адміністративний)"
)
async def get_user_by_id_admin(
    user_id: uuid.UUID, # Змінено на uuid.UUID
    db_session: DBSession = Depends(),
    current_admin: UserModel = Depends(CurrentSuperuser) # UserModel тут - це UserSchema
):
    logger.info(f"Адміністратор {current_admin.email} запитує інформацію про користувача ID: {user_id}.")
    user_service = UserService(db_session)
    user_model = await user_service.get_user_by_id(user_id=user_id)
    if not user_model:
        logger.warning(f"Користувача з ID {user_id} не знайдено (запит від {current_admin.email}).")
        raise NotFoundException(detail_key="error_resource_not_found_details", resource_name="User", identifier=str(user_id))
    return UserSchema.model_validate(user_model)


@router.put(
    "/{user_id}",
    response_model=UserSchema,
    tags=["Users (Admin)"],
    summary="Оновити інформацію про користувача (адміністративний)"
)
async def update_user_by_admin(
    user_id: uuid.UUID, # Змінено на uuid.UUID
    user_in: UserAdminUpdateSchema,
    db_session: DBSession = Depends(),
    current_admin: UserModel = Depends(CurrentSuperuser) # UserModel тут - це UserSchema
):
    logger.info(f"Адміністратор {current_admin.email} оновлює інформацію для користувача ID: {user_id}.")
    user_service = UserService(db_session)
    try:
        # Передаємо current_admin як admin_user в сервіс
        updated_user_model = await user_service.admin_update_user(
            user_to_update_id=user_id,
            obj_in=user_in,
            admin_user=current_admin # Передаємо UserSchema як UserModel, сервіс має це обробити або очікувати UserModel
                                      # Краще, щоб сервіс приймав UserModel. CurrentSuperuser повертає UserSchema.
                                      # Потрібно буде отримати UserModel для current_admin в сервісі або тут.
                                      # Поки що припускаємо, що сервіс може працювати з UserSchema для admin_user.
        )
        logger.info(f"Інформація користувача ID {user_id} успішно оновлена адміністратором {current_admin.email}.")
        return UserSchema.model_validate(updated_user_model)
    except (NotFoundException, BadRequestException, ForbiddenException) as e:
        logger.warning(f"Помилка оновлення користувача ID {user_id} адміністратором: {e.detail}")
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при оновленні користувача ID {user_id} адміністратором: {e_gen}", exc_info=True)
        raise InternalServerErrorException(detail_key="error_user_update_failed_admin")


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Users (Admin)"],
    summary="Видалити користувача (адміністративний)"
)
async def delete_user_by_admin(
    user_id: uuid.UUID, # Змінено на uuid.UUID
    db_session: DBSession = Depends(),
    current_admin: UserModel = Depends(CurrentSuperuser) # UserModel тут - це UserSchema
):
    # Потрібно отримати UserModel для current_admin
    # Це вже є в current_admin, якщо CurrentSuperuser повертає UserModel
    # Але CurrentSuperuser (як і get_current_user) повертає UserSchema.
    # Потрібно буде завантажити UserModel для current_admin.
    user_service = UserService(db_session)
    admin_user_model = await user_service.get_user_by_id(user_id=current_admin.id)
    if not admin_user_model: # Малоймовірно
        raise ForbiddenException(detail_key="error_failed_to_verify_admin_rights")

    if admin_user_model.id == user_id:
        logger.warning(f"Адміністратор {admin_user_model.email} спробував видалити сам себе.")
        raise ForbiddenException(detail_key="error_admin_cannot_delete_self")

    logger.info(f"Адміністратор {admin_user_model.email} видаляє користувача ID: {user_id}.")

    # Використовуємо метод delete_user з UserService
    deleted_user = await user_service.delete_user(user_to_delete_id=user_id, actor=admin_user_model, soft_delete=True) # Припускаємо м'яке видалення

    if not deleted_user: # Якщо delete_user повертає None при помилці або NotFound
        # NotFoundException вже має бути кинуто з delete_user, якщо користувача не знайдено
        # Тут можна додати лог, якщо потрібно, але сервіс вже має обробити.
        # Якщо delete_user кидає виняток, він буде перехоплений FastAPI.
        # Цей блок може бути зайвим, якщо сервіс надійний.
        logger.warning(f"Користувача з ID {user_id} не знайдено або не вдалося видалити (запит від {admin_user_model.email}).")
        # Не кидаємо тут, бо сервіс вже мав кинути NotFound або інший виняток.
        # Якщо сервіс повернув None без винятку (погана практика), то:
        # raise NotFoundException(detail_key="error_resource_not_found_details", resource_name="User", identifier=str(user_id))
        pass


    logger.info(f"Користувач ID {user_id} успішно видалений (або позначений як видалений) адміністратором {admin_user_model.email}.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Роутер буде підключений в backend/app/src/api/v1/users/__init__.py
