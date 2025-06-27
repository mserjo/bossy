# backend/app/src/api/v1/gamification/ratings.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для перегляду рейтингів користувачів API v1.

Цей модуль надає API для:
- Перегляду рейтингів користувачів у групі (наприклад, топ-N за балами, за кількістю виконаних завдань).
- Можливо, перегляду позиції поточного користувача в рейтингу.
"""

from fastapi import APIRouter, Depends, Path, Query
from typing import List, Optional

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.gamification.rating import UserGroupRatingSchema # Схема для представлення позиції в рейтингу
from backend.app.src.services.gamification.rating_service import RatingService
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.api.v1.groups.groups import group_member_permission
from backend.app.src.models.auth.user import UserModel
from backend.app.src.core.constants import DEFAULT_PAGE_SIZE # Для ліміту в топі

logger = get_logger(__name__)
router = APIRouter()

# Ендпоінти для перегляду рейтингів
# Префікс /groups/{group_id}/gamification/ratings

@router.get(
    "", # Відносно /groups/{group_id}/gamification/ratings
    response_model=List[UserGroupRatingSchema],
    tags=["Gamification", "Ratings"],
    summary="Отримати рейтинг користувачів у групі"
)
async def get_group_ratings(
    group_id: int = Path(..., description="ID групи"),
    access_check: dict = Depends(group_member_permission),
    db_session: DBSession = Depends(),
    # Параметри для типу рейтингу та пагінації/ліміту
    rating_type: str = Query("total_score", description="Тип рейтингу (напр. 'total_score', 'tasks_completed')"),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100, description="Кількість позицій у рейтингу")
):
    current_user: UserModel = access_check["current_user"]
    logger.info(
        f"Користувач {current_user.email} запитує рейтинг типу '{rating_type}' "
        f"для групи {group_id} (ліміт: {limit})."
    )
    service = RatingService(db_session)

    # Сервіс повинен обробляти різні типи рейтингів
    ratings = await service.get_group_ratings(
        group_id=group_id,
        rating_type=rating_type,
        limit=limit
    )

    if not ratings:
        logger.info(f"Дані для рейтингу типу '{rating_type}' в групі {group_id} відсутні.")
        # Повертаємо порожній список, а не 404, бо рейтинг може бути просто порожнім

    return ratings

@router.get(
    "/my-position", # Відносно /groups/{group_id}/gamification/ratings
    response_model=Optional[UserGroupRatingSchema], # Може бути None, якщо користувач не в рейтингу
    tags=["Gamification", "Ratings"],
    summary="Отримати свою позицію в рейтингу групи"
)
async def get_my_rating_position_in_group(
    group_id: int = Path(..., description="ID групи"),
    access_check: dict = Depends(group_member_permission),
    db_session: DBSession = Depends(),
    rating_type: str = Query("total_score", description="Тип рейтингу, для якого запитується позиція")
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
            f"групи {group_id} не знайдена (можливо, ще немає активності)."
        )
        # Повертаємо 200 з порожнім тілом або null, якщо Optional

    return my_position

# Роутер буде підключений в backend/app/src/api/v1/gamification/__init__.py
