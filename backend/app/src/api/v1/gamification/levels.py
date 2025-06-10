# backend/app/src/api/v1/gamification/levels.py
from typing import List, Optional, Generic, TypeVar # Додано Generic, TypeVar для PaginatedResponse
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from pydantic import BaseModel # Додано BaseModel для PaginatedResponse, якщо визначається локально
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_user, get_current_active_superuser
from app.src.models.auth import User as UserModel
# from app.src.models.gamification import Level as LevelModel # Потрібна модель рівня
# from app.src.models.gamification import UserLevel as UserLevelModel # Потрібна модель рівня користувача
from app.src.schemas.gamification.level import ( # Схеми для рівнів
    LevelCreate,
    LevelUpdate,
    LevelResponse,
    UserLevelResponse
)
# Припускаємо, що ці схеми імпортуються, якщо ні - можна визначити як у users.py або groups.py
from app.src.schemas.pagination import PaginatedResponse, PageParams
from app.src.services.gamification.level import LevelService # Сервіс для визначень рівнів
from app.src.services.gamification.user_level import UserLevelService # Сервіс для рівнів користувачів

router = APIRouter()

# Ендпоінти для управління визначеннями рівнів (Level Definitions)
@router.post(
    "/definitions/", # Шлях відносно /gamification/levels/definitions
    response_model=LevelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створення нового визначення рівня (Адмін/Суперюзер)",
    description="Дозволяє адміністратору або суперюзеру створити нове визначення рівня в системі (наприклад, назва, необхідні бали)."
)
async def create_level_definition(
    level_in: LevelCreate,
    db: AsyncSession = Depends(get_db_session),
    current_admin_user: UserModel = Depends(get_current_active_superuser), # Або інша залежність для адміна
    level_service: LevelService = Depends()
):
    '''
    Створює нове визначення рівня.
    - `name`: Назва рівня.
    - `points_required`: Кількість балів для досягнення.
    - `group_id`: ID групи, якщо рівні специфічні для груп (опціонально).
    '''
    if not hasattr(level_service, 'db_session') or level_service.db_session is None:
        level_service.db_session = db

    created_level_def = await level_service.create_level_definition(
        level_create_schema=level_in,
        requesting_user=current_admin_user # Для перевірки прав, якщо потрібно
    )
    # Сервіс має кидати HTTPException у разі помилок
    return LevelResponse.model_validate(created_level_def)

@router.get(
    "/definitions/",
    response_model=PaginatedResponse[LevelResponse],
    summary="Отримання списку визначень рівнів",
    description="Повертає список усіх визначень рівнів з пагінацією. Може фільтруватися за групою."
)
async def read_level_definitions(
    group_id: Optional[int] = Query(None, description="ID групи для фільтрації визначень рівнів"),
    page_params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    # current_user: UserModel = Depends(get_current_active_user), # Для загального доступу, якщо дозволено
    level_service: LevelService = Depends()
):
    '''
    Отримує список визначень рівнів.
    '''
    if not hasattr(level_service, 'db_session') or level_service.db_session is None:
        level_service.db_session = db

    total_defs, level_defs = await level_service.get_level_definitions(
        group_id=group_id,
        skip=page_params.skip,
        limit=page_params.limit
    )
    return PaginatedResponse[LevelResponse]( # Явно вказуємо тип Generic
        total=total_defs,
        page=page_params.page,
        size=page_params.size,
        results=[LevelResponse.model_validate(ld) for ld in level_defs]
    )

@router.get(
    "/definitions/{level_def_id}",
    response_model=LevelResponse,
    summary="Отримання інформації про визначення рівня за ID",
    description="Повертає детальну інформацію про конкретне визначення рівня."
)
async def read_level_definition_by_id(
    level_def_id: int,
    db: AsyncSession = Depends(get_db_session),
    level_service: LevelService = Depends()
):
    '''
    Отримує інформацію про визначення рівня за його ID.
    '''
    if not hasattr(level_service, 'db_session') or level_service.db_session is None:
        level_service.db_session = db

    level_def = await level_service.get_level_definition_by_id(level_def_id=level_def_id)
    if not level_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Визначення рівня з ID {level_def_id} не знайдено."
        )
    return LevelResponse.model_validate(level_def)

@router.put(
    "/definitions/{level_def_id}",
    response_model=LevelResponse,
    summary="Оновлення визначення рівня (Адмін/Суперюзер)",
    description="Дозволяє адміністратору або суперюзеру оновити існуюче визначення рівня."
)
async def update_level_definition(
    level_def_id: int,
    level_in: LevelUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_admin_user: UserModel = Depends(get_current_active_superuser),
    level_service: LevelService = Depends()
):
    '''
    Оновлює дані визначення рівня.
    '''
    if not hasattr(level_service, 'db_session') or level_service.db_session is None:
        level_service.db_session = db

    updated_level_def = await level_service.update_level_definition(
        level_def_id=level_def_id,
        level_update_schema=level_in,
        requesting_user=current_admin_user
    )
    # Сервіс має кидати HTTPException у разі помилок
    return LevelResponse.model_validate(updated_level_def)

