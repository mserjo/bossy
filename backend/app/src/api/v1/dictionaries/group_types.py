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
# from app.src.models.auth import User as UserModel # Для доступу на основі ролей

router = APIRouter(
    prefix="/group-types",
    tags=["Dictionary - Group Types"],
    dependencies=[Depends(get_current_active_superuser)] # TODO: Налаштувати дозволи
)

# Залежність для отримання GroupTypeService
async def get_group_type_service(session: AsyncSession = Depends(get_db_session)) -> GroupTypeService:
    """
    Залежність для отримання екземпляра GroupTypeService.
    """
    return GroupTypeService(GroupTypeRepository(session))

@router.post(
    "/",
    response_model=GroupTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створити новий тип групи",
    description="Дозволяє суперкористувачу створювати новий тип групи.",
)
async def create_group_type(
    group_type_in: GroupTypeCreate,
    service: GroupTypeService = Depends(get_group_type_service),
) -> GroupTypeModel:
    """
    Створити новий тип групи.
    """
    return await service.create(obj_in=group_type_in)

@router.get(
    "/{group_type_id}",
    response_model=GroupTypeResponse,
    status_code=status.HTTP_200_OK,
    summary="Отримати тип групи за ID",
    description="Дозволяє автентифікованим користувачам отримувати конкретний тип групи. (TODO: Перевірити дозволи)",
)
async def get_group_type(
    group_type_id: UUID,
    service: GroupTypeService = Depends(get_group_type_service),
    # current_user: UserModel = Depends(get_current_active_user) # TODO: Налаштувати
) -> GroupTypeModel:
    """
    Отримати тип групи за його ID.
    """
    db_group_type = await service.get_by_id(obj_id=group_type_id)
    if not db_group_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип групи не знайдено")
    return db_group_type

@router.get(
    "/",
    response_model=PagedResponse[GroupTypeResponse],
    status_code=status.HTTP_200_OK,
    summary="Отримати всі типи груп",
    description="Дозволяє автентифікованим користувачам отримувати сторінковий список типів груп. (TODO: Перевірити дозволи)",
)
async def get_all_group_types(
    page_params: PageParams = Depends(paginator),
    service: GroupTypeService = Depends(get_group_type_service),
    # current_user: UserModel = Depends(get_current_active_user) # TODO: Налаштувати
) -> PagedResponse[GroupTypeModel]:
    """
    Отримати всі типи груп з пагінацією.
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
    summary="Оновити тип групи",
    description="Дозволяє суперкористувачу оновлювати існуючий тип групи.",
)
async def update_group_type(
    group_type_id: UUID,
    group_type_in: GroupTypeUpdate,
    service: GroupTypeService = Depends(get_group_type_service),
) -> GroupTypeModel:
    """
    Оновити існуючий тип групи.
    """
    db_group_type = await service.get_by_id(obj_id=group_type_id)
    if not db_group_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип групи не знайдено")
    return await service.update(obj_db=db_group_type, obj_in=group_type_in)

@router.delete(
    "/{group_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити тип групи",
    description="Дозволяє суперкористувачу видалити тип групи. (Жорстке видалення)", # TODO: Підтвердити вимогу щодо м'якого видалення
)
async def delete_group_type(
    group_type_id: UUID,
    service: GroupTypeService = Depends(get_group_type_service),
) -> None:
    """
    Видалити тип групи за його ID.
    """
    db_group_type = await service.get_by_id(obj_id=group_type_id)
    if not db_group_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип групи не знайдено")
    await service.delete(obj_id=group_type_id)
    return None

# TODO: Розглянути можливість додавання ендпоінта get_group_type_by_code, якщо потрібно.
