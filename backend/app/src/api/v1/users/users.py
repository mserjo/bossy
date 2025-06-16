# backend/app/src/api/v1/users/users.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління користувачами на рівні системи (для суперкористувачів).

Надає CRUD-операції для системних адміністраторів (суперкористувачів)
для управління всіма обліковими записами користувачів.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from typing import List, TypeVar  # Optional, Any, Dict не використовуються, TypeVar для PagedResponse
from uuid import UUID  # user_id тепер UUID
from fastapi import APIRouter, Depends, HTTPException, status # Query видалено
from sqlalchemy.ext.asyncio import AsyncSession  # Не використовується прямо, якщо сесія інкапсульована

# Повні шляхи імпорту
from backend.app.src.api.dependencies import get_api_db_session, get_current_active_superuser, get_user_service, \
    paginator
from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.auth.user import (
    UserResponse,
    UserCreateSuperuser,  # Спеціальна схема для створення користувача суперюзером
    UserUpdateSuperuser  # Спеціальна схема для оновлення користувача суперюзером
)
from backend.app.src.core.pagination import PagedResponse, PageParams  # Використовуємо з core.pagination
from backend.app.src.services.auth.user import UserService
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings as global_settings  # Для DEBUG тощо

router = APIRouter(
    dependencies=[Depends(get_current_active_superuser)]  # Всі ендпоінти тут вимагають прав суперкористувача
)


