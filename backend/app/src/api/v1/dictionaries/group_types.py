# backend/app/src/api/v1/dictionaries/group_types.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління довідником "Типи Груп".

Дозволяє створювати, отримувати, оновлювати та видаляти типи груп.
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
from backend.app.src.schemas.dictionaries.group_types import GroupTypeCreate, GroupTypeUpdate, GroupTypeResponse
from backend.app.src.services.dictionaries.group_types import GroupTypeService
# from backend.app.src.repositories.dictionaries import GroupTypeRepository # Видалено
from backend.app.src.core.pagination import PagedResponse, PageParams
from backend.app.src.config.logging import logger  # Централізований логер

router = APIRouter(
    # Префікс /group-types буде додано в __init__.py батьківського роутера
    # Теги також успадковуються/додаються звідти
)


# Залежність для отримання GroupTypeService
async def get_group_type_service(session: AsyncSession = Depends(get_api_db_session)) -> GroupTypeService:
    """
    Залежність FastAPI для отримання екземпляра GroupTypeService.
    """
    return GroupTypeService(db_session=session)  # Використовуємо db_session напряму


@router.post(
    "/",
    response_model=GroupTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створити новий тип групи",  # i18n
    description="Дозволяє суперкористувачу створювати новий тип групи.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Тільки суперюзер
)
async def create_group_type(
        group_type_in: GroupTypeCreate,
        service: GroupTypeService = Depends(get_group_type_service),
        current_user: UserModel = Depends(get_current_active_superuser)
) -> GroupTypeResponse:
    """
    Створює новий тип групи.
    Доступно тільки суперкористувачам.
    """
    logger.info(f"Спроба створення типу групи '{group_type_in.name}' користувачем ID '{current_user.id}'.")
    try:
        # TODO: Перевірити, чи модель GroupType має created_by_user_id і чи BaseDictionaryService це обробляє.
        created_item = await service.create(data=group_type_in)
        return created_item
    except ValueError as e:
        logger.warning(f"Помилка створення типу групи '{group_type_in.name}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при створенні '{group_type_in.name}': {e}", exc_info=True)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.get(
    "/{group_type_id}",
    response_model=GroupTypeResponse,
    summary="Отримати тип групи за ID",  # i18n
    description="Дозволяє автентифікованим користувачам отримувати інформацію про конкретний тип групи.",  # i18n
    dependencies=[Depends(get_current_active_user)]  # Будь-який активний користувач
)
async def get_group_type(
        group_type_id: UUID,
        service: GroupTypeService = Depends(get_group_type_service),
) -> GroupTypeResponse:
    """
    Отримує тип групи за його ID.
    Доступно будь-якому автентифікованому користувачеві.
    """
    logger.debug(f"Запит на отримання типу групи за ID: {group_type_id}")
    db_item = await service.get_by_id(item_id=group_type_id)
    if not db_item:
        logger.warning(f"Тип групи з ID '{group_type_id}' не знайдено.")
        # i18n
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип групи не знайдено.")
    return db_item


@router.get(
    "/",
    response_model=PagedResponse[GroupTypeResponse],
    summary="Отримати список всіх типів груп",  # i18n
    description="Дозволяє автентифікованим користувачам отримувати сторінковий список всіх типів груп.",  # i18n
    dependencies=[Depends(get_current_active_user)]  # Будь-який активний користувач
)
async def get_all_group_types(
        page_params: PageParams = Depends(paginator),
        service: GroupTypeService = Depends(get_group_type_service),
) -> PagedResponse[GroupTypeResponse]:
    """
    Отримує всі типи груп з пагінацією.
    Доступно будь-якому автентифікованому користувачеві.
    """
    logger.debug(f"Запит на отримання списку типів груп: сторінка {page_params.page}, розмір {page_params.size}")
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
    "/{group_type_id}",
    response_model=GroupTypeResponse,
    summary="Оновити тип групи",  # i18n
    description="Дозволяє суперкористувачу оновлювати існуючий тип групи.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Тільки суперюзер
)
async def update_group_type(
        group_type_id: UUID,
        group_type_in: GroupTypeUpdate,
        service: GroupTypeService = Depends(get_group_type_service),
        current_user: UserModel = Depends(get_current_active_superuser)
) -> GroupTypeResponse:
    """
    Оновлює існуючий тип групи.
    Доступно тільки суперкористувачам.
    """
    logger.info(f"Спроба оновлення типу групи ID '{group_type_id}' користувачем ID '{current_user.id}'.")
    try:
        # TODO: Перевірити, чи модель GroupType має updated_by_user_id і чи BaseDictionaryService це обробляє.
        updated_item = await service.update(item_id=group_type_id, data=group_type_in)
        if not updated_item:
            logger.warning(f"Тип групи з ID '{group_type_id}' не знайдено для оновлення.")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип групи не знайдено.")
        return updated_item
    except ValueError as e:
        logger.warning(f"Помилка оновлення типу групи ID '{group_type_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при оновленні ID '{group_type_id}': {e}", exc_info=True)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.delete(
    "/{group_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити тип групи",  # i18n
    description="Дозволяє суперкористувачу видалити тип групи. Виконується жорстке видалення.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Тільки суперюзер
)
async def delete_group_type(
        group_type_id: UUID,
        service: GroupTypeService = Depends(get_group_type_service),
        current_user: UserModel = Depends(get_current_active_superuser)
):
    """
    Видаляє тип групи за його ID.
    Доступно тільки суперкористувачам.
    """
    logger.info(f"Спроба видалення типу групи ID '{group_type_id}' користувачем ID '{current_user.id}'.")
    try:
        deleted = await service.delete(item_id=group_type_id)
        if not deleted:
            logger.warning(f"Тип групи з ID '{group_type_id}' не знайдено для видалення.")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип групи не знайдено.")
    except ValueError as e:  # Наприклад, якщо об'єкт використовується
        logger.warning(f"Помилка видалення типу групи ID '{group_type_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при видаленні ID '{group_type_id}': {e}", exc_info=True)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")

    return None


# TODO: Розглянути, чи потрібен get_group_type_by_code, якщо 'code' є ключовим для цієї сутності.
# BaseDictionaryService вже має get_by_code.

logger.info(f"Роутер для довідника '{router.prefix}' (Типи Груп) визначено.")
