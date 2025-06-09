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
# from app.src.models.auth import User as UserModel # For role-based access

router = APIRouter(
    prefix="/calendar-providers",
    tags=["Dictionary - Calendar Providers"],
    dependencies=[Depends(get_current_active_superuser)] # TODO: Adjust permissions - Superuser only as per task
)

# Dependency to get CalendarProviderService
async def get_calendar_provider_service(session: AsyncSession = Depends(get_db_session)) -> CalendarProviderService:
    """
    Dependency to get an instance of CalendarProviderService.
    """
    return CalendarProviderService(CalendarProviderRepository(session))

@router.post(
    "/",
    response_model=CalendarProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new calendar provider",
    description="Allows a superuser to create a new calendar provider.",
)
async def create_calendar_provider(
    calendar_provider_in: CalendarProviderCreate,
    service: CalendarProviderService = Depends(get_calendar_provider_service),
) -> CalendarProviderModel:
    """
    Create a new calendar provider.
    """
    return await service.create(obj_in=calendar_provider_in)

@router.get(
    "/{calendar_provider_id}",
    response_model=CalendarProviderResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a calendar provider by ID",
    description="Allows a superuser to retrieve a specific calendar provider.", # As per task, only superuser configures this
)
async def get_calendar_provider(
    calendar_provider_id: UUID,
    service: CalendarProviderService = Depends(get_calendar_provider_service),
    # current_user: UserModel = Depends(get_current_active_superuser) # Ensure superuser
) -> CalendarProviderModel:
    """
    Get a calendar provider by its ID.
    """
    db_calendar_provider = await service.get_by_id(obj_id=calendar_provider_id)
    if not db_calendar_provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar provider not found")
    return db_calendar_provider

@router.get(
    "/",
    response_model=PagedResponse[CalendarProviderResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all calendar providers",
    description="Allows a superuser to retrieve a paginated list of calendar providers.", # As per task, only superuser configures this
)
async def get_all_calendar_providers(
    page_params: PageParams = Depends(paginator),
    service: CalendarProviderService = Depends(get_calendar_provider_service),
    # current_user: UserModel = Depends(get_current_active_superuser) # Ensure superuser
) -> PagedResponse[CalendarProviderModel]:
    """
    Get all calendar providers with pagination.
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
    summary="Update a calendar provider",
    description="Allows a superuser to update an existing calendar provider.",
)
async def update_calendar_provider(
    calendar_provider_id: UUID,
    calendar_provider_in: CalendarProviderUpdate,
    service: CalendarProviderService = Depends(get_calendar_provider_service),
) -> CalendarProviderModel:
    """
    Update an existing calendar provider.
    """
    db_calendar_provider = await service.get_by_id(obj_id=calendar_provider_id)
    if not db_calendar_provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar provider not found")
    return await service.update(obj_db=db_calendar_provider, obj_in=calendar_provider_in)

@router.delete(
    "/{calendar_provider_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a calendar provider",
    description="Allows a superuser to delete a calendar provider. (Hard delete)", # TODO: Confirm soft delete
)
async def delete_calendar_provider(
    calendar_provider_id: UUID,
    service: CalendarProviderService = Depends(get_calendar_provider_service),
) -> None:
    """
    Delete a calendar provider by its ID.
    """
    db_calendar_provider = await service.get_by_id(obj_id=calendar_provider_id)
    if not db_calendar_provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar provider not found")
    await service.delete(obj_id=calendar_provider_id)
    return None

# TODO: Consider get_calendar_provider_by_code endpoint if needed.
