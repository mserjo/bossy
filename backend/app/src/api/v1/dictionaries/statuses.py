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
    dependencies=[Depends(get_current_active_superuser)] # TODO: Adjust permissions as per technical_task.txt
)

# Dependency to get StatusService
async def get_status_service(session: AsyncSession = Depends(get_db_session)) -> StatusService:
    """
    Dependency to get an instance of StatusService.

    Args:
        session: The database session.

    Returns:
        An instance of StatusService.
    """
    return StatusService(StatusRepository(session))

@router.post(
    "/",
    response_model=StatusResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new status",
    description="Allows a superuser to create a new status type for the system.",
)
async def create_status(
    status_in: StatusCreate,
    service: StatusService = Depends(get_status_service),
) -> StatusModel:
    """
    Create a new status.

    Args:
        status_in: The status data to create.
        service: The status service.

    Returns:
        The created status.
    """
    # TODO: Add logic based on technical_task.txt for specific roles if needed
    return await service.create(obj_in=status_in)

@router.get(
    "/{status_id}",
    response_model=StatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a status by ID",
    description="Allows any authenticated user (TODO: verify this based on task) to retrieve a specific status by its ID.",
)
async def get_status(
    status_id: UUID,
    service: StatusService = Depends(get_status_service),
    # current_user: UserModel = Depends(get_current_active_user) # TODO: Add if needed for role-based access
) -> StatusModel:
    """
    Get a status by its ID.

    Args:
        status_id: The ID of the status to retrieve.
        service: The status service.

    Returns:
        The status with the given ID.

    Raises:
        HTTPException: If the status is not found.
    """
    db_status = await service.get_by_id(obj_id=status_id)
    if not db_status:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status not found")
    return db_status

@router.get(
    "/",
    response_model=PagedResponse[StatusResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all statuses",
    description="Allows any authenticated user (TODO: verify this based on task) to retrieve a paginated list of all statuses.",
)
async def get_all_statuses(
    page_params: PageParams = Depends(paginator),
    service: StatusService = Depends(get_status_service),
    # current_user: UserModel = Depends(get_current_active_user) # TODO: Add if needed for role-based access
) -> PagedResponse[StatusModel]:
    """
    Get all statuses with pagination.

    Args:
        page_params: Pagination parameters.
        service: The status service.

    Returns:
        A paginated list of statuses.
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
    summary="Update a status",
    description="Allows a superuser to update an existing status.",
)
async def update_status(
    status_id: UUID,
    status_in: StatusUpdate,
    service: StatusService = Depends(get_status_service),
) -> StatusModel:
    """
    Update an existing status.

    Args:
        status_id: The ID of the status to update.
        status_in: The new status data.
        service: The status service.

    Returns:
        The updated status.

    Raises:
        HTTPException: If the status is not found.
    """
    db_status = await service.get_by_id(obj_id=status_id)
    if not db_status:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status not found")
    # TODO: Add logic based on technical_task.txt for specific roles if needed
    return await service.update(obj_db=db_status, obj_in=status_in)

@router.delete(
    "/{status_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a status",
    description="Allows a superuser to delete a status. This is a hard delete.", # TODO: Confirm if soft delete is needed based on BaseMainModel
)
async def delete_status(
    status_id: UUID,
    service: StatusService = Depends(get_status_service),
) -> None:
    """
    Delete a status by its ID.

    Args:
        status_id: The ID of the status to delete.
        service: The status service.

    Raises:
        HTTPException: If the status is not found.
    """
    db_status = await service.get_by_id(obj_id=status_id)
    if not db_status:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status not found")
    # TODO: Add logic based on technical_task.txt for specific roles if needed
    await service.delete(obj_id=status_id)
    return None # FastAPI will return 204 No Content automatically

# TODO: Add more specific endpoints if required by technical_task.txt
# For example, get_status_by_code if 'code' is a unique field and frequently used for lookup.
