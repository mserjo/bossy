# backend/app/src/api/v1/gamification/ratings.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для перегляду рейтингів користувачів API v1.

Цей модуль надає API для:
- Перегляду рейтингів користувачів у групі (наприклад, топ-N за балами,
  за кількістю виконаних завдань).
- Перегляду позиції поточного користувача в рейтингу.
"""

from fastapi import APIRouter, Depends, Path, Query, status, HTTPException
from typing import List, Optional

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.gamification.rating import UserGroupRatingSchema
# TODO: Розглянути створення Enum для rating_type:
# from backend.app.src.schemas.gamification.enums import RatingTypeEnum
from backend.app.src.services.gamification.rating_service import RatingService
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.api.v1.groups.groups import group_member_permission
from backend.app.src.models.auth.user import UserModel
from backend.app.src.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE # DEFAULT_PAGE тут може бути не потрібний, якщо немає пагінації

logger = get_logger(__name__)
router = APIRouter()

# Ендпоінти для перегляду рейтингів
# Префікс /groups/{group_id}/gamification/ratings

@router.get(
    "",
    response_model=List[UserGroupRatingSchema],
    tags=["Gamification", "Ratings"],
    summary="Отримати рейтинг користувачів у групі"
)
async def get_group_ratings(
    group_id: int = Path(..., description="ID групи"),
    access_check: dict = Depends(group_member_permission),
    db_session: DBSession = Depends(),
    rating_type: str = Query("total_score", description="Тип рейтингу (напр. 'total_score', 'tasks_completed'). TODO: Замінити на Enum."),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100, description="Кількість позицій у рейтингу (топ-N)")
    # page: int = Query(DEFAULT_PAGE, ge=1, description="Номер сторінки, якщо потрібна повна пагінація"), # Поки не використовується
):
    current_user: UserModel = access_check["current_user"]
    logger.info(
        f"Користувач {current_user.email} запитує рейтинг типу '{rating_type}' "
        f"для групи {group_id} (ліміт: {limit})."
    )
    service = RatingService(db_session)

    ratings = await service.get_group_ratings(
        group_id=group_id,
        rating_type=rating_type,
        limit=limit,
        # skip=(page - 1) * limit if page else 0 # Для пагінації
    )

    if not ratings: # Сервіс може повертати порожній список, якщо даних немає
        logger.info(f"Дані для рейтингу типу '{rating_type}' в групі {group_id} відсутні або рейтинг порожній.")
    return ratings

@router.get(
    "/my-position",
    response_model=Optional[UserGroupRatingSchema],
    tags=["Gamification", "Ratings"],
    summary="Отримати свою позицію в рейтингу групи"
)
async def get_my_rating_position_in_group(
    group_id: int = Path(..., description="ID групи"),
    access_check: dict = Depends(group_member_permission),
    db_session: DBSession = Depends(),
    rating_type: str = Query("total_score", description="Тип рейтингу, для якого запитується позиція. TODO: Замінити на Enum.")
):
    current_user: UserModel = access_check["current_user"]
    logger.info(
        f"Користувач {current_user.email} запитує свою позицію в рейтингу типу '{rating_type}' "
        f"в групі {group_id}."
    )
    service = RatingService(db_session)

    my_position = await service.get_user_rating_position(
        user_id=current_user.id,
        group_id=group_id,
        rating_type=rating_type
    )

    if not my_position:
        logger.info(
            f"Позиція користувача {current_user.email} в рейтингу '{rating_type}' "
            f"групи {group_id} не знайдена."
        )
    return my_position

# Роутер буде підключений в backend/app/src/api/v1/gamification/__init__.py
# з префіксом /ratings
# Тоді шляхи будуть:
# /groups/{group_id}/gamification/ratings?rating_type=...&limit=...
# /groups/{group_id}/gamification/ratings/my-position?rating_type=...
