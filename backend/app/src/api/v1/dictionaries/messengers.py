# backend/app/src/api/v1/dictionaries/messengers.py
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_superuser
from app.src.models.dictionaries import MessengerPlatform as MessengerPlatformModel
from app.src.schemas.dictionaries import MessengerPlatformCreate, MessengerPlatformUpdate, MessengerPlatformResponse
from app.src.services.dictionaries import MessengerPlatformService
from app.src.repositories.dictionaries import MessengerPlatformRepository
from app.src.core.pagination import PagedResponse, PageParams
from app.src.core.dependencies import paginator
# from app.src.models.auth import User as UserModel # Для доступу на основі ролей

router = APIRouter(
    prefix="/messenger-platforms",
    tags=["Dictionary - Messenger Platforms"],
    dependencies=[Depends(get_current_active_superuser)] # TODO: Налаштувати дозволи - Тільки суперкористувач згідно із завданням
)

# Залежність для отримання MessengerPlatformService
async def get_messenger_platform_service(session: AsyncSession = Depends(get_db_session)) -> MessengerPlatformService:
    """
    Залежність для отримання екземпляра MessengerPlatformService.
    """
    return MessengerPlatformService(MessengerPlatformRepository(session))

@router.post(
    "/",
    response_model=MessengerPlatformResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створити нову платформу месенджера",
    description="Дозволяє суперкористувачу створювати нову платформу месенджера.",
)
async def create_messenger_platform(
    messenger_platform_in: MessengerPlatformCreate,
    service: MessengerPlatformService = Depends(get_messenger_platform_service),
) -> MessengerPlatformModel:
    """
    Створити нову платформу месенджера.
    """
    return await service.create(obj_in=messenger_platform_in)

@router.get(
    "/{messenger_platform_id}",
    response_model=MessengerPlatformResponse,
    status_code=status.HTTP_200_OK,
    summary="Отримати платформу месенджера за ID",
    description="Дозволяє суперкористувачу отримувати конкретну платформу месенджера.", # Згідно із завданням, налаштовує тільки суперкористувач
)
async def get_messenger_platform(
    messenger_platform_id: UUID,
    service: MessengerPlatformService = Depends(get_messenger_platform_service),
    # current_user: UserModel = Depends(get_current_active_superuser) # Переконатися, що це суперкористувач
) -> MessengerPlatformModel:
    """
    Отримати платформу месенджера за її ID.
    """
    db_messenger_platform = await service.get_by_id(obj_id=messenger_platform_id)
    if not db_messenger_platform:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Платформу месенджера не знайдено")
    return db_messenger_platform

@router.get(
    "/",
    response_model=PagedResponse[MessengerPlatformResponse],
    status_code=status.HTTP_200_OK,
    summary="Отримати всі платформи месенджерів",
    description="Дозволяє суперкористувачу отримувати сторінковий список платформ месенджерів.", # Згідно із завданням, налаштовує тільки суперкористувач
)
async def get_all_messenger_platforms(
    page_params: PageParams = Depends(paginator),
    service: MessengerPlatformService = Depends(get_messenger_platform_service),
    # current_user: UserModel = Depends(get_current_active_superuser) # Переконатися, що це суперкористувач
) -> PagedResponse[MessengerPlatformModel]:
    """
    Отримати всі платформи месенджерів з пагінацією.
    """
    messenger_platforms = await service.get_multi(
        skip=page_params.skip,
        limit=page_params.limit,
        sort=page_params.sort,
        sort_by=page_params.sort_by
    )
    count = await service.count()
    return PagedResponse(results=messenger_platforms, total=count, page=page_params.page, size=page_params.size)

@router.put(
    "/{messenger_platform_id}",
    response_model=MessengerPlatformResponse,
    status_code=status.HTTP_200_OK,
    summary="Оновити платформу месенджера",
    description="Дозволяє суперкористувачу оновлювати існуючу платформу месенджера.",
)
async def update_messenger_platform(
    messenger_platform_id: UUID,
    messenger_platform_in: MessengerPlatformUpdate,
    service: MessengerPlatformService = Depends(get_messenger_platform_service),
) -> MessengerPlatformModel:
    """
    Оновити існуючу платформу месенджера.
    """
    db_messenger_platform = await service.get_by_id(obj_id=messenger_platform_id)
    if not db_messenger_platform:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Платформу месенджера не знайдено")
    return await service.update(obj_db=db_messenger_platform, obj_in=messenger_platform_in)

@router.delete(
    "/{messenger_platform_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити платформу месенджера",
    description="Дозволяє суперкористувачу видалити платформу месенджера. (Жорстке видалення)", # TODO: Підтвердити м'яке видалення
)
async def delete_messenger_platform(
    messenger_platform_id: UUID,
    service: MessengerPlatformService = Depends(get_messenger_platform_service),
) -> None:
    """
    Видалити платформу месенджера за її ID.
    """
    db_messenger_platform = await service.get_by_id(obj_id=messenger_platform_id)
    if not db_messenger_platform:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Платформу месенджера не знайдено")
    await service.delete(obj_id=messenger_platform_id)
    return None

# TODO: Розглянути можливість додавання ендпоінта get_messenger_platform_by_code, якщо потрібно.
