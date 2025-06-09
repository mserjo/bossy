# backend/app/src/api/v1/dictionaries/group_types.py
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_superuser
from app.src.models.dictionaries import GroupType as GroupTypeModel
from app.src.schemas.dictionaries import GroupTypeCreate, GroupTypeUpdate, GroupTypeResponse
from app.src.services.dictionaries import GroupTypeService
from app.src.repositories.dictionaries import GroupTypeRepository
from app.src.core.pagination import PagedResponse, PageParams
from app.src.core.dependencies import paginator
# from app.src.models.auth import User as UserModel # For role-based access

router = APIRouter(
    prefix="/group-types",
    tags=["Dictionary - Group Types"],
    dependencies=[Depends(get_current_active_superuser)] # TODO: Adjust permissions
)

# Dependency to get GroupTypeService
async def get_group_type_service(session: AsyncSession = Depends(get_db_session)) -> GroupTypeService:
    """
    Dependency to get an instance of GroupTypeService.
    """
    return GroupTypeService(GroupTypeRepository(session))

@router.post(
    "/",
    response_model=GroupTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new group type",
    description="Allows a superuser to create a new group type.",
)
async def create_group_type(
    group_type_in: GroupTypeCreate,
    service: GroupTypeService = Depends(get_group_type_service),
) -> GroupTypeModel:
    """
    Create a new group type.
    """
    return await service.create(obj_in=group_type_in)

@router.get(
    "/{group_type_id}",
    response_model=GroupTypeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a group type by ID",
    description="Allows authenticated users to retrieve a specific group type. (TODO: Verify permissions)",
)
async def get_group_type(
    group_type_id: UUID,
    service: GroupTypeService = Depends(get_group_type_service),
    # current_user: UserModel = Depends(get_current_active_user) # TODO: Adjust
) -> GroupTypeModel:
    """
    Get a group type by its ID.
    """
    db_group_type = await service.get_by_id(obj_id=group_type_id)
    if not db_group_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group type not found")
    return db_group_type

@router.get(
    "/",
    response_model=PagedResponse[GroupTypeResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all group types",
    description="Allows authenticated users to retrieve a paginated list of group types. (TODO: Verify permissions)",
)
async def get_all_group_types(
    page_params: PageParams = Depends(paginator),
    service: GroupTypeService = Depends(get_group_type_service),
    # current_user: UserModel = Depends(get_current_active_user) # TODO: Adjust
) -> PagedResponse[GroupTypeModel]:
    """
    Get all group types with pagination.
    """
    group_types = await service.get_multi(
        skip=page_params.skip,
        limit=page_params.limit,
        sort=page_params.sort,
        sort_by=page_params.sort_by
    )
    count = await service.count()
    return PagedResponse(results=group_types, total=count, page=page_params.page, size=page_params.size)

@router.put(
    "/{group_type_id}",
    response_model=GroupTypeResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a group type",
    description="Allows a superuser to update an existing group type.",
)
async def update_group_type(
    group_type_id: UUID,
    group_type_in: GroupTypeUpdate,
    service: GroupTypeService = Depends(get_group_type_service),
) -> GroupTypeModel:
    """
    Update an existing group type.
    """
    db_group_type = await service.get_by_id(obj_id=group_type_id)
    if not db_group_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group type not found")
    return await service.update(obj_db=db_group_type, obj_in=group_type_in)

@router.delete(
    "/{group_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a group type",
    description="Allows a superuser to delete a group type. (Hard delete)", # TODO: Confirm soft delete requirement
)
async def delete_group_type(
    group_type_id: UUID,
    service: GroupTypeService = Depends(get_group_type_service),
) -> None:
    """
    Delete a group type by its ID.
    """
    db_group_type = await service.get_by_id(obj_id=group_type_id)
    if not db_group_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group type not found")
    await service.delete(obj_id=group_type_id)
    return None

# TODO: Consider get_group_type_by_code endpoint if needed.
