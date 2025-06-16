# backend/app/src/api/v1/dictionaries/calendars.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління довідником "Постачальники Календарів".

Дозволяє створювати, отримувати, оновлювати та видаляти постачальників календарів.
Доступ до операцій створення, оновлення та видалення обмежений для суперкористувачів.
Перегляд списку та окремих елементів доступний автентифікованим користувачам.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from typing import List # Any видалено, оскільки не використовується
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# Повні шляхи імпорту
from backend.app.src.api.dependencies import get_api_db_session, get_current_active_superuser, get_current_active_user, \
    paginator
from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.dictionaries.calendars import CalendarProviderCreate, CalendarProviderUpdate, \
    CalendarProviderResponse
from backend.app.src.services.dictionaries.calendars import CalendarProviderService
# from backend.app.src.repositories.dictionaries import CalendarProviderRepository # Видалено, сервіс працює напряму з сесією
from backend.app.src.core.pagination import PagedResponse, PageParams
from backend.app.src.config.logging import logger  # Централізований логер

router = APIRouter(
    # Префікс /calendar-providers буде додано в __init__.py батьківського роутера
    # Теги також успадковуються/додаються звідти
)


# Залежність для отримання CalendarProviderService
async def get_calendar_provider_service(session: AsyncSession = Depends(get_api_db_session)) -> CalendarProviderService:
    """
    Залежність FastAPI для отримання екземпляра CalendarProviderService.
    """
    return CalendarProviderService(db_session=session)  # Використовуємо db_session напряму

# ПРИМІТКА: Реалізація полів `created_by_user_id`/`updated_by_user_id` (якщо вони є в моделі)
# залежить від можливостей базового сервісу `BaseDictionaryService`.
@router.post(
    "/",
    response_model=CalendarProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створити нового постачальника календарів",  # i18n
    description="Дозволяє суперкористувачу створювати нового постачальника календарів.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Тільки суперюзер
)
async def create_calendar_provider(
        calendar_provider_in: CalendarProviderCreate,
        service: CalendarProviderService = Depends(get_calendar_provider_service),
        current_user: UserModel = Depends(get_current_active_superuser)  # Для created_by_user_id, якщо потрібно
) -> CalendarProviderResponse:
    """
    Створює нового постачальника календарів.
    Доступно тільки суперкористувачам.
    """
    logger.info(
        f"Спроба створення постачальника календарів '{calendar_provider_in.name}' користувачем ID '{current_user.id}'.")
    try:
        # TODO: Перевірити, чи модель CalendarProvider має created_by_user_id і чи BaseDictionaryService це обробляє.
        created_item = await service.create(data=calendar_provider_in)
        return created_item
    except ValueError as e:
        logger.warning(f"Помилка створення постачальника календарів '{calendar_provider_in.name}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при створенні '{calendar_provider_in.name}': {e}", exc_info=True)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.get(
    "/{calendar_provider_id}",
    response_model=CalendarProviderResponse,
    summary="Отримати постачальника календарів за ID",  # i18n
    description="Дозволяє автентифікованим користувачам отримувати інформацію про конкретного постачальника календарів.",
    # i18n
    dependencies=[Depends(get_current_active_user)]  # Будь-який активний користувач
)
async def get_calendar_provider(
        calendar_provider_id: UUID,
        service: CalendarProviderService = Depends(get_calendar_provider_service),
) -> CalendarProviderResponse:
    """
    Отримує постачальника календарів за його ID.
    Доступно будь-якому автентифікованому користувачеві.
    """
    logger.debug(f"Запит на отримання постачальника календарів за ID: {calendar_provider_id}")
    db_item = await service.get_by_id(item_id=calendar_provider_id)
    if not db_item:
        logger.warning(f"Постачальника календарів з ID '{calendar_provider_id}' не знайдено.")
        # i18n
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Постачальника календарів не знайдено.")
    return db_item

