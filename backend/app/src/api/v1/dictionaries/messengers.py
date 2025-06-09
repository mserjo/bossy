# backend/app/src/api/v1/dictionaries/messengers.py
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_superuser
from app.src.models.dictionaries import MessengerPlatform as MessengerPlatformModel
from app.src.schemas.dictionaries import MessengerPlatformCreate, MessengerPlatformUpdate, MessengerPlatformResponse
from app.src.services.dictionaries import MessengerPlatformService
from app.src.repositories.dictionaries import MessengerPlatformRepository
from app.src.core.pagination import PagedResponse, PageParams
from app.src.core.dependencies import paginator
# from app.src.models.auth import User as UserModel # For role-based access

router = APIRouter(
    prefix="/messenger-platforms",
    tags=["Dictionary - Messenger Platforms"],
    dependencies=[Depends(get_current_active_superuser)] # TODO: Adjust permissions - Superuser only as per task
)

# Dependency to get MessengerPlatformService
async def get_messenger_platform_service(session: AsyncSession = Depends(get_db_session)) -> MessengerPlatformService:
    """
    Dependency to get an instance of MessengerPlatformService.
    """
    return MessengerPlatformService(MessengerPlatformRepository(session))

@router.post(
    "/",
    response_model=MessengerPlatformResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new messenger platform",
    description="Allows a superuser to create a new messenger platform.",
)
async def create_messenger_platform(
    messenger_platform_in: MessengerPlatformCreate,
    service: MessengerPlatformService = Depends(get_messenger_platform_service),
) -> MessengerPlatformModel:
    """
    Create a new messenger platform.
    """
    return await service.create(obj_in=messenger_platform_in)

@router.get(
    "/{messenger_platform_id}",
    response_model=MessengerPlatformResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a messenger platform by ID",
    description="Allows a superuser to retrieve a specific messenger platform.", # As per task, only superuser configures this
)
async def get_messenger_platform(
    messenger_platform_id: UUID,
    service: MessengerPlatformService = Depends(get_messenger_platform_service),
    # current_user: UserModel = Depends(get_current_active_superuser) # Ensure superuser
) -> MessengerPlatformModel:
    """
    Get a messenger platform by its ID.
    """
    db_messenger_platform = await service.get_by_id(obj_id=messenger_platform_id)
    if not db_messenger_platform:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Messenger platform not found")
    return db_messenger_platform

@router.get(
    "/",
    response_model=PagedResponse[MessengerPlatformResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all messenger platforms",
    description="Allows a superuser to retrieve a paginated list of messenger platforms.", # As per task, only superuser configures this
)
async def get_all_messenger_platforms(
    page_params: PageParams = Depends(paginator),
    service: MessengerPlatformService = Depends(get_messenger_platform_service),
    # current_user: UserModel = Depends(get_current_active_superuser) # Ensure superuser
) -> PagedResponse[MessengerPlatformModel]:
    """
    Get all messenger platforms with pagination.
    """
    messenger_platforms = await service.get_multi(
        skip=page_params.skip,
        limit=page_params.limit,
        sort=page_params.sort,
        sort_by=page_params.sort_by
    )
    count = await service.count()
    return PagedResponse(results=messenger_platforms, total=count, page=page_params.page, size=page_params.size)

@router.put(
    "/{messenger_platform_id}",
    response_model=MessengerPlatformResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a messenger platform",
    description="Allows a superuser to update an existing messenger platform.",
)
async def update_messenger_platform(
    messenger_platform_id: UUID,
    messenger_platform_in: MessengerPlatformUpdate,
    service: MessengerPlatformService = Depends(get_messenger_platform_service),
) -> MessengerPlatformModel:
    """
    Update an existing messenger platform.
    """
    db_messenger_platform = await service.get_by_id(obj_id=messenger_platform_id)
    if not db_messenger_platform:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Messenger platform not found")
    return await service.update(obj_db=db_messenger_platform, obj_in=messenger_platform_in)

@router.delete(
    "/{messenger_platform_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a messenger platform",
    description="Allows a superuser to delete a messenger platform. (Hard delete)", # TODO: Confirm soft delete
)
async def delete_messenger_platform(
    messenger_platform_id: UUID,
    service: MessengerPlatformService = Depends(get_messenger_platform_service),
) -> None:
    """
    Delete a messenger platform by its ID.
    """
    db_messenger_platform = await service.get_by_id(obj_id=messenger_platform_id)
    if not db_messenger_platform:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Messenger platform not found")
    await service.delete(obj_id=messenger_platform_id)
    return None

# TODO: Consider get_messenger_platform_by_code endpoint if needed.
