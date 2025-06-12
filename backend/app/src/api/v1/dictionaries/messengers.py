# backend/app/src/api/v1/dictionaries/messengers.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління довідником "Платформи Месенджерів".

Дозволяє створювати, отримувати, оновлювати та видаляти платформи месенджерів.
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
from backend.app.src.schemas.dictionaries.messengers import MessengerPlatformCreate, MessengerPlatformUpdate, \
    MessengerPlatformResponse
from backend.app.src.services.dictionaries.messengers import MessengerPlatformService
# from backend.app.src.repositories.dictionaries import MessengerPlatformRepository # Видалено
from backend.app.src.core.pagination import PagedResponse, PageParams
from backend.app.src.config.logging import logger  # Централізований логер

router = APIRouter(
    # Префікс /messenger-platforms буде додано в __init__.py батьківського роутера
    # Теги також успадковуються/додаються звідти
)


# Залежність для отримання MessengerPlatformService
async def get_messenger_platform_service(
        session: AsyncSession = Depends(get_api_db_session)) -> MessengerPlatformService:
    """
    Залежність FastAPI для отримання екземпляра MessengerPlatformService.
    """
    return MessengerPlatformService(db_session=session)  # Використовуємо db_session напряму


@router.post(
    "/",
    response_model=MessengerPlatformResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створити нову платформу месенджера",  # i18n
    description="Дозволяє суперкористувачу створювати нову платформу месенджера.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Тільки суперюзер
)
async def create_messenger_platform(
        messenger_platform_in: MessengerPlatformCreate,
        service: MessengerPlatformService = Depends(get_messenger_platform_service),
        current_user: UserModel = Depends(get_current_active_superuser)
) -> MessengerPlatformResponse:
    """
    Створює нову платформу месенджера.
    Доступно тільки суперкористувачам.
    """
    logger.info(
        f"Спроба створення платформи месенджера '{messenger_platform_in.name}' користувачем ID '{current_user.id}'.")
    try:
        # TODO: Перевірити, чи модель MessengerPlatform має created_by_user_id і чи BaseDictionaryService це обробляє.
        created_item = await service.create(data=messenger_platform_in)
        return created_item
    except ValueError as e:
        logger.warning(f"Помилка створення платформи '{messenger_platform_in.name}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при створенні '{messenger_platform_in.name}': {e}", exc_info=True)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.get(
    "/{messenger_platform_id}",
    response_model=MessengerPlatformResponse,
    summary="Отримати платформу месенджера за ID",  # i18n
    description="Дозволяє автентифікованим користувачам отримувати інформацію про конкретну платформу месенджера.",
    # i18n
    dependencies=[Depends(get_current_active_user)]  # Будь-який активний користувач
)
async def get_messenger_platform(
        messenger_platform_id: UUID,
        service: MessengerPlatformService = Depends(get_messenger_platform_service),
) -> MessengerPlatformResponse:
    """
    Отримує платформу месенджера за її ID.
    Доступно будь-якому автентифікованому користувачеві.
    """
    logger.debug(f"Запит на отримання платформи месенджера за ID: {messenger_platform_id}")
    db_item = await service.get_by_id(item_id=messenger_platform_id)
    if not db_item:
        logger.warning(f"Платформу месенджера з ID '{messenger_platform_id}' не знайдено.")
        # i18n
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Платформу месенджера не знайдено.")
    return db_item


@router.get(
    "/",
    response_model=PagedResponse[MessengerPlatformResponse],
    summary="Отримати список всіх платформ месенджерів",  # i18n
    description="Дозволяє автентифікованим користувачам отримувати сторінковий список всіх платформ месенджерів.",
    # i18n
    dependencies=[Depends(get_current_active_user)]  # Будь-який активний користувач
)
async def get_all_messenger_platforms(
        page_params: PageParams = Depends(paginator),
        service: MessengerPlatformService = Depends(get_messenger_platform_service),
) -> PagedResponse[MessengerPlatformResponse]:
    """
    Отримує всі платформи месенджерів з пагінацією.
    Доступно будь-якому автентифікованому користувачеві.
    """
    logger.debug(
        f"Запит на отримання списку платформ месенджерів: сторінка {page_params.page}, розмір {page_params.size}")
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
    "/{messenger_platform_id}",
    response_model=MessengerPlatformResponse,
    summary="Оновити платформу месенджера",  # i18n
    description="Дозволяє суперкористувачу оновлювати існуючу платформу месенджера.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Тільки суперюзер
)
async def update_messenger_platform(
        messenger_platform_id: UUID,
        messenger_platform_in: MessengerPlatformUpdate,
        service: MessengerPlatformService = Depends(get_messenger_platform_service),
        current_user: UserModel = Depends(get_current_active_superuser)
) -> MessengerPlatformResponse:
    """
    Оновлює існуючу платформу месенджера.
    Доступно тільки суперкористувачам.
    """
    logger.info(
        f"Спроба оновлення платформи месенджера ID '{messenger_platform_id}' користувачем ID '{current_user.id}'.")
    try:
        # TODO: Перевірити, чи модель MessengerPlatform має updated_by_user_id і чи BaseDictionaryService це обробляє.
        updated_item = await service.update(item_id=messenger_platform_id, data=messenger_platform_in)
        if not updated_item:
            logger.warning(f"Платформу месенджера з ID '{messenger_platform_id}' не знайдено для оновлення.")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Платформу месенджера не знайдено.")
        return updated_item
    except ValueError as e:
        logger.warning(f"Помилка оновлення платформи ID '{messenger_platform_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при оновленні ID '{messenger_platform_id}': {e}", exc_info=True)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.delete(
    "/{messenger_platform_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити платформу месенджера",  # i18n
    description="Дозволяє суперкористувачу видалити платформу месенджера. Виконується жорстке видалення.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Тільки суперюзер
)
async def delete_messenger_platform(
        messenger_platform_id: UUID,
        service: MessengerPlatformService = Depends(get_messenger_platform_service),
        current_user: UserModel = Depends(get_current_active_superuser)
):
    """
    Видаляє платформу месенджера за її ID.
    Доступно тільки суперкористувачам.
    """
    logger.info(
        f"Спроба видалення платформи месенджера ID '{messenger_platform_id}' користувачем ID '{current_user.id}'.")
    try:
        deleted = await service.delete(item_id=messenger_platform_id)
        if not deleted:
            logger.warning(f"Платформу месенджера з ID '{messenger_platform_id}' не знайдено для видалення.")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Платформу месенджера не знайдено.")
    except ValueError as e:  # Наприклад, якщо об'єкт використовується
        logger.warning(f"Помилка видалення платформи ID '{messenger_platform_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при видаленні ID '{messenger_platform_id}': {e}", exc_info=True)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")

    return None


logger.info(f"Роутер для довідника '{router.prefix}' (Платформи Месенджерів) визначено.")
