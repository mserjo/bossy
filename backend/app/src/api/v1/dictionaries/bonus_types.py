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
# from app.src.models.auth import User as UserModel # Для доступу на основі ролей

router = APIRouter(
    prefix="/bonus-types",
    tags=["Dictionary - Bonus Types"],
    dependencies=[Depends(get_current_active_superuser)] # TODO: Налаштувати дозволи
)

# Залежність для отримання BonusTypeService
async def get_bonus_type_service(session: AsyncSession = Depends(get_db_session)) -> BonusTypeService:
    """
    Залежність для отримання екземпляра BonusTypeService.
    """
    return BonusTypeService(BonusTypeRepository(session))

@router.post(
    "/",
    response_model=BonusTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створити новий тип бонусу",
    description="Дозволяє суперкористувачу створювати новий тип бонусу.",
)
async def create_bonus_type(
    bonus_type_in: BonusTypeCreate,
    service: BonusTypeService = Depends(get_bonus_type_service),
) -> BonusTypeModel:
    """
    Створити новий тип бонусу.
    """
    return await service.create(obj_in=bonus_type_in)

@router.get(
    "/{bonus_type_id}",
    response_model=BonusTypeResponse,
    status_code=status.HTTP_200_OK,
    summary="Отримати тип бонусу за ID",
    description="Дозволяє автентифікованим користувачам отримувати конкретний тип бонусу. (TODO: Перевірити дозволи)",
)
async def get_bonus_type(
    bonus_type_id: UUID,
    service: BonusTypeService = Depends(get_bonus_type_service),
    # current_user: UserModel = Depends(get_current_active_user) # TODO: Налаштувати
) -> BonusTypeModel:
    """
    Отримати тип бонусу за його ID.
    """
    db_bonus_type = await service.get_by_id(obj_id=bonus_type_id)
    if not db_bonus_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип бонусу не знайдено")
    return db_bonus_type

@router.get(
    "/",
    response_model=PagedResponse[BonusTypeResponse],
    status_code=status.HTTP_200_OK,
    summary="Отримати всі типи бонусів",
    description="Дозволяє автентифікованим користувачам отримувати сторінковий список типів бонусів. (TODO: Перевірити дозволи)",
)
async def get_all_bonus_types(
    page_params: PageParams = Depends(paginator),
    service: BonusTypeService = Depends(get_bonus_type_service),
    # current_user: UserModel = Depends(get_current_active_user) # TODO: Налаштувати
) -> PagedResponse[BonusTypeModel]:
    """
    Отримати всі типи бонусів з пагінацією.
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
    summary="Оновити тип бонусу",
    description="Дозволяє суперкористувачу оновлювати існуючий тип бонусу.",
)
async def update_bonus_type(
    bonus_type_id: UUID,
    bonus_type_in: BonusTypeUpdate,
    service: BonusTypeService = Depends(get_bonus_type_service),
) -> BonusTypeModel:
    """
    Оновити існуючий тип бонусу.
    """
    db_bonus_type = await service.get_by_id(obj_id=bonus_type_id)
    if not db_bonus_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип бонусу не знайдено")
    return await service.update(obj_db=db_bonus_type, obj_in=bonus_type_in)

@router.delete(
    "/{bonus_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити тип бонусу",
    description="Дозволяє суперкористувачу видалити тип бонусу. (Жорстке видалення)", # TODO: Підтвердити вимогу щодо м'якого видалення
)
async def delete_bonus_type(
    bonus_type_id: UUID,
    service: BonusTypeService = Depends(get_bonus_type_service),
) -> None:
    """
    Видалити тип бонусу за його ID.
    """
    db_bonus_type = await service.get_by_id(obj_id=bonus_type_id)
    if not db_bonus_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип бонусу не знайдено")
    await service.delete(obj_id=bonus_type_id)
    return None

# TODO: Розглянути можливість додавання ендпоінта get_bonus_type_by_code, якщо потрібно.
