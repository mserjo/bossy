# backend/app/src/api/v1/dictionaries/user_types.py
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_superuser
from app.src.models.dictionaries import UserType as UserTypeModel
from app.src.schemas.dictionaries import UserTypeCreate, UserTypeUpdate, UserTypeResponse
from app.src.services.dictionaries import UserTypeService
from app.src.repositories.dictionaries import UserTypeRepository
from app.src.core.pagination import PagedResponse, PageParams
from app.src.core.dependencies import paginator
# from app.src.models.auth import User as UserModel # For role-based access

router = APIRouter(
    prefix="/user-types",
    tags=["Dictionary - User Types"],
    dependencies=[Depends(get_current_active_superuser)] # TODO: Adjust permissions
)

# Dependency to get UserTypeService
async def get_user_type_service(session: AsyncSession = Depends(get_db_session)) -> UserTypeService:
    """
    Dependency to get an instance of UserTypeService.
    """
    return UserTypeService(UserTypeRepository(session))

@router.post(
    "/",
    response_model=UserTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user type",
    description="Allows a superuser to create a new user type.",
)
async def create_user_type(
    user_type_in: UserTypeCreate,
    service: UserTypeService = Depends(get_user_type_service),
) -> UserTypeModel:
    """
    Create a new user type.
    """
    return await service.create(obj_in=user_type_in)

@router.get(
    "/{user_type_id}",
    response_model=UserTypeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a user type by ID",
    description="Allows authenticated users to retrieve a specific user type. (TODO: Verify permissions)",
)
async def get_user_type(
    user_type_id: UUID,
    service: UserTypeService = Depends(get_user_type_service),
    # current_user: UserModel = Depends(get_current_active_user) # TODO: Adjust
) -> UserTypeModel:
    """
    Get a user type by its ID.
    """
    db_user_type = await service.get_by_id(obj_id=user_type_id)
    if not db_user_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User type not found")
    return db_user_type

@router.get(
    "/",
    response_model=PagedResponse[UserTypeResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all user types",
    description="Allows authenticated users to retrieve a paginated list of user types. (TODO: Verify permissions)",
)
async def get_all_user_types(
    page_params: PageParams = Depends(paginator),
    service: UserTypeService = Depends(get_user_type_service),
    # current_user: UserModel = Depends(get_current_active_user) # TODO: Adjust
) -> PagedResponse[UserTypeModel]:
    """
    Get all user types with pagination.
    """
    user_types = await service.get_multi(
        skip=page_params.skip,
        limit=page_params.limit,
        sort=page_params.sort,
        sort_by=page_params.sort_by
    )
    count = await service.count()
    return PagedResponse(results=user_types, total=count, page=page_params.page, size=page_params.size)

@router.put(
    "/{user_type_id}",
    response_model=UserTypeResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a user type",
    description="Allows a superuser to update an existing user type.",
)
async def update_user_type(
    user_type_id: UUID,
    user_type_in: UserTypeUpdate,
    service: UserTypeService = Depends(get_user_type_service),
) -> UserTypeModel:
    """
    Update an existing user type.
    """
    db_user_type = await service.get_by_id(obj_id=user_type_id)
    if not db_user_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User type not found")
    return await service.update(obj_db=db_user_type, obj_in=user_type_in)

@router.delete(
    "/{user_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user type",
    description="Allows a superuser to delete a user type. (Hard delete)", # TODO: Confirm soft delete requirement
)
async def delete_user_type(
    user_type_id: UUID,
    service: UserTypeService = Depends(get_user_type_service),
) -> None:
    """
    Delete a user type by its ID.
    """
    db_user_type = await service.get_by_id(obj_id=user_type_id)
    if not db_user_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User type not found")
    await service.delete(obj_id=user_type_id)
    return None

# TODO: Consider get_user_type_by_code endpoint if needed.
