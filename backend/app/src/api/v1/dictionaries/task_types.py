# backend/app/src/api/v1/dictionaries/task_types.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління довідником "Типи Завдань".

Дозволяє створювати, отримувати, оновлювати та видаляти типи завдань.
Доступ до операцій створення, оновлення та видалення обмежений для суперкористувачів.
Перегляд списку та окремих елементів доступний автентифікованим користувачам.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from typing import List # Any вже було видалено, або не було
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# Повні шляхи імпорту
from backend.app.src.api.dependencies import get_api_db_session, get_current_active_superuser, get_current_active_user, \
    paginator
from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.dictionaries.task_types import TaskTypeCreate, TaskTypeUpdate, TaskTypeResponse
from backend.app.src.services.dictionaries.task_types import TaskTypeService
# from backend.app.src.repositories.dictionaries import TaskTypeRepository # Видалено
from backend.app.src.core.pagination import PagedResponse, PageParams
from backend.app.src.config.logging import logger  # Централізований логер

router = APIRouter(
    # Префікс /task-types буде додано в __init__.py батьківського роутера
    # Теги також успадковуються/додаються звідти
)


# Залежність для отримання TaskTypeService
async def get_task_type_service(session: AsyncSession = Depends(get_api_db_session)) -> TaskTypeService:
    """
    Залежність FastAPI для отримання екземпляра TaskTypeService.
    """
    return TaskTypeService(db_session=session)  # Використовуємо db_session напряму

# ПРИМІТКА: Реалізація полів `created_by_user_id`/`updated_by_user_id` (якщо вони є в моделі)
# залежить від можливостей базового сервісу `BaseDictionaryService`.
@router.post(
    "/",
    response_model=TaskTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створити новий тип завдання",  # i18n
    description="Дозволяє суперкористувачу створювати новий тип завдання.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Тільки суперюзер
)
async def create_task_type(
        task_type_in: TaskTypeCreate,
        service: TaskTypeService = Depends(get_task_type_service),
        current_user: UserModel = Depends(get_current_active_superuser)
) -> TaskTypeResponse:
    """
    Створює новий тип завдання.
    Доступно тільки суперкористувачам.
    """
    logger.info(f"Спроба створення типу завдання '{task_type_in.name}' користувачем ID '{current_user.id}'.")
    try:
        # TODO: Перевірити, чи модель TaskType має created_by_user_id і чи BaseDictionaryService це обробляє.
        created_item = await service.create(data=task_type_in)
        return created_item
    except ValueError as e:
        logger.warning(f"Помилка створення типу завдання '{task_type_in.name}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при створенні '{task_type_in.name}': {e}", exc_info=True)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.get(
    "/{task_type_id}",
    response_model=TaskTypeResponse,
    summary="Отримати тип завдання за ID",  # i18n
    description="Дозволяє автентифікованим користувачам отримувати інформацію про конкретний тип завдання.",  # i18n
    dependencies=[Depends(get_current_active_user)]  # Будь-який активний користувач
)
async def get_task_type(
        task_type_id: UUID,
        service: TaskTypeService = Depends(get_task_type_service),
) -> TaskTypeResponse:
    """
    Отримує тип завдання за його ID.
    Доступно будь-якому автентифікованому користувачеві.
    """
    logger.debug(f"Запит на отримання типу завдання за ID: {task_type_id}")
    db_item = await service.get_by_id(item_id=task_type_id)
    if not db_item:
        logger.warning(f"Тип завдання з ID '{task_type_id}' не знайдено.")
        # i18n
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип завдання не знайдено.")
    return db_item

# ПРИМІТКА: Коректна пагінація залежить від реалізації методу `count_all()`
# в `TaskTypeService` (успадкованого від `BaseDictionaryService`).
@router.get(
    "/",
    response_model=PagedResponse[TaskTypeResponse],
    summary="Отримати список всіх типів завдань",  # i18n
    description="Дозволяє автентифікованим користувачам отримувати сторінковий список всіх типів завдань.",  # i18n
    dependencies=[Depends(get_current_active_user)]  # Будь-який активний користувач
)
async def get_all_task_types(
        page_params: PageParams = Depends(paginator),
        service: TaskTypeService = Depends(get_task_type_service),
) -> PagedResponse[TaskTypeResponse]:
    """
    Отримує всі типи завдань з пагінацією.
    Доступно будь-якому автентифікованому користувачеві.
    """
    logger.debug(f"Запит на отримання списку типів завдань: сторінка {page_params.page}, розмір {page_params.size}")
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
    "/{task_type_id}",
    response_model=TaskTypeResponse,
    summary="Оновити тип завдання",  # i18n
    description="Дозволяє суперкористувачу оновлювати існуючий тип завдання.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Тільки суперюзер
)
async def update_task_type(
        task_type_id: UUID,
        task_type_in: TaskTypeUpdate,
        service: TaskTypeService = Depends(get_task_type_service),
        current_user: UserModel = Depends(get_current_active_superuser)
) -> TaskTypeResponse:
    """
    Оновлює існуючий тип завдання.
    Доступно тільки суперкористувачам.
    """
    logger.info(f"Спроба оновлення типу завдання ID '{task_type_id}' користувачем ID '{current_user.id}'.")
    try:
        # TODO: Перевірити, чи модель TaskType має updated_by_user_id і чи BaseDictionaryService це обробляє.
        updated_item = await service.update(item_id=task_type_id, data=task_type_in)
        if not updated_item:
            logger.warning(f"Тип завдання з ID '{task_type_id}' не знайдено для оновлення.")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип завдання не знайдено.")
        return updated_item
    except ValueError as e:
        logger.warning(f"Помилка оновлення типу завдання ID '{task_type_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при оновленні ID '{task_type_id}': {e}", exc_info=True)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.delete(
    "/{task_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити тип завдання",  # i18n
    description="Дозволяє суперкористувачу видалити тип завдання. Виконується жорстке видалення.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Тільки суперюзер
)
async def delete_task_type(
        task_type_id: UUID,
        service: TaskTypeService = Depends(get_task_type_service),
        current_user: UserModel = Depends(get_current_active_superuser)
):
    """
    Видаляє тип завдання за його ID.
    Доступно тільки суперкористувачам.
    """
    logger.info(f"Спроба видалення типу завдання ID '{task_type_id}' користувачем ID '{current_user.id}'.")
    try:
        deleted = await service.delete(item_id=task_type_id)
        if not deleted:
            logger.warning(f"Тип завдання з ID '{task_type_id}' не знайдено для видалення.")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип завдання не знайдено.")
    except ValueError as e:  # Наприклад, якщо об'єкт використовується
        logger.warning(f"Помилка видалення типу завдання ID '{task_type_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при видаленні ID '{task_type_id}': {e}", exc_info=True)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")

    return None


logger.info(f"Роутер для довідника '{router.prefix}' (Типи Завдань) визначено.")
