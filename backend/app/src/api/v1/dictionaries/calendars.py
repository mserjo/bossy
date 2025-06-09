# backend/app/src/api/v1/dictionaries/calendars.py
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_superuser
from app.src.models.dictionaries import CalendarProvider as CalendarProviderModel
from app.src.schemas.dictionaries import CalendarProviderCreate, CalendarProviderUpdate, CalendarProviderResponse
from app.src.services.dictionaries import CalendarProviderService
from app.src.repositories.dictionaries import CalendarProviderRepository
from app.src.core.pagination import PagedResponse, PageParams
from app.src.core.dependencies import paginator
# from app.src.models.auth import User as UserModel # Для доступу на основі ролей

router = APIRouter(
    prefix="/calendar-providers",
    tags=["Dictionary - Calendar Providers"],
    dependencies=[Depends(get_current_active_superuser)] # TODO: Налаштувати дозволи - Тільки суперкористувач згідно із завданням
)

# Залежність для отримання CalendarProviderService
async def get_calendar_provider_service(session: AsyncSession = Depends(get_db_session)) -> CalendarProviderService:
    """
    Залежність для отримання екземпляра CalendarProviderService.
    """
    return CalendarProviderService(CalendarProviderRepository(session))

@router.post(
    "/",
    response_model=CalendarProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створити нового постачальника календарів",
    description="Дозволяє суперкористувачу створювати нового постачальника календарів.",
)
async def create_calendar_provider(
    calendar_provider_in: CalendarProviderCreate,
    service: CalendarProviderService = Depends(get_calendar_provider_service),
) -> CalendarProviderModel:
    """
    Створити нового постачальника календарів.
    """
    return await service.create(obj_in=calendar_provider_in)

@router.get(
    "/{calendar_provider_id}",
    response_model=CalendarProviderResponse,
    status_code=status.HTTP_200_OK,
    summary="Отримати постачальника календарів за ID",
    description="Дозволяє суперкористувачу отримувати конкретного постачальника календарів.", # Згідно із завданням, налаштовує тільки суперкористувач
)
async def get_calendar_provider(
    calendar_provider_id: UUID,
    service: CalendarProviderService = Depends(get_calendar_provider_service),
    # current_user: UserModel = Depends(get_current_active_superuser) # Переконатися, що це суперкористувач
) -> CalendarProviderModel:
    """
    Отримати постачальника календарів за його ID.
    """
    db_calendar_provider = await service.get_by_id(obj_id=calendar_provider_id)
    if not db_calendar_provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Постачальника календарів не знайдено")
    return db_calendar_provider

@router.get(
    "/",
    response_model=PagedResponse[CalendarProviderResponse],
    status_code=status.HTTP_200_OK,
    summary="Отримати всіх постачальників календарів",
    description="Дозволяє суперкористувачу отримувати сторінковий список постачальників календарів.", # Згідно із завданням, налаштовує тільки суперкористувач
)
async def get_all_calendar_providers(
    page_params: PageParams = Depends(paginator),
    service: CalendarProviderService = Depends(get_calendar_provider_service),
    # current_user: UserModel = Depends(get_current_active_superuser) # Переконатися, що це суперкористувач
) -> PagedResponse[CalendarProviderModel]:
    """
    Отримати всіх постачальників календарів з пагінацією.
    """
    calendar_providers = await service.get_multi(
        skip=page_params.skip,
        limit=page_params.limit,
        sort=page_params.sort,
        sort_by=page_params.sort_by
    )
    count = await service.count()
    return PagedResponse(results=calendar_providers, total=count, page=page_params.page, size=page_params.size)

@router.put(
    "/{calendar_provider_id}",
    response_model=CalendarProviderResponse,
    status_code=status.HTTP_200_OK,
    summary="Оновити постачальника календарів",
    description="Дозволяє суперкористувачу оновлювати існуючого постачальника календарів.",
)
async def update_calendar_provider(
    calendar_provider_id: UUID,
    calendar_provider_in: CalendarProviderUpdate,
    service: CalendarProviderService = Depends(get_calendar_provider_service),
) -> CalendarProviderModel:
    """
    Оновити існуючого постачальника календарів.
    """
    db_calendar_provider = await service.get_by_id(obj_id=calendar_provider_id)
    if not db_calendar_provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Постачальника календарів не знайдено")
    return await service.update(obj_db=db_calendar_provider, obj_in=calendar_provider_in)

@router.delete(
    "/{calendar_provider_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити постачальника календарів",
    description="Дозволяє суперкористувачу видалити постачальника календарів. (Жорстке видалення)", # TODO: Підтвердити м'яке видалення
)
async def delete_calendar_provider(
    calendar_provider_id: UUID,
    service: CalendarProviderService = Depends(get_calendar_provider_service),
) -> None:
    """
    Видалити постачальника календарів за його ID.
    """
    db_calendar_provider = await service.get_by_id(obj_id=calendar_provider_id)
    if not db_calendar_provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Постачальника календарів не знайдено")
    await service.delete(obj_id=calendar_provider_id)
    return None

# TODO: Розглянути можливість додавання ендпоінта get_calendar_provider_by_code, якщо потрібно.
