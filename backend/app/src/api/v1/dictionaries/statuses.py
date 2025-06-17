# backend/app/src/api/v1/dictionaries/statuses.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління довідником "Статуси".

Дозволяє створювати, отримувати, оновлювати та видаляти статуси.
Доступ до операцій створення, оновлення та видалення обмежений для суперкористувачів.
Перегляд списку та окремих елементів доступний автентифікованим користувачам.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.src.api.dependencies import get_api_db_session, get_current_active_superuser, get_current_active_user, paginator
from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.dictionaries.statuses import StatusCreate, StatusUpdate, StatusResponse
from backend.app.src.services.dictionaries.statuses import StatusService
from backend.app.src.core.pagination import PagedResponse, PageParams
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

router = APIRouter(
    # Префікс /statuses буде додано в __init__.py батьківського роутера
    # Теги також успадковуються/додаються звідти
)


# Залежність для отримання StatusService
async def get_status_service(session: AsyncSession = Depends(get_api_db_session)) -> StatusService:
    """
    Залежність FastAPI для отримання екземпляра StatusService.
    """
    return StatusService(db_session=session)  # Використовуємо db_session напряму

# ПРИМІТКА: Реалізація полів `created_by_user_id`/`updated_by_user_id` (якщо вони є в моделі)
# залежить від можливостей базового сервісу `BaseDictionaryService`.
@router.post(
    "/",
    response_model=StatusResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створити новий статус",  # i18n
    description="Дозволяє суперкористувачу створювати новий системний статус.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Тільки суперюзер
)
async def create_status(
        status_in: StatusCreate,
        service: StatusService = Depends(get_status_service),
        current_user: UserModel = Depends(get_current_active_superuser)
) -> StatusResponse:
    """
    Створює новий статус.
    Доступно тільки суперкористувачам.
    Кожен статус може бути пов'язаний з певним типом сутності (`entity_type`).
    """
    logger.info(
        f"Спроба створення статусу '{status_in.name}' (код: {status_in.code}) користувачем ID '{current_user.id}'.")
    try:
        # TODO: Перевірити, чи модель Status має created_by_user_id і чи BaseDictionaryService це обробляє.
        created_item = await service.create(data=status_in)
        return created_item
    except ValueError as e:
        logger.warning(f"Помилка створення статусу '{status_in.name}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при створенні статусу '{status_in.name}': {e}", exc_info=True)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.get(
    "/{status_id}",
    response_model=StatusResponse,
    summary="Отримати статус за ID",  # i18n
    description="Дозволяє автентифікованим користувачам отримувати інформацію про конкретний статус.",  # i18n
    dependencies=[Depends(get_current_active_user)]  # Будь-який активний користувач
)
async def get_status(
        status_id: UUID,
        service: StatusService = Depends(get_status_service),
) -> StatusResponse:
    """
    Отримує статус за його ID.
    Доступно будь-якому автентифікованому користувачеві.
    """
    logger.debug(f"Запит на отримання статусу за ID: {status_id}")
    db_item = await service.get_by_id(item_id=status_id)
    if not db_item:
        logger.warning(f"Статус з ID '{status_id}' не знайдено.")
        # i18n
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статус не знайдено.")
    return db_item

