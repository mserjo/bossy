# backend/app/src/api/v1/dictionaries/user_roles.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління довідником "Ролі Користувачів".

Дозволяє створювати, отримувати, оновлювати та видаляти ролі користувачів.
Доступ до операцій створення, оновлення та видалення обмежений для суперкористувачів.
Перегляд списку та окремих елементів доступний автентифікованим користувачам.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from typing import List # Any вже було видалено, або не було
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.src.api.dependencies import get_api_db_session, get_current_active_superuser, get_current_active_user, paginator
from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.dictionaries.user_roles import UserRoleCreate, UserRoleUpdate, UserRoleResponse
from backend.app.src.services.dictionaries.user_roles import UserRoleService
# from backend.app.src.repositories.dictionaries import UserRoleRepository # Видалено
from backend.app.src.core.pagination import PagedResponse, PageParams
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

router = APIRouter(
    # Префікс /user-roles буде додано в __init__.py батьківського роутера
    # Теги також успадковуються/додаються звідти
)


# Залежність для отримання UserRoleService
async def get_user_role_service(session: AsyncSession = Depends(get_api_db_session)) -> UserRoleService:
    """
    Залежність FastAPI для отримання екземпляра UserRoleService.
    """
    return UserRoleService(db_session=session)  # Використовуємо db_session напряму

# ПРИМІТКА: Реалізація полів `created_by_user_id`/`updated_by_user_id` (якщо вони є в моделі)
# залежить від можливостей базового сервісу `BaseDictionaryService`.
@router.post(
    "/",
    response_model=UserRoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створити нову роль користувача",  # i18n
    description="Дозволяє суперкористувачу створювати нову роль користувача.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Тільки суперюзер
)
async def create_user_role(
        user_role_in: UserRoleCreate,
        service: UserRoleService = Depends(get_user_role_service),
        current_user: UserModel = Depends(get_current_active_superuser)
) -> UserRoleResponse:
    """
    Створює нову роль користувача.
    Доступно тільки суперкористувачам.
    """
    logger.info(
        f"Спроба створення ролі користувача '{user_role_in.name}' (код: {user_role_in.code}) користувачем ID '{current_user.id}'.")
    try:
        # TODO: Перевірити, чи модель UserRole має created_by_user_id і чи BaseDictionaryService це обробляє.
        created_item = await service.create(data=user_role_in)
        return created_item
    except ValueError as e:
        logger.warning(f"Помилка створення ролі '{user_role_in.name}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при створенні ролі '{user_role_in.name}': {e}", exc_info=True)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.get(
    "/{user_role_id}",
    response_model=UserRoleResponse,
    summary="Отримати роль користувача за ID",  # i18n
    description="Дозволяє автентифікованим користувачам отримувати інформацію про конкретну роль користувача.",  # i18n
    dependencies=[Depends(get_current_active_user)]  # Будь-який активний користувач
)
async def get_user_role(
        user_role_id: UUID,
        service: UserRoleService = Depends(get_user_role_service),
) -> UserRoleResponse:
    """
    Отримує роль користувача за її ID.
    Доступно будь-якому автентифікованому користувачеві.
    """
    logger.debug(f"Запит на отримання ролі користувача за ID: {user_role_id}")
    db_item = await service.get_by_id(item_id=user_role_id)
    if not db_item:
        logger.warning(f"Роль користувача з ID '{user_role_id}' не знайдено.")
        # i18n
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Роль користувача не знайдено.")
    return db_item

