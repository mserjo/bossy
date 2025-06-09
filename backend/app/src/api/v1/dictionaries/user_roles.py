# backend/app/src/api/v1/dictionaries/user_roles.py
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_superuser
from app.src.models.dictionaries import UserRole as UserRoleModel
from app.src.schemas.dictionaries import UserRoleCreate, UserRoleUpdate, UserRoleResponse
from app.src.services.dictionaries import UserRoleService
from app.src.repositories.dictionaries import UserRoleRepository
from app.src.core.pagination import PagedResponse, PageParams
from app.src.core.dependencies import paginator
# Assuming UserModel is needed for role-based access, import it
# from app.src.models.auth import User as UserModel

router = APIRouter(
    prefix="/user-roles",
    tags=["Dictionary - User Roles"],
    dependencies=[Depends(get_current_active_superuser)] # TODO: Adjust permissions as per technical_task.txt
)

# Dependency to get UserRoleService
async def get_user_role_service(session: AsyncSession = Depends(get_db_session)) -> UserRoleService:
    """
    Dependency to get an instance of UserRoleService.

    Args:
        session: The database session.

    Returns:
        An instance of UserRoleService.
    """
    return UserRoleService(UserRoleRepository(session))

@router.post(
    "/",
    response_model=UserRoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user role",
    description="Allows a superuser to create a new user role for the system.",
)
async def create_user_role(
    user_role_in: UserRoleCreate,
    service: UserRoleService = Depends(get_user_role_service),
) -> UserRoleModel:
    """
    Create a new user role.

    Args:
        user_role_in: The user role data to create.
        service: The user role service.

    Returns:
        The created user role.
    """
    # TODO: Add logic based on technical_task.txt for specific roles if needed
    return await service.create(obj_in=user_role_in)

@router.get(
    "/{user_role_id}",
    response_model=UserRoleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a user role by ID",
    description="Allows any authenticated user (TODO: verify this based on task) to retrieve a specific user role by its ID.",
)
async def get_user_role(
    user_role_id: UUID,
    service: UserRoleService = Depends(get_user_role_service),
    # current_user: UserModel = Depends(get_current_active_user) # TODO: Add if needed for role-based access
) -> UserRoleModel:
    """
    Get a user role by its ID.

    Args:
        user_role_id: The ID of the user role to retrieve.
        service: The user role service.

    Returns:
        The user role with the given ID.

    Raises:
        HTTPException: If the user role is not found.
    """
    db_user_role = await service.get_by_id(obj_id=user_role_id)
    if not db_user_role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User role not found")
    return db_user_role

@router.get(
    "/",
    response_model=PagedResponse[UserRoleResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all user roles",
    description="Allows any authenticated user (TODO: verify this based on task) to retrieve a paginated list of all user roles.",
)
async def get_all_user_roles(
    page_params: PageParams = Depends(paginator),
    service: UserRoleService = Depends(get_user_role_service),
    # current_user: UserModel = Depends(get_current_active_user) # TODO: Add if needed for role-based access
) -> PagedResponse[UserRoleModel]:
    """
    Get all user roles with pagination.

    Args:
        page_params: Pagination parameters.
        service: The user role service.

    Returns:
        A paginated list of user roles.
    """
    user_roles = await service.get_multi(
        skip=page_params.skip,
        limit=page_params.limit,
        sort=page_params.sort,
        sort_by=page_params.sort_by
    )
    count = await service.count()
    return PagedResponse(results=user_roles, total=count, page=page_params.page, size=page_params.size)

@router.put(
    "/{user_role_id}",
    response_model=UserRoleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a user role",
    description="Allows a superuser to update an existing user role.",
)
async def update_user_role(
    user_role_id: UUID,
    user_role_in: UserRoleUpdate,
    service: UserRoleService = Depends(get_user_role_service),
) -> UserRoleModel:
    """
    Update an existing user role.

    Args:
        user_role_id: The ID of the user role to update.
        user_role_in: The new user role data.
        service: The user role service.

    Returns:
        The updated user role.

    Raises:
        HTTPException: If the user role is not found.
    """
    db_user_role = await service.get_by_id(obj_id=user_role_id)
    if not db_user_role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User role not found")
    # TODO: Add logic based on technical_task.txt for specific roles if needed
    return await service.update(obj_db=db_user_role, obj_in=user_role_in)

@router.delete(
    "/{user_role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user role",
    description="Allows a superuser to delete a user role. This is a hard delete.", # TODO: Confirm if soft delete is needed
)
async def delete_user_role(
    user_role_id: UUID,
    service: UserRoleService = Depends(get_user_role_service),
) -> None:
    """
    Delete a user role by its ID.

    Args:
        user_role_id: The ID of the user role to delete.
        service: The user role service.

    Raises:
        HTTPException: If the user role is not found.
    """
    db_user_role = await service.get_by_id(obj_id=user_role_id)
    if not db_user_role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User role not found")
    # TODO: Add logic based on technical_task.txt for specific roles if needed
    await service.delete(obj_id=user_role_id)
    return None

# TODO: Add more specific endpoints if required by technical_task.txt
# For example, get_user_role_by_code if 'code' is a unique field and used for lookup.