# ПРИМІТКА: Коректна фільтрація за `entity_type` та відповідна пагінація
# залежать від реалізації спеціалізованих методів у `StatusService`
# (наприклад, `list_statuses_by_entity_type` та `count_by_entity_type`),
# як зазначено в TODO. Поточна реалізація фільтрації є заглушкою.
@router.get(
    "/",
    response_model=PagedResponse[StatusResponse],
    summary="Отримати список всіх статусів",  # i18n
    description="Дозволяє автентифікованим користувачам отримувати сторінковий список всіх статусів, з можливістю фільтрації за типом сутності.",
    # i18n
    dependencies=[Depends(get_current_active_user)]  # Будь-який активний користувач
)
async def get_all_statuses(
        entity_type: Optional[str] = Query(None,
                                           description="Фільтрувати статуси за типом сутності (наприклад, TASK, PROJECT)."),
        # i18n
        page_params: PageParams = Depends(paginator),
        service: StatusService = Depends(get_status_service),
) -> PagedResponse[StatusResponse]:
    """
    Отримує всі статуси з пагінацією та можливістю фільтрації за `entity_type`.
    Доступно будь-якому автентифікованому користувачеві.
    """
    logger.debug(
        f"Запит на отримання списку статусів: сторінка {page_params.page}, розмір {page_params.size}, entity_type: {entity_type}")

    # TODO: Додати метод get_all_with_filter до BaseDictionaryService або кастомний метод до StatusService
    #  для фільтрації за entity_type та іншими полями, якщо потрібно.
    #  Поки що, якщо entity_type надано, використовуємо кастомний запит. Якщо ні - загальний get_all.
    if entity_type:
        # Припускаємо, що StatusService має кастомний метод для такої фільтрації,
        # або ми реалізуємо його тут (що менш бажано).
        # Для прикладу, припустимо, StatusService має list_statuses_by_entity_type
        if hasattr(service, 'list_statuses_by_entity_type'):
            items_page = await service.list_statuses_by_entity_type(  # type: ignore
                entity_type=entity_type, skip=page_params.skip, limit=page_params.limit
            )
            # Для PagedResponse потрібен загальний count для цього фільтра
            # total_count = await service.count_by_entity_type(entity_type=entity_type) # Потрібен такий метод
            # Тимчасова заглушка для count
            total_count = len(items_page) if items_page else 0
            logger.warning(
                "Використовується тимчасова заглушка для total_count при фільтрації статусів за entity_type.")

        else:  # Якщо немає спеціального методу, повертаємо помилку або пустий список
            logger.warning(
                f"Фільтрація за entity_type для статусів не реалізована в сервісі. Повернення порожнього списку.")
            items_page = []
            total_count = 0
    else:
        items_page = await service.get_all(skip=page_params.skip, limit=page_params.limit)
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
    "/{status_id}",
    response_model=StatusResponse,
    summary="Оновити статус",  # i18n
    description="Дозволяє суперкористувачу оновлювати існуючий статус.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Тільки суперюзер
)
async def update_status(
        status_id: UUID,
        status_in: StatusUpdate,
        service: StatusService = Depends(get_status_service),
        current_user: UserModel = Depends(get_current_active_superuser)
) -> StatusResponse:
    """
    Оновлює існуючий статус.
    Доступно тільки суперкористувачам.
    """
    logger.info(f"Спроба оновлення статусу ID '{status_id}' користувачем ID '{current_user.id}'.")
    try:
        # TODO: Перевірити, чи модель Status має updated_by_user_id і чи BaseDictionaryService це обробляє.
        updated_item = await service.update(item_id=status_id, data=status_in)
        if not updated_item:
            logger.warning(f"Статус з ID '{status_id}' не знайдено для оновлення.")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статус не знайдено.")
        return updated_item
    except ValueError as e:
        logger.warning(f"Помилка оновлення статусу ID '{status_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при оновленні статусу ID '{status_id}': {e}", exc_info=True)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.delete(
    "/{status_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити статус",  # i18n
    description="Дозволяє суперкористувачу видалити статус. Виконується жорстке видалення.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Тільки суперюзер
)
async def delete_status(
        status_id: UUID,
        service: StatusService = Depends(get_status_service),
        current_user: UserModel = Depends(get_current_active_superuser)
):
    """
    Видаляє статус за його ID.
    Доступно тільки суперкористувачам.
    """
    logger.info(f"Спроба видалення статусу ID '{status_id}' користувачем ID '{current_user.id}'.")
    try:
        deleted = await service.delete(item_id=status_id)
        if not deleted:
            logger.warning(f"Статус з ID '{status_id}' не знайдено для видалення.")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статус не знайдено.")
    except ValueError as e:  # Наприклад, якщо об'єкт використовується
        logger.warning(f"Помилка видалення статусу ID '{status_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при видаленні статусу ID '{status_id}': {e}", exc_info=True)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")

    return None


logger.info(f"Роутер для довідника '{router.prefix}' (Статуси) визначено.")