# ПРИМІТКА: Коректна пагінація залежить від реалізації методу `count_all()`
# в `UserRoleService` (успадкованого від `BaseDictionaryService`).
@router.get(
    "/",
    response_model=PagedResponse[UserRoleResponse],
    summary="Отримати список всіх ролей користувачів",  # i18n
    description="Дозволяє автентифікованим користувачам отримувати сторінковий список всіх ролей користувачів.",  # i18n
    dependencies=[Depends(get_current_active_user)]  # Будь-який активний користувач
)
async def get_all_user_roles(
        page_params: PageParams = Depends(paginator),
        service: UserRoleService = Depends(get_user_role_service),
) -> PagedResponse[UserRoleResponse]:
    """
    Отримує всі ролі користувачів з пагінацією.
    Доступно будь-якому автентифікованому користувачеві.
    """
    logger.debug(
        f"Запит на отримання списку ролей користувачів: сторінка {page_params.page}, розмір {page_params.size}")
    items_page = await service.get_all(skip=page_params.skip, limit=page_params.limit)
    # TODO: Реалізувати метод count_all() в BaseDictionaryService для коректної пагінації.
    total_count = await service.count_all()

    return PagedResponse(
        results=items_page,
        total=total_count,
        page=page_params.page,
        size=page_params.size
    )


@router.put(
    "/{user_role_id}",
    response_model=UserRoleResponse,
    summary="Оновити роль користувача",  # i18n
    description="Дозволяє суперкористувачу оновлювати існуючу роль користувача.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Тільки суперюзер
)
async def update_user_role(
        user_role_id: UUID,
        user_role_in: UserRoleUpdate,
        service: UserRoleService = Depends(get_user_role_service),
        current_user: UserModel = Depends(get_current_active_superuser)
) -> UserRoleResponse:
    """
    Оновлює існуючу роль користувача.
    Доступно тільки суперкористувачам.
    TODO: Додати перевірку, чи не змінюються системні ролі (наприклад, SUPERUSER), якщо це заборонено.
    """
# ПРИМІТКА: Важливо реалізувати перевірку, щоб запобігти небажаним змінам
# системних ролей, як зазначено в TODO.
    logger.info(f"Спроба оновлення ролі користувача ID '{user_role_id}' користувачем ID '{current_user.id}'.")
    try:
        # TODO: Перевірити, чи модель UserRole має updated_by_user_id і чи BaseDictionaryService це обробляє.
        updated_item = await service.update(item_id=user_role_id, data=user_role_in)
        if not updated_item:
            logger.warning(f"Роль користувача з ID '{user_role_id}' не знайдено для оновлення.")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Роль користувача не знайдено.")
        return updated_item
    except ValueError as e:
        logger.warning(f"Помилка оновлення ролі ID '{user_role_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при оновленні ролі ID '{user_role_id}': {e}", exc_info=True)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.delete(
    "/{user_role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити роль користувача",  # i18n
    description="Дозволяє суперкористувачу видалити роль користувача. Виконується жорстке видалення.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Тільки суперюзер
)
async def delete_user_role(
        user_role_id: UUID,
        service: UserRoleService = Depends(get_user_role_service),
        current_user: UserModel = Depends(get_current_active_superuser)
):
    """
    Видаляє роль користувача за її ID.
    Доступно тільки суперкористувачам.
    TODO: Додати перевірку, чи не видаляються системні ролі (наприклад, SUPERUSER, ADMIN, USER), якщо це заборонено.
    """
# ПРИМІТКА: Необхідно реалізувати перевірку, щоб уникнути видалення
# критично важливих системних ролей, як зазначено в TODO.
    logger.info(f"Спроба видалення ролі користувача ID '{user_role_id}' користувачем ID '{current_user.id}'.")
    try:
        deleted = await service.delete(item_id=user_role_id)
        if not deleted:
            logger.warning(f"Роль користувача з ID '{user_role_id}' не знайдено для видалення.")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Роль користувача не знайдено.")
    except ValueError as e:  # Наприклад, якщо роль використовується
        logger.warning(f"Помилка видалення ролі ID '{user_role_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при видаленні ролі ID '{user_role_id}': {e}", exc_info=True)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")

    return None


logger.info(f"Роутер для довідника '{router.prefix}' (Ролі Користувачів) визначено.")