# ПРИМІТКА: Коректна пагінація залежить від реалізації методу `count_all()`
# в `CalendarProviderService` (успадкованого від `BaseDictionaryService`).
@router.get(
    "/",
    response_model=PagedResponse[CalendarProviderResponse],
    summary="Отримати список всіх постачальників календарів",  # i18n
    description="Дозволяє автентифікованим користувачам отримувати сторінковий список всіх постачальників календарів.",
    # i18n
    dependencies=[Depends(get_current_active_user)]  # Будь-який активний користувач
)
async def get_all_calendar_providers(
        page_params: PageParams = Depends(paginator),
        service: CalendarProviderService = Depends(get_calendar_provider_service),
) -> PagedResponse[CalendarProviderResponse]:
    """
    Отримує всіх постачальників календарів з пагінацією.
    Доступно будь-якому автентифікованому користувачеві.
    """
    logger.debug(
        f"Запит на отримання списку постачальників календарів: сторінка {page_params.page}, розмір {page_params.size}")
    items_page = await service.get_all(skip=page_params.skip, limit=page_params.limit)
    # TODO: Реалізувати метод count_all() в BaseDictionaryService для коректної пагінації.
    total_count = await service.count_all()

    return PagedResponse(
        results=items_page,
        total=total_count,
        page=page_params.page,
        size=page_params.size
    )


# ПРИМІТКА: Реалізація полів `created_by_user_id`/`updated_by_user_id` (якщо вони є в моделі)
# залежить від можливостей базового сервісу `BaseDictionaryService`.
@router.put(
    "/{calendar_provider_id}",
    response_model=CalendarProviderResponse,
    summary="Оновити постачальника календарів",  # i18n
    description="Дозволяє суперкористувачу оновлювати існуючого постачальника календарів.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Тільки суперюзер
)
async def update_calendar_provider(
        calendar_provider_id: UUID,
        calendar_provider_in: CalendarProviderUpdate,
        service: CalendarProviderService = Depends(get_calendar_provider_service),
        current_user: UserModel = Depends(get_current_active_superuser)  # Для updated_by_user_id
) -> CalendarProviderResponse:
    """
    Оновлює існуючого постачальника календарів.
    Доступно тільки суперкористувачам.
    """
    logger.info(
        f"Спроба оновлення постачальника календарів ID '{calendar_provider_id}' користувачем ID '{current_user.id}'.")
    try:
        # TODO: Перевірити, чи модель CalendarProvider має updated_by_user_id і чи BaseDictionaryService це обробляє.
        updated_item = await service.update(item_id=calendar_provider_id, data=calendar_provider_in)
        if not updated_item:
            logger.warning(f"Постачальника календарів з ID '{calendar_provider_id}' не знайдено для оновлення.")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Постачальника календарів не знайдено.")
        return updated_item
    except ValueError as e:
        logger.warning(f"Помилка оновлення постачальника ID '{calendar_provider_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при оновленні ID '{calendar_provider_id}': {e}", exc_info=True)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.delete(
    "/{calendar_provider_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити постачальника календарів",  # i18n
    description="Дозволяє суперкористувачу видалити постачальника календарів. Виконується жорстке видалення.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Тільки суперюзер
)
async def delete_calendar_provider(
        calendar_provider_id: UUID,
        service: CalendarProviderService = Depends(get_calendar_provider_service),
        current_user: UserModel = Depends(get_current_active_superuser)  # Для логування аудиту
):
    """
    Видаляє постачальника календарів за його ID.
    Доступно тільки суперкористувачам.
    """
    logger.info(
        f"Спроба видалення постачальника календарів ID '{calendar_provider_id}' користувачем ID '{current_user.id}'.")
    try:
        deleted = await service.delete(item_id=calendar_provider_id)
        if not deleted:
            logger.warning(f"Постачальника календарів з ID '{calendar_provider_id}' не знайдено для видалення.")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Постачальника календарів не знайдено.")
    except ValueError as e:  # Наприклад, якщо об'єкт використовується і сервіс кидає помилку
        logger.warning(f"Помилка видалення постачальника ID '{calendar_provider_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при видаленні ID '{calendar_provider_id}': {e}", exc_info=True)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")

    return None  # Повертаємо порожню відповідь зі статусом 204


# TODO: Розглянути можливість додавання ендпоінта get_calendar_provider_by_code, якщо поле 'code' є ключовим.
# BaseDictionaryService вже має get_by_code, тому, якщо CalendarProvider має 'code', він буде доступний.

logger.info(f"Роутер для довідника '{router.prefix}' (Постачальники Календарів) визначено.")
