# backend/app/src/api/v1/dictionaries/user_types.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління довідником "Типи Користувачів".

Дозволяє створювати, отримувати, оновлювати та видаляти типи користувачів.
Доступ до операцій створення, оновлення та видалення обмежений для суперкористувачів.
Перегляд списку та окремих елементів доступний автентифікованим користувачам.
"""
from typing import List  # Any не використовується, можна прибрати
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# Повні шляхи імпорту
from backend.app.src.api.dependencies import get_api_db_session, get_current_active_superuser, get_current_active_user, \
    paginator
from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.dictionaries.user_types import UserTypeCreate, UserTypeUpdate, UserTypeResponse
from backend.app.src.services.dictionaries.user_types import UserTypeService
# from backend.app.src.repositories.dictionaries import UserTypeRepository # Видалено
from backend.app.src.core.pagination import PagedResponse, PageParams
from backend.app.src.config.logging import logger  # Централізований логер

router = APIRouter(
    # Префікс /user-types буде додано в __init__.py батьківського роутера
    # Теги також успадковуються/додаються звідти
)


# Залежність для отримання UserTypeService
async def get_user_type_service(session: AsyncSession = Depends(get_api_db_session)) -> UserTypeService:
    """
    Залежність FastAPI для отримання екземпляра UserTypeService.
    """
    return UserTypeService(db_session=session)  # Використовуємо db_session напряму


@router.post(
    "/",
    response_model=UserTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створити новий тип користувача",  # i18n
    description="Дозволяє суперкористувачу створювати новий тип користувача.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Тільки суперюзер
)
async def create_user_type(
        user_type_in: UserTypeCreate,
        service: UserTypeService = Depends(get_user_type_service),
        current_user: UserModel = Depends(get_current_active_superuser)
) -> UserTypeResponse:
    """
    Створює новий тип користувача.
    Доступно тільки суперкористувачам.
    """
    logger.info(
        f"Спроба створення типу користувача '{user_type_in.name}' (код: {user_type_in.code}) користувачем ID '{current_user.id}'.")
    try:
        # TODO: Перевірити, чи модель UserType має created_by_user_id і чи BaseDictionaryService це обробляє.
        created_item = await service.create(data=user_type_in)
        return created_item
    except ValueError as e:
        logger.warning(f"Помилка створення типу користувача '{user_type_in.name}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при створенні '{user_type_in.name}': {e}", exc_info=True)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.get(
    "/{user_type_id}",
    response_model=UserTypeResponse,
    summary="Отримати тип користувача за ID",  # i18n
    description="Дозволяє автентифікованим користувачам отримувати інформацію про конкретний тип користувача.",  # i18n
    dependencies=[Depends(get_current_active_user)]  # Будь-який активний користувач
)
async def get_user_type(
        user_type_id: UUID,
        service: UserTypeService = Depends(get_user_type_service),
) -> UserTypeResponse:
    """
    Отримує тип користувача за його ID.
    Доступно будь-якому автентифікованому користувачеві.
    """
    logger.debug(f"Запит на отримання типу користувача за ID: {user_type_id}")
    db_item = await service.get_by_id(item_id=user_type_id)
    if not db_item:
        logger.warning(f"Тип користувача з ID '{user_type_id}' не знайдено.")
        # i18n
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип користувача не знайдено.")
    return db_item


@router.get(
    "/",
    response_model=PagedResponse[UserTypeResponse],
    summary="Отримати список всіх типів користувачів",  # i18n
    description="Дозволяє автентифікованим користувачам отримувати сторінковий список всіх типів користувачів.",  # i18n
    dependencies=[Depends(get_current_active_user)]  # Будь-який активний користувач
)
async def get_all_user_types(
        page_params: PageParams = Depends(paginator),
        service: UserTypeService = Depends(get_user_type_service),
) -> PagedResponse[UserTypeResponse]:
    """
    Отримує всі типи користувачів з пагінацією.
    Доступно будь-якому автентифікованому користувачеві.
    """
    logger.debug(
        f"Запит на отримання списку типів користувачів: сторінка {page_params.page}, розмір {page_params.size}")
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
    "/{user_type_id}",
    response_model=UserTypeResponse,
    summary="Оновити тип користувача",  # i18n
    description="Дозволяє суперкористувачу оновлювати існуючий тип користувача.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Тільки суперюзер
)
async def update_user_type(
        user_type_id: UUID,
        user_type_in: UserTypeUpdate,
        service: UserTypeService = Depends(get_user_type_service),
        current_user: UserModel = Depends(get_current_active_superuser)
) -> UserTypeResponse:
    """
    Оновлює існуючий тип користувача.
    Доступно тільки суперкористувачам.
    TODO: Додати перевірку, чи не змінюються системні типи (наприклад, SUPERUSER_TYPE), якщо це заборонено.
    """
    logger.info(f"Спроба оновлення типу користувача ID '{user_type_id}' користувачем ID '{current_user.id}'.")
    try:
        # TODO: Перевірити, чи модель UserType має updated_by_user_id і чи BaseDictionaryService це обробляє.
        updated_item = await service.update(item_id=user_type_id, data=user_type_in)
        if not updated_item:
            logger.warning(f"Тип користувача з ID '{user_type_id}' не знайдено для оновлення.")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип користувача не знайдено.")
        return updated_item
    except ValueError as e:
        logger.warning(f"Помилка оновлення типу користувача ID '{user_type_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при оновленні типу ID '{user_type_id}': {e}", exc_info=True)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.delete(
    "/{user_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити тип користувача",  # i18n
    description="Дозволяє суперкористувачу видалити тип користувача. Виконується жорстке видалення.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Тільки суперюзер
)
async def delete_user_type(
        user_type_id: UUID,
        service: UserTypeService = Depends(get_user_type_service),
        current_user: UserModel = Depends(get_current_active_superuser)
):
    """
    Видаляє тип користувача за його ID.
    Доступно тільки суперкористувачам.
    TODO: Додати перевірку, чи не видаляються системні типи (наприклад, SUPERUSER_TYPE), якщо це заборонено.
    """
    logger.info(f"Спроба видалення типу користувача ID '{user_type_id}' користувачем ID '{current_user.id}'.")
    try:
        deleted = await service.delete(item_id=user_type_id)
        if not deleted:
            logger.warning(f"Тип користувача з ID '{user_type_id}' не знайдено для видалення.")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип користувача не знайдено.")
    except ValueError as e:  # Наприклад, якщо об'єкт використовується
        logger.warning(f"Помилка видалення типу користувача ID '{user_type_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при видаленні типу ID '{user_type_id}': {e}", exc_info=True)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")

    return None


logger.info(f"Роутер для довідника '{router.prefix}' (Типи Користувачів) визначено.")
