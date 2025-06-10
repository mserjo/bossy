# backend/app/src/api/v1/dictionaries/statuses.py
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_superuser
from app.src.models.dictionaries import Status as StatusModel
from app.src.schemas.dictionaries import StatusCreate, StatusUpdate, StatusResponse
from app.src.services.dictionaries import StatusService
from app.src.repositories.dictionaries import StatusRepository
from app.src.core.pagination import PagedResponse, PageParams
from app.src.core.dependencies import paginator

router = APIRouter(
    prefix="/statuses",
    tags=["Dictionary - Statuses"],
    dependencies=[Depends(get_current_active_superuser)] # TODO: Налаштувати дозволи згідно з technical_task.txt
)

# Залежність для отримання StatusService
async def get_status_service(session: AsyncSession = Depends(get_db_session)) -> StatusService:
    """
    Залежність для отримання екземпляра StatusService.

    Args:
        session: Сесія бази даних.

    Returns:
        Екземпляр StatusService.
    """
    return StatusService(StatusRepository(session))

@router.post(
    "/",
    response_model=StatusResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створити новий статус",
    description="Дозволяє суперкористувачу створювати новий тип статусу для системи.",
)
async def create_status(
    status_in: StatusCreate,
    service: StatusService = Depends(get_status_service),
) -> StatusModel:
    """
    Створити новий статус.

    Args:
        status_in: Дані статусу для створення.
        service: Сервіс статусів.

    Returns:
        Створений статус.
    """
    # TODO: Додати логіку на основі technical_task.txt для конкретних ролей, якщо потрібно
    return await service.create(obj_in=status_in)

@router.get(
    "/{status_id}",
    response_model=StatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Отримати статус за ID",
    description="Дозволяє будь-якому автентифікованому користувачу (TODO: перевірити це на основі завдання) отримати конкретний статус за його ID.",
)
async def get_status(
    status_id: UUID,
    service: StatusService = Depends(get_status_service),
    # current_user: UserModel = Depends(get_current_active_user) # TODO: Додати, якщо потрібно для доступу на основі ролей
) -> StatusModel:
    """
    Отримати статус за його ID.

    Args:
        status_id: ID статусу для отримання.
        service: Сервіс статусів.

    Returns:
        Статус із зазначеним ID.

    Raises:
        HTTPException: Якщо статус не знайдено.
    """
    db_status = await service.get_by_id(obj_id=status_id)
    if not db_status:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статус не знайдено")
    return db_status

@router.get(
    "/",
    response_model=PagedResponse[StatusResponse],
    status_code=status.HTTP_200_OK,
    summary="Отримати всі статуси",
    description="Дозволяє будь-якому автентифікованому користувачу (TODO: перевірити це на основі завдання) отримати сторінковий список усіх статусів.",
)
async def get_all_statuses(
    page_params: PageParams = Depends(paginator),
    service: StatusService = Depends(get_status_service),
    # current_user: UserModel = Depends(get_current_active_user) # TODO: Додати, якщо потрібно для доступу на основі ролей
) -> PagedResponse[StatusModel]:
    """
    Отримати всі статуси з пагінацією.

    Args:
        page_params: Параметри пагінації.
        service: Сервіс статусів.

    Returns:
        Сторінковий список статусів.
    """
    statuses = await service.get_multi(
        skip=page_params.skip,
        limit=page_params.limit,
        sort=page_params.sort,
        sort_by=page_params.sort_by
    )
    count = await service.count()
    return PagedResponse(results=statuses, total=count, page=page_params.page, size=page_params.size)


@router.put(
    "/{status_id}",
    response_model=StatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Оновити статус",
    description="Дозволяє суперкористувачу оновлювати існуючий статус.",
)
async def update_status(
    status_id: UUID,
    status_in: StatusUpdate,
    service: StatusService = Depends(get_status_service),
) -> StatusModel:
    """
    Оновити існуючий статус.

    Args:
        status_id: ID статусу для оновлення.
        status_in: Нові дані статусу.
        service: Сервіс статусів.

    Returns:
        Оновлений статус.

    Raises:
        HTTPException: Якщо статус не знайдено.
    """
    db_status = await service.get_by_id(obj_id=status_id)
    if not db_status:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статус не знайдено")
    # TODO: Додати логіку на основі technical_task.txt для конкретних ролей, якщо потрібно
    return await service.update(obj_db=db_status, obj_in=status_in)

@router.delete(
    "/{status_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити статус",
    description="Дозволяє суперкористувачу видалити статус. Це жорстке видалення.", # TODO: Підтвердити, чи потрібне м'яке видалення на основі BaseMainModel
)
async def delete_status(
    status_id: UUID,
    service: StatusService = Depends(get_status_service),
) -> None:
    """
    Видалити статус за його ID.

    Args:
        status_id: ID статусу для видалення.
        service: Сервіс статусів.

    Raises:
        HTTPException: Якщо статус не знайдено.
    """
    db_status = await service.get_by_id(obj_id=status_id)
    if not db_status:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статус не знайдено")
    # TODO: Додати логіку на основі technical_task.txt для конкретних ролей, якщо потрібно
    await service.delete(obj_id=status_id)
    return None # FastAPI автоматично поверне 204 No Content

# TODO: Додати більш конкретні ендпоінти, якщо це вимагається technical_task.txt
# Наприклад, get_status_by_code, якщо 'code' є унікальним полем і часто використовується для пошуку.
