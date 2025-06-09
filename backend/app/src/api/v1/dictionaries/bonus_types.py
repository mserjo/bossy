# backend/app/src/api/v1/dictionaries/bonus_types.py
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_superuser
from app.src.models.dictionaries import BonusType as BonusTypeModel
from app.src.schemas.dictionaries import BonusTypeCreate, BonusTypeUpdate, BonusTypeResponse
from app.src.services.dictionaries import BonusTypeService
from app.src.repositories.dictionaries import BonusTypeRepository
from app.src.core.pagination import PagedResponse, PageParams
from app.src.core.dependencies import paginator
# from app.src.models.auth import User as UserModel # For role-based access

router = APIRouter(
    prefix="/bonus-types",
    tags=["Dictionary - Bonus Types"],
    dependencies=[Depends(get_current_active_superuser)] # TODO: Adjust permissions
)

# Dependency to get BonusTypeService
async def get_bonus_type_service(session: AsyncSession = Depends(get_db_session)) -> BonusTypeService:
    """
    Dependency to get an instance of BonusTypeService.
    """
    return BonusTypeService(BonusTypeRepository(session))

@router.post(
    "/",
    response_model=BonusTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new bonus type",
    description="Allows a superuser to create a new bonus type.",
)
async def create_bonus_type(
    bonus_type_in: BonusTypeCreate,
    service: BonusTypeService = Depends(get_bonus_type_service),
) -> BonusTypeModel:
    """
    Create a new bonus type.
    """
    return await service.create(obj_in=bonus_type_in)

@router.get(
    "/{bonus_type_id}",
    response_model=BonusTypeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a bonus type by ID",
    description="Allows authenticated users to retrieve a specific bonus type. (TODO: Verify permissions)",
)
async def get_bonus_type(
    bonus_type_id: UUID,
    service: BonusTypeService = Depends(get_bonus_type_service),
    # current_user: UserModel = Depends(get_current_active_user) # TODO: Adjust
) -> BonusTypeModel:
    """
    Get a bonus type by its ID.
    """
    db_bonus_type = await service.get_by_id(obj_id=bonus_type_id)
    if not db_bonus_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bonus type not found")
    return db_bonus_type

@router.get(
    "/",
    response_model=PagedResponse[BonusTypeResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all bonus types",
    description="Allows authenticated users to retrieve a paginated list of bonus types. (TODO: Verify permissions)",
)
async def get_all_bonus_types(
    page_params: PageParams = Depends(paginator),
    service: BonusTypeService = Depends(get_bonus_type_service),
    # current_user: UserModel = Depends(get_current_active_user) # TODO: Adjust
) -> PagedResponse[BonusTypeModel]:
    """
    Get all bonus types with pagination.
    """
    bonus_types = await service.get_multi(
        skip=page_params.skip,
        limit=page_params.limit,
        sort=page_params.sort,
        sort_by=page_params.sort_by
    )
    count = await service.count()
    return PagedResponse(results=bonus_types, total=count, page=page_params.page, size=page_params.size)

@router.put(
    "/{bonus_type_id}",
    response_model=BonusTypeResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a bonus type",
    description="Allows a superuser to update an existing bonus type.",
)
async def update_bonus_type(
    bonus_type_id: UUID,
    bonus_type_in: BonusTypeUpdate,
    service: BonusTypeService = Depends(get_bonus_type_service),
) -> BonusTypeModel:
    """
    Update an existing bonus type.
    """
    db_bonus_type = await service.get_by_id(obj_id=bonus_type_id)
    if not db_bonus_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bonus type not found")
    return await service.update(obj_db=db_bonus_type, obj_in=bonus_type_in)

@router.delete(
    "/{bonus_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a bonus type",
    description="Allows a superuser to delete a bonus type. (Hard delete)", # TODO: Confirm soft delete requirement
)
async def delete_bonus_type(
    bonus_type_id: UUID,
    service: BonusTypeService = Depends(get_bonus_type_service),
) -> None:
    """
    Delete a bonus type by its ID.
    """
    db_bonus_type = await service.get_by_id(obj_id=bonus_type_id)
    if not db_bonus_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bonus type not found")
    await service.delete(obj_id=bonus_type_id)
    return None

# TODO: Consider get_bonus_type_by_code endpoint if needed.