@router.post(
    "/",
    response_model=UserResponse,  # Або спеціальна UserSuperAdminView, якщо є відмінності
    status_code=status.HTTP_201_CREATED,
    summary="Створення нового користувача (Суперюзер)",  # i18n
    description="Дозволяє суперюзеру створити нового користувача в системі з розширеними налаштуваннями."  # i18n
)
# ПРИМІТКА: Успішне створення користувача залежить від реалізації методу
# `create_user_admin` в `UserService`, який має обробляти всі необхідні
# перевірки та призначення атрибутів згідно схеми `UserCreateSuperuser`.
async def create_user_by_superuser(
        user_in: UserCreateSuperuser,  # Схема, що дозволяє встановлювати ролі, тип, is_active, is_superuser
        current_superuser: UserModel = Depends(get_current_active_superuser),  # Для аудиту та перевірок
        user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    """
    Створює нового користувача з 지정ними атрибутами. Доступно тільки суперюзерам.
    `UserService.create_user_admin` має обробляти унікальність email/username та інші правила.
    """
    logger.info(f"Суперкористувач ID '{current_superuser.id}' намагається створити користувача: {user_in.email}")
    try:
        # TODO: Реалізувати або адаптувати `UserService.create_user` або створити `UserService.create_user_admin`
        #  який приймає UserCreateSuperuser та creator_id (опціонально для аудиту).
        #  Цей метод сервісу має обробляти хешування пароля, перевірку унікальності,
        #  призначення ролей/типу з `user_in.role_codes` та `user_in.user_type_code`.
        created_user_orm = await user_service.create_user_admin(  # Припускаємо існування такого методу
            user_create_data=user_in,
            creator_id=current_superuser.id
        )
        if not created_user_orm:  # Малоймовірно, якщо сервіс кидає винятки
            # i18n
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Не вдалося створити користувача.")

        logger.info(
            f"Користувача '{created_user_orm.username}' (ID: {created_user_orm.id}) успішно створено суперкористувачем ID '{current_superuser.id}'.")
        return UserResponse.model_validate(created_user_orm)  # Pydantic v2
    except ValueError as e:  # Помилки валідації з сервісу (напр., дублікат email/username)
        logger.warning(f"Помилка створення користувача '{user_in.email}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при створенні користувача '{user_in.email}': {e}",
                     exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Внутрішня помилка сервера при створенні користувача.")


@router.get(
    "/",
    response_model=PagedResponse[UserResponse],  # Або UserSuperAdminView
    summary="Отримання списку користувачів (Суперюзер)",  # i18n
    description="Повертає список всіх користувачів системи з пагінацією. Доступно тільки суперюзерам."  # i18n
)
# ПРИМІТКА: Повноцінна реалізація цього ендпоінта вимагає додавання
# можливостей фільтрації та сортування в метод `list_users_paginated`
# сервісу `UserService`, як зазначено в TODO.
async def read_users_by_superuser(  # Перейменовано для уникнення конфлікту
        page_params: PageParams = Depends(paginator),  # Залежність для пагінації
        # TODO: Додати фільтри (наприклад, за роллю, типом, статусом активності) як Query параметри
        user_service: UserService = Depends(get_user_service)
) -> PagedResponse[UserResponse]:
    """
    Отримує список користувачів з пагінацією.
    Дозволяє фільтрацію за певними критеріями (буде додано за потреби).
    """
    logger.info(f"Запит списку користувачів: сторінка {page_params.page}, розмір {page_params.size}")
    # TODO: UserService.list_users має повертати кортеж (items, total_count) або PagedResponse.
    #  Припускаємо, що він повертає (List[UserModel], int)
    users_orm, total_users = await user_service.list_users_paginated(
        skip=page_params.skip,
        limit=page_params.limit
        # TODO: Передати сюди параметри фільтрації та сортування
    )

    return PagedResponse[UserResponse](
        total=total_users,
        page=page_params.page,
        size=page_params.size,
        results=[UserResponse.model_validate(user) for user in users_orm]  # Pydantic v2
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,  # Або UserSuperAdminView
    summary="Отримання інформації про користувача за ID (Суперюзер)",  # i18n
    description="Повертає детальну інформацію про конкретного користувача за його ID. Доступно тільки суперюзерам."
    # i18n
)
async def read_user_by_id_superuser(  # Перейменовано
        user_id: UUID,  # ID користувача тепер UUID
        user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    """
    Отримує інформацію про користувача за його ID.
    """
    logger.debug(f"Запит інформації про користувача за ID: {user_id}")
    # UserService.get_user_by_id має повертати ORM модель або Pydantic схему
    user_response_schema = await user_service.get_user_by_id(user_id=user_id,
                                                             include_relations=True)  # Припускаємо, що get_user_by_id повертає схему
    if not user_response_schema:
        logger.warning(f"Користувача з ID '{user_id}' не знайдено.")
        # i18n
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Користувача з ID {user_id} не знайдено.")
    return user_response_schema


@router.put(
    "/{user_id}",
    response_model=UserResponse,  # Або UserSuperAdminView
    summary="Оновлення інформації про користувача (Суперюзер)",  # i18n
    description="Дозволяє суперюзеру оновити дані існуючого користувача, включаючи роль, статус тощо."  # i18n
)
async def update_user_by_superuser(
        user_id: UUID,  # ID користувача тепер UUID
        user_in: UserUpdateSuperuser,  # Схема для оновлення суперюзером
        current_superuser: UserModel = Depends(get_current_active_superuser),  # Для аудиту
        user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    """
    Оновлює дані користувача. Доступно тільки суперюзерам.
    Дозволяє змінювати email, ім'я, роль, статус активації, прапорець суперкористувача.
    """
    logger.info(
        f"Суперкористувач ID '{current_superuser.id}' намагається оновити користувача ID '{user_id}'. Дані: {user_in.model_dump(exclude_unset=True)}")
    try:
        # UserService.update_user має приймати user_id, схему оновлення та прапорець is_admin_update=True
        updated_user_orm = await user_service.update_user(
            user_id=user_id,
            user_update_data=user_in,  # UserUpdateSuperuser є підкласом UserUpdate або сумісний
            # current_user_id=current_superuser.id, # Якщо сервіс потребує аудиту
            is_admin_update=True  # Вказує, що це оновлення з розширеними правами
        )
        if not updated_user_orm:  # Малоймовірно, якщо сервіс кидає винятки
            logger.error(f"Оновлення користувача ID '{user_id}' повернуло None з сервісу.")
            # i18n
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Не вдалося оновити користувача.")

        logger.info(f"Користувача ID '{user_id}' успішно оновлено суперкористувачем ID '{current_superuser.id}'.")
        return UserResponse.model_validate(updated_user_orm)  # Pydantic v2
    except ValueError as e:  # Обробка помилок валідації з сервісного шару
        logger.warning(f"Помилка оновлення користувача ID '{user_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except PermissionError as e:  # Якщо сервіс кидає PermissionError (наприклад, спроба зняти останнього суперюзера)
        logger.warning(f"Спроба неавторизованого оновлення користувача ID '{user_id}': {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при оновленні користувача ID '{user_id}': {e}",
                     exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Внутрішня помилка сервера при оновленні користувача.")


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення користувача (Суперюзер)",  # i18n
    description="Дозволяє суперюзеру видалити користувача. Тип видалення (м'яке/жорстке) визначається сервісом."  # i18n
)
async def delete_user_by_superuser(
        user_id: UUID,  # ID користувача тепер UUID
        current_superuser: UserModel = Depends(get_current_active_superuser),
        user_service: UserService = Depends(get_user_service)
):
    """
    Видаляє користувача. Суперюзер не може видалити сам себе через цей ендпоінт.
    """
    logger.info(f"Суперкористувач ID '{current_superuser.id}' намагається видалити користувача ID '{user_id}'.")
    if user_id == current_superuser.id:
        logger.warning(f"Суперкористувач ID '{current_superuser.id}' намагається видалити сам себе. Заборонено.")
        # i18n
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Суперюзер не може видалити сам себе.")

    try:
        # TODO: UserService.delete_user має існувати та обробляти логіку видалення (м'яке/жорстке).
        #  Він може повертати bool або кидати виняток, якщо користувача не знайдено.
        success = await user_service.delete_user_admin(user_id_to_delete=user_id,
                                                       current_user_id=current_superuser.id)  # Припускаємо такий метод
        if not success:
            # Це може статися, якщо користувач не знайдений, або сервіс має внутрішні перевірки, що запобігли видаленню.
            logger.warning(f"Не вдалося видалити користувача ID '{user_id}' (сервіс повернув False).")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Користувача з ID {user_id} не знайдено або не вдалося видалити.")
    except ValueError as e:  # Наприклад, якщо сервіс кидає помилку (користувач не знайдений)
        logger.warning(f"Помилка видалення користувача ID '{user_id}': {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))  # i18n
    except PermissionError as e:  # Якщо сервіс кидає помилку дозволу (наприклад, спроба видалити захищеного користувача)
        logger.warning(f"Заборона видалення користувача ID '{user_id}': {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при видаленні користувача ID '{user_id}': {e}",
                     exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Внутрішня помилка сервера при видаленні користувача.")

    # Успішна відповідь HTTP 204 No Content не повинна мати тіла
    return None


logger.info(f"Роутер для управління користувачами суперкористувачем визначено.")
