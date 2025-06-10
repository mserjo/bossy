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
# Припускаючи, що UserModel потрібен для доступу на основі ролей, імпортуйте його
# from app.src.models.auth import User as UserModel

router = APIRouter(
    prefix="/user-roles",
    tags=["Dictionary - User Roles"],
    dependencies=[Depends(get_current_active_superuser)] # TODO: Налаштувати дозволи згідно з technical_task.txt
)

# Залежність для отримання UserRoleService
async def get_user_role_service(session: AsyncSession = Depends(get_db_session)) -> UserRoleService:
    """
    Залежність для отримання екземпляра UserRoleService.

    Args:
        session: Сесія бази даних.

    Returns:
        Екземпляр UserRoleService.
    """
    return UserRoleService(UserRoleRepository(session))

@router.post(
    "/",
    response_model=UserRoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створити нову роль користувача",
    description="Дозволяє суперкористувачу створювати нову роль користувача для системи.",
)
async def create_user_role(
    user_role_in: UserRoleCreate,
    service: UserRoleService = Depends(get_user_role_service),
) -> UserRoleModel:
    """
    Створити нову роль користувача.

    Args:
        user_role_in: Дані ролі користувача для створення.
        service: Сервіс ролей користувачів.

    Returns:
        Створена роль користувача.
    """
    # TODO: Додати логіку на основі technical_task.txt для конкретних ролей, якщо потрібно
    return await service.create(obj_in=user_role_in)

@router.get(
    "/{user_role_id}",
    response_model=UserRoleResponse,
    status_code=status.HTTP_200_OK,
    summary="Отримати роль користувача за ID",
    description="Дозволяє будь-якому автентифікованому користувачу (TODO: перевірити це на основі завдання) отримати конкретну роль користувача за її ID.",
)
async def get_user_role(
    user_role_id: UUID,
    service: UserRoleService = Depends(get_user_role_service),
    # current_user: UserModel = Depends(get_current_active_user) # TODO: Додати, якщо потрібно для доступу на основі ролей
) -> UserRoleModel:
    """
    Отримати роль користувача за її ID.

    Args:
        user_role_id: ID ролі користувача для отримання.
        service: Сервіс ролей користувачів.

    Returns:
        Роль користувача із зазначеним ID.

    Raises:
        HTTPException: Якщо роль користувача не знайдено.
    """
    db_user_role = await service.get_by_id(obj_id=user_role_id)
    if not db_user_role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Роль користувача не знайдено")
    return db_user_role

@router.get(
    "/",
    response_model=PagedResponse[UserRoleResponse],
    status_code=status.HTTP_200_OK,
    summary="Отримати всі ролі користувачів",
    description="Дозволяє будь-якому автентифікованому користувачу (TODO: перевірити це на основі завдання) отримати сторінковий список усіх ролей користувачів.",
)
async def get_all_user_roles(
    page_params: PageParams = Depends(paginator),
    service: UserRoleService = Depends(get_user_role_service),
    # current_user: UserModel = Depends(get_current_active_user) # TODO: Додати, якщо потрібно для доступу на основі ролей
) -> PagedResponse[UserRoleModel]:
    """
    Отримати всі ролі користувачів з пагінацією.

    Args:
        page_params: Параметри пагінації.
        service: Сервіс ролей користувачів.

    Returns:
        Сторінковий список ролей користувачів.
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
    summary="Оновити роль користувача",
    description="Дозволяє суперкористувачу оновлювати існуючу роль користувача.",
)
async def update_user_role(
    user_role_id: UUID,
    user_role_in: UserRoleUpdate,
    service: UserRoleService = Depends(get_user_role_service),
) -> UserRoleModel:
    """
    Оновити існуючу роль користувача.

    Args:
        user_role_id: ID ролі користувача для оновлення.
        user_role_in: Нові дані ролі користувача.
        service: Сервіс ролей користувачів.

    Returns:
        Оновлена роль користувача.

    Raises:
        HTTPException: Якщо роль користувача не знайдено.
    """
    db_user_role = await service.get_by_id(obj_id=user_role_id)
    if not db_user_role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Роль користувача не знайдено")
    # TODO: Додати логіку на основі technical_task.txt для конкретних ролей, якщо потрібно
    return await service.update(obj_db=db_user_role, obj_in=user_role_in)

@router.delete(
    "/{user_role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити роль користувача",
    description="Дозволяє суперкористувачу видалити роль користувача. Це жорстке видалення.", # TODO: Підтвердити, чи потрібне м'яке видалення
)
async def delete_user_role(
    user_role_id: UUID,
    service: UserRoleService = Depends(get_user_role_service),
) -> None:
    """
    Видалити роль користувача за її ID.

    Args:
        user_role_id: ID ролі користувача для видалення.
        service: Сервіс ролей користувачів.

    Raises:
        HTTPException: Якщо роль користувача не знайдено.
    """
    db_user_role = await service.get_by_id(obj_id=user_role_id)
    if not db_user_role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Роль користувача не знайдено")
    # TODO: Додати логіку на основі technical_task.txt для конкретних ролей, якщо потрібно
    await service.delete(obj_id=user_role_id)
    return None

# TODO: Додати більш конкретні ендпоінти, якщо це вимагається technical_task.txt
# Наприклад, get_user_role_by_code, якщо 'code' є унікальним полем і використовується для пошуку.
