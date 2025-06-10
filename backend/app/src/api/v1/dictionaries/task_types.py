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
# from app.src.models.auth import User as UserModel # Для доступу на основі ролей

router = APIRouter(
    prefix="/task-types",
    tags=["Dictionary - Task Types"],
    dependencies=[Depends(get_current_active_superuser)] # TODO: Налаштувати дозволи
)

# Залежність для отримання TaskTypeService
async def get_task_type_service(session: AsyncSession = Depends(get_db_session)) -> TaskTypeService:
    """
    Залежність для отримання екземпляра TaskTypeService.
    """
    return TaskTypeService(TaskTypeRepository(session))

@router.post(
    "/",
    response_model=TaskTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створити новий тип завдання",
    description="Дозволяє суперкористувачу створювати новий тип завдання.",
)
async def create_task_type(
    task_type_in: TaskTypeCreate,
    service: TaskTypeService = Depends(get_task_type_service),
) -> TaskTypeModel:
    """
    Створити новий тип завдання.
    """
    return await service.create(obj_in=task_type_in)

@router.get(
    "/{task_type_id}",
    response_model=TaskTypeResponse,
    status_code=status.HTTP_200_OK,
    summary="Отримати тип завдання за ID",
    description="Дозволяє автентифікованим користувачам отримувати конкретний тип завдання. (TODO: Перевірити дозволи)",
)
async def get_task_type(
    task_type_id: UUID,
    service: TaskTypeService = Depends(get_task_type_service),
    # current_user: UserModel = Depends(get_current_active_user) # TODO: Налаштувати
) -> TaskTypeModel:
    """
    Отримати тип завдання за його ID.
    """
    db_task_type = await service.get_by_id(obj_id=task_type_id)
    if not db_task_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип завдання не знайдено")
    return db_task_type

@router.get(
    "/",
    response_model=PagedResponse[TaskTypeResponse],
    status_code=status.HTTP_200_OK,
    summary="Отримати всі типи завдань",
    description="Дозволяє автентифікованим користувачам отримувати сторінковий список типів завдань. (TODO: Перевірити дозволи)",
)
async def get_all_task_types(
    page_params: PageParams = Depends(paginator),
    service: TaskTypeService = Depends(get_task_type_service),
    # current_user: UserModel = Depends(get_current_active_user) # TODO: Налаштувати
) -> PagedResponse[TaskTypeModel]:
    """
    Отримати всі типи завдань з пагінацією.
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
    summary="Оновити тип завдання",
    description="Дозволяє суперкористувачу оновлювати існуючий тип завдання.",
)
async def update_task_type(
    task_type_id: UUID,
    task_type_in: TaskTypeUpdate,
    service: TaskTypeService = Depends(get_task_type_service),
) -> TaskTypeModel:
    """
    Оновити існуючий тип завдання.
    """
    db_task_type = await service.get_by_id(obj_id=task_type_id)
    if not db_task_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип завдання не знайдено")
    return await service.update(obj_db=db_task_type, obj_in=task_type_in)

@router.delete(
    "/{task_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити тип завдання",
    description="Дозволяє суперкористувачу видалити тип завдання. (Жорстке видалення)", # TODO: Підтвердити вимогу щодо м'якого видалення
)
async def delete_task_type(
    task_type_id: UUID,
    service: TaskTypeService = Depends(get_task_type_service),
) -> None:
    """
    Видалити тип завдання за його ID.
    """
    db_task_type = await service.get_by_id(obj_id=task_type_id)
    if not db_task_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип завдання не знайдено")
    await service.delete(obj_id=task_type_id)
    return None

# TODO: Розглянути можливість додавання ендпоінта get_task_type_by_code, якщо потрібно.
