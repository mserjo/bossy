# backend/app/src/api/v1/dictionaries/task_types.py
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_superuser
from app.src.models.dictionaries import TaskType as TaskTypeModel
from app.src.schemas.dictionaries import TaskTypeCreate, TaskTypeUpdate, TaskTypeResponse
from app.src.services.dictionaries import TaskTypeService
from app.src.repositories.dictionaries import TaskTypeRepository
from app.src.core.pagination import PagedResponse, PageParams
from app.src.core.dependencies import paginator
# from app.src.models.auth import User as UserModel # For role-based access

router = APIRouter(
    prefix="/task-types",
    tags=["Dictionary - Task Types"],
    dependencies=[Depends(get_current_active_superuser)] # TODO: Adjust permissions
)

# Dependency to get TaskTypeService
async def get_task_type_service(session: AsyncSession = Depends(get_db_session)) -> TaskTypeService:
    """
    Dependency to get an instance of TaskTypeService.
    """
    return TaskTypeService(TaskTypeRepository(session))

@router.post(
    "/",
    response_model=TaskTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task type",
    description="Allows a superuser to create a new task type.",
)
async def create_task_type(
    task_type_in: TaskTypeCreate,
    service: TaskTypeService = Depends(get_task_type_service),
) -> TaskTypeModel:
    """
    Create a new task type.
    """
    return await service.create(obj_in=task_type_in)

@router.get(
    "/{task_type_id}",
    response_model=TaskTypeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a task type by ID",
    description="Allows authenticated users to retrieve a specific task type. (TODO: Verify permissions)",
)
async def get_task_type(
    task_type_id: UUID,
    service: TaskTypeService = Depends(get_task_type_service),
    # current_user: UserModel = Depends(get_current_active_user) # TODO: Adjust
) -> TaskTypeModel:
    """
    Get a task type by its ID.
    """
    db_task_type = await service.get_by_id(obj_id=task_type_id)
    if not db_task_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task type not found")
    return db_task_type

@router.get(
    "/",
    response_model=PagedResponse[TaskTypeResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all task types",
    description="Allows authenticated users to retrieve a paginated list of task types. (TODO: Verify permissions)",
)
async def get_all_task_types(
    page_params: PageParams = Depends(paginator),
    service: TaskTypeService = Depends(get_task_type_service),
    # current_user: UserModel = Depends(get_current_active_user) # TODO: Adjust
) -> PagedResponse[TaskTypeModel]:
    """
    Get all task types with pagination.
    """
    task_types = await service.get_multi(
        skip=page_params.skip,
        limit=page_params.limit,
        sort=page_params.sort,
        sort_by=page_params.sort_by
    )
    count = await service.count()
    return PagedResponse(results=task_types, total=count, page=page_params.page, size=page_params.size)

@router.put(
    "/{task_type_id}",
    response_model=TaskTypeResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a task type",
    description="Allows a superuser to update an existing task type.",
)
async def update_task_type(
    task_type_id: UUID,
    task_type_in: TaskTypeUpdate,
    service: TaskTypeService = Depends(get_task_type_service),
) -> TaskTypeModel:
    """
    Update an existing task type.
    """
    db_task_type = await service.get_by_id(obj_id=task_type_id)
    if not db_task_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task type not found")
    return await service.update(obj_db=db_task_type, obj_in=task_type_in)

@router.delete(
    "/{task_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task type",
    description="Allows a superuser to delete a task type. (Hard delete)", # TODO: Confirm soft delete requirement
)
async def delete_task_type(
    task_type_id: UUID,
    service: TaskTypeService = Depends(get_task_type_service),
) -> None:
    """
    Delete a task type by its ID.
    """
    db_task_type = await service.get_by_id(obj_id=task_type_id)
    if not db_task_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task type not found")
    await service.delete(obj_id=task_type_id)
    return None

# TODO: Consider get_task_type_by_code endpoint if needed.
