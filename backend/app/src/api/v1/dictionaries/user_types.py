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
# from app.src.models.auth import User as UserModel # Для доступу на основі ролей

router = APIRouter(
    prefix="/user-types",
    tags=["Dictionary - User Types"],
    dependencies=[Depends(get_current_active_superuser)] # TODO: Налаштувати дозволи
)

# Залежність для отримання UserTypeService
async def get_user_type_service(session: AsyncSession = Depends(get_db_session)) -> UserTypeService:
    """
    Залежність для отримання екземпляра UserTypeService.
    """
    return UserTypeService(UserTypeRepository(session))

@router.post(
    "/",
    response_model=UserTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створити новий тип користувача",
    description="Дозволяє суперкористувачу створювати новий тип користувача.",
)
async def create_user_type(
    user_type_in: UserTypeCreate,
    service: UserTypeService = Depends(get_user_type_service),
) -> UserTypeModel:
    """
    Створити новий тип користувача.
    """
    return await service.create(obj_in=user_type_in)

@router.get(
    "/{user_type_id}",
    response_model=UserTypeResponse,
    status_code=status.HTTP_200_OK,
    summary="Отримати тип користувача за ID",
    description="Дозволяє автентифікованим користувачам отримувати конкретний тип користувача. (TODO: Перевірити дозволи)",
)
async def get_user_type(
    user_type_id: UUID,
    service: UserTypeService = Depends(get_user_type_service),
    # current_user: UserModel = Depends(get_current_active_user) # TODO: Налаштувати
) -> UserTypeModel:
    """
    Отримати тип користувача за його ID.
    """
    db_user_type = await service.get_by_id(obj_id=user_type_id)
    if not db_user_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип користувача не знайдено")
    return db_user_type

@router.get(
    "/",
    response_model=PagedResponse[UserTypeResponse],
    status_code=status.HTTP_200_OK,
    summary="Отримати всі типи користувачів",
    description="Дозволяє автентифікованим користувачам отримувати сторінковий список типів користувачів. (TODO: Перевірити дозволи)",
)
async def get_all_user_types(
    page_params: PageParams = Depends(paginator),
    service: UserTypeService = Depends(get_user_type_service),
    # current_user: UserModel = Depends(get_current_active_user) # TODO: Налаштувати
) -> PagedResponse[UserTypeModel]:
    """
    Отримати всі типи користувачів з пагінацією.
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
    summary="Оновити тип користувача",
    description="Дозволяє суперкористувачу оновлювати існуючий тип користувача.",
)
async def update_user_type(
    user_type_id: UUID,
    user_type_in: UserTypeUpdate,
    service: UserTypeService = Depends(get_user_type_service),
) -> UserTypeModel:
    """
    Оновити існуючий тип користувача.
    """
    db_user_type = await service.get_by_id(obj_id=user_type_id)
    if not db_user_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип користувача не знайдено")
    return await service.update(obj_db=db_user_type, obj_in=user_type_in)

@router.delete(
    "/{user_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити тип користувача",
    description="Дозволяє суперкористувачу видалити тип користувача. (Жорстке видалення)", # TODO: Підтвердити вимогу щодо м'якого видалення
)
async def delete_user_type(
    user_type_id: UUID,
    service: UserTypeService = Depends(get_user_type_service),
) -> None:
    """
    Видалити тип користувача за його ID.
    """
    db_user_type = await service.get_by_id(obj_id=user_type_id)
    if not db_user_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип користувача не знайдено")
    await service.delete(obj_id=user_type_id)
    return None

# TODO: Розглянути можливість додавання ендпоінта get_user_type_by_code, якщо потрібно.
