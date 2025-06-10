# backend/app/src/api/v1/gamification/badges.py
from typing import List, Optional, Generic, TypeVar # Додано Generic, TypeVar для PaginatedResponse
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from pydantic import BaseModel # Додано BaseModel для PaginatedResponse, якщо визначається локально
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_user, get_current_active_superuser
from app.src.models.auth import User as UserModel
# from app.src.models.gamification import Badge as BadgeModel # Потрібна модель бейджа
from app.src.schemas.gamification.badge import ( # Схеми для бейджів
    BadgeCreate,
    BadgeUpdate,
    BadgeResponse
)
# Припускаємо, що ці схеми імпортуються, якщо ні - можна визначити як у users.py або groups.py
from app.src.schemas.pagination import PaginatedResponse, PageParams
from app.src.services.gamification.badge import BadgeService # Сервіс для визначень бейджів

router = APIRouter()

@router.post(
    "/", # Шлях відносно /gamification/badges
    response_model=BadgeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створення нового визначення бейджа (Адмін/Суперюзер)",
    description="Дозволяє адміністратору або суперюзеру створити нове визначення бейджа (назва, опис, іконка, критерії)."
)
async def create_badge_definition(
    badge_in: BadgeCreate,
    db: AsyncSession = Depends(get_db_session),
    current_admin_user: UserModel = Depends(get_current_active_superuser), # Або інша залежність для адміна
    badge_service: BadgeService = Depends()
):
    '''
    Створює нове визначення бейджа.
    - `name`: Назва бейджа.
    - `description`: Опис.
    - `icon_url`: URL іконки.
    - `criteria`: Критерії для отримання (може бути текстовим описом або структурованими даними).
    - `group_id`: ID групи, якщо бейдж специфічний для групи (опціонально).
    '''
    if not hasattr(badge_service, 'db_session') or badge_service.db_session is None:
        badge_service.db_session = db

    created_badge_def = await badge_service.create_badge_definition(
        badge_create_schema=badge_in,
        requesting_user=current_admin_user # Для перевірки прав, якщо потрібно
    )
    # Сервіс має кидати HTTPException у разі помилок
    return BadgeResponse.model_validate(created_badge_def)

@router.get(
    "/",
    response_model=PaginatedResponse[BadgeResponse],
    summary="Отримання списку визначень бейджів",
    description="Повертає список усіх визначень бейджів з пагінацією. Може фільтруватися за групою."
)
async def read_badge_definitions(
    group_id: Optional[int] = Query(None, description="ID групи для фільтрації визначень бейджів"),
    page_params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    # current_user: UserModel = Depends(get_current_active_user), # Для загального доступу, якщо дозволено
    badge_service: BadgeService = Depends()
):
    '''
    Отримує список визначень бейджів.
    '''
    if not hasattr(badge_service, 'db_session') or badge_service.db_session is None:
        badge_service.db_session = db

    total_defs, badge_defs = await badge_service.get_badge_definitions(
        group_id=group_id,
        skip=page_params.skip,
        limit=page_params.limit
        # requesting_user=current_user # Якщо потрібна перевірка доступу на перегляд
    )
    return PaginatedResponse[BadgeResponse]( # Явно вказуємо тип Generic
        total=total_defs,
        page=page_params.page,
        size=page_params.size,
        results=[BadgeResponse.model_validate(bd) for bd in badge_defs]
    )

@router.get(
    "/{badge_def_id}",
    response_model=BadgeResponse,
    summary="Отримання інформації про визначення бейджа за ID",
    description="Повертає детальну інформацію про конкретне визначення бейджа."
)
async def read_badge_definition_by_id(
    badge_def_id: int,
    db: AsyncSession = Depends(get_db_session),
    badge_service: BadgeService = Depends()
    # current_user: UserModel = Depends(get_current_active_user) # Якщо потрібна перевірка доступу
):
    '''
    Отримує інформацію про визначення бейджа за його ID.
    '''
    if not hasattr(badge_service, 'db_session') or badge_service.db_session is None:
        badge_service.db_session = db

    badge_def = await badge_service.get_badge_definition_by_id(
        badge_def_id=badge_def_id
        # requesting_user=current_user # Якщо потрібна перевірка доступу
        )
    if not badge_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Визначення бейджа з ID {badge_def_id} не знайдено."
        )
    return BadgeResponse.model_validate(badge_def)

@router.put(
    "/{badge_def_id}",
    response_model=BadgeResponse,
    summary="Оновлення визначення бейджа (Адмін/Суперюзер)",
    description="Дозволяє адміністратору або суперюзеру оновити існуюче визначення бейджа."
)
async def update_badge_definition(
    badge_def_id: int,
    badge_in: BadgeUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_admin_user: UserModel = Depends(get_current_active_superuser),
    badge_service: BadgeService = Depends()
):
    '''
    Оновлює дані визначення бейджа.
    '''
    if not hasattr(badge_service, 'db_session') or badge_service.db_session is None:
        badge_service.db_session = db

    updated_badge_def = await badge_service.update_badge_definition(
        badge_def_id=badge_def_id,
        badge_update_schema=badge_in,
        requesting_user=current_admin_user
    )
    # Сервіс має кидати HTTPException у разі помилок
    return BadgeResponse.model_validate(updated_badge_def)

@router.delete(
    "/{badge_def_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення визначення бейджа (Адмін/Суперюзер)",
    description="Дозволяє адміністратору або суперюзеру видалити визначення бейджа."
)
async def delete_badge_definition(
    badge_def_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_admin_user: UserModel = Depends(get_current_active_superuser),
    badge_service: BadgeService = Depends()
):
    '''
    Видаляє визначення бейджа.
    '''
    if not hasattr(badge_service, 'db_session') or badge_service.db_session is None:
        badge_service.db_session = db

    success = await badge_service.delete_badge_definition(
        badge_def_id=badge_def_id,
        requesting_user=current_admin_user
    )
    if not success: # Сервіс має кидати HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Не вдалося видалити визначення бейджа з ID {badge_def_id}."
        )
    # HTTP 204 No Content

# Міркування:
# 1.  Призначення: Цей модуль керує тільки визначеннями бейджів (як вони виглядають, як їх отримати).
#     Фактичне нагородження користувачів бейджами (UserAchievements) буде оброблятися окремо,
#     можливо, автоматично сервісами або через окремий API для адмінів (якщо потрібне ручне нагородження).
# 2.  Схеми: `BadgeCreate`, `BadgeUpdate`, `BadgeResponse` з `app.src.schemas.gamification.badge`.
# 3.  Сервіс `BadgeService`: CRUD операції для `BadgeModel` (визначення бейджів).
# 4.  Права доступу: CRUD визначень бейджів - Адміністратори/Суперюзери. Перегляд списку - можливо, всі користувачі.
#     Поточна реалізація GET-ендпоінтів не вимагає `current_user` для перегляду, але це може бути додано в сервісі.
# 5.  Контекст групи: Якщо бейджі залежать від групи (`group_id`), це має бути враховано.
# 6.  Коментарі: Українською мовою.
# 7.  URL-и: Цей роутер буде підключений до `gamification_router` з префіксом `/badges`.