@router.delete(
    "/definitions/{level_def_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення визначення рівня (Адмін/Суперюзер)",
    description="Дозволяє адміністратору або суперюзеру видалити визначення рівня."
)
async def delete_level_definition(
    level_def_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_admin_user: UserModel = Depends(get_current_active_superuser),
    level_service: LevelService = Depends()
):
    '''
    Видаляє визначення рівня.
    '''
    if not hasattr(level_service, 'db_session') or level_service.db_session is None:
        level_service.db_session = db

    success = await level_service.delete_level_definition(
        level_def_id=level_def_id,
        requesting_user=current_admin_user
    )
    if not success: # Сервіс має кидати HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Не вдалося видалити визначення рівня з ID {level_def_id}."
        )
    # HTTP 204 No Content


# Ендпоінти для перегляду рівнів користувачів (User Levels)
@router.get(
    "/user/me", # Шлях відносно /gamification/levels/user/me
    response_model=UserLevelResponse, # Або список, якщо користувач може мати рівні в різних контекстах/групах
    summary="Отримання поточного рівня користувача",
    description="Повертає інформацію про поточний рівень аутентифікованого користувача."
)
async def get_my_user_level(
    # group_id: Optional[int] = Query(None, description="ID групи, якщо рівні визначаються в контексті групи"),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    user_level_service: UserLevelService = Depends()
):
    '''
    Отримує поточний рівень користувача.
    Якщо рівні залежать від групи, `group_id` може бути необхідним параметром.
    '''
    if not hasattr(user_level_service, 'db_session') or user_level_service.db_session is None:
        user_level_service.db_session = db

    user_level_info = await user_level_service.get_user_level_info(
        user_id=current_user.id,
        # group_id=group_id # Якщо потрібно
        requesting_user=current_user
    )
    if not user_level_info:
        # Можливо, користувач ще не має рівня (0 балів) або сталася помилка
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Інформацію про рівень користувача не знайдено.")
    return UserLevelResponse.model_validate(user_level_info)


@router.get(
    "/user/{user_id}", # Шлях відносно /gamification/levels/user/{user_id}
    response_model=UserLevelResponse,
    summary="Отримання рівня конкретного користувача (Адмін/Суперюзер)",
    description="Повертає інформацію про рівень вказаного користувача. Доступно адміністраторам або суперюзерам."
)
async def get_user_level_by_id(
    user_id: int = Path(..., description="ID користувача"),
    # group_id: Optional[int] = Query(None, description="ID групи, якщо рівні визначаються в контексті групи"),
    db: AsyncSession = Depends(get_db_session),
    current_admin_user: UserModel = Depends(get_current_active_superuser), # Або інша адмінська перевірка
    user_level_service: UserLevelService = Depends()
):
    '''
    Отримує рівень вказаного користувача.
    Потрібна перевірка прав `current_admin_user` на перегляд даних `user_id`.
    '''
    if not hasattr(user_level_service, 'db_session') or user_level_service.db_session is None:
        user_level_service.db_session = db

    user_level_info = await user_level_service.get_user_level_info(
        user_id=user_id,
        # group_id=group_id,
        requesting_user=current_admin_user # Передаємо для перевірки прав в сервісі
    )
    if not user_level_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Інформацію про рівень для користувача ID {user_id} не знайдено.")
    return UserLevelResponse.model_validate(user_level_info)


# Міркування:
# 1.  Розділення: Ендпоінти для CRUD визначень рівнів та для перегляду рівнів користувачів.
#     URL-и можуть бути структуровані як `/definitions` для визначень і `/user` для рівнів користувачів,
#     все це під загальним префіксом `/levels` модуля `gamification`.
# 2.  Схеми: `LevelCreate`, `LevelUpdate`, `LevelResponse` для визначень рівнів.
#     `UserLevelResponse` для інформації про рівень користувача (може включати поточні бали, наступний рівень тощо).
# 3.  Сервіси:
#     - `LevelService`: CRUD операції для `LevelModel` (визначення рівнів).
#     - `UserLevelService`: Логіка отримання інформації про рівень користувача (`UserLevelModel`).
#       Розрахунок рівня користувача зазвичай відбувається автоматично на основі балів користувача.
# 4.  Права доступу:
#     - CRUD визначень рівнів: Адміністратори/Суперюзери.
#     - Перегляд свого рівня: Будь-який аутентифікований користувач.
#     - Перегляд чужого рівня: Адміністратори/Суперюзери.
# 5.  Контекст групи: Якщо рівні залежать від групи (`group_id`), це має бути враховано в схемах, сервісах та ендпоінтах.
#     Поки що `group_id` закоментовано як опціональний параметр.
# 6.  Коментарі: Українською мовою.
