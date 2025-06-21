# backend/app/src/api/v1/gamification/ratings.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для перегляду рейтингів користувачів та таблиць лідерів.

Рейтинги зазвичай розраховуються на основі накопичених бонусних балів
в межах групи та за певний період (наприклад, "за весь час", "поточний місяць").

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from typing import Optional  # List, Generic, TypeVar, BaseModel не потрібні, якщо імпортуються з core
from uuid import UUID  # ID тепер UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession  # Не використовується прямо

from backend.app.src.api.dependencies import (
    get_api_db_session, get_current_active_user,
    paginator,  # paginator може не використовуватися, якщо лідерборд має власний ліміт
    get_group_membership_service
)
# TODO: Використати залежність для перевірки членства в групі або прав суперюзера
from backend.app.src.api.v1.groups.groups import check_group_view_permission

from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.gamification.rating import (
    UserGroupRatingResponse,  # Для індивідуального рейтингу користувача
    GroupLeaderboardResponse  # Для відповіді лідерборду
)
from backend.app.src.core.pagination import PageParams  # PagedResponse тут може не знадобитися
from backend.app.src.services.gamification.rating import UserRatingService
from backend.app.src.services.groups.membership import GroupMembershipService
from backend.app.src.config import settings as global_settings
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

router = APIRouter(
    # Префікс /ratings буде додано в __init__.py батьківського роутера gamification
    # Теги також успадковуються/додаються звідти
)


# Залежність для отримання UserRatingService
async def get_user_rating_service(session: AsyncSession = Depends(get_api_db_session)) -> UserRatingService:
    """Залежність FastAPI для отримання екземпляра UserRatingService."""
    return UserRatingService(db_session=session)

# ПРИМІТКА: Перевірка прав доступу до групи виконується через залежність `check_group_view_permission`.
# Основна логіка формування лідерборду покладається на `UserRatingService`.
@router.get(
    "/group/{group_id}/leaderboard",  # Змінено шлях для ясності
    response_model=GroupLeaderboardResponse,  # Повертає весь об'єкт лідерборду
    summary="Отримання рейтингу користувачів у групі (лідерборд)",  # i18n
    description="""Повертає відсортований список найкращих користувачів у вказаній групі
    на основі їхніх балів за вказаний період.
    Доступно членам групи або суперюзерам.""",  # i18n
    dependencies=[Depends(check_group_view_permission)]  # Перевірка доступу до групи
)
async def get_group_ratings_leaderboard(
        group_id: UUID = Path(..., description="ID групи, для якої запитується лідерборд"),  # i18n
        period_identifier: Optional[str] = Query(None,
                                                 description="Ідентифікатор періоду (напр., 'all_time', 'YYYY-MM')"),
        # i18n
        limit: int = Query(global_settings.DEFAULT_LEADERBOARD_SIZE, ge=1, le=global_settings.MAX_LEADERBOARD_SIZE,
                           description="Кількість позицій у лідерборді"),  # i18n
        # current_user_with_permission: UserModel = Depends(check_group_view_permission), # Вже в dependencies
        rating_service: UserRatingService = Depends(get_user_rating_service)
) -> GroupLeaderboardResponse:
    """
    Отримує лідерборд (рейтинг користувачів) для вказаної групи та періоду.
    Користувач повинен бути членом групи або мати відповідні права для перегляду.
    """
    # logger.info(f"Користувач ID '{current_user_with_permission.id}' запитує лідерборд для групи ID '{group_id}'.")
    logger.info(f"Запит лідерборду для групи ID '{group_id}'. Період: {period_identifier}, Ліміт: {limit}.")

    try:
        # UserRatingService.get_group_leaderboard повертає готовий GroupLeaderboardResponse
        leaderboard_response = await rating_service.get_group_leaderboard(
            group_id=group_id,
            period_identifier=period_identifier,  # Сервіс використає дефолт, якщо None
            limit=limit
        )
        if not leaderboard_response:  # Малоймовірно, якщо сервіс кидає винятки при помилках
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Лідерборд для вказаної групи не знайдено.")
        return leaderboard_response
    except ValueError as e:  # Наприклад, якщо група не знайдена (має обробитися в check_group_view_permission)
        logger.warning(f"Помилка отримання лідерборду для групи ID '{group_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при отриманні лідерборду для групи ID '{group_id}': {e}",
                     exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.get(
    "/me/group/{group_id}",
    response_model=Optional[UserGroupRatingResponse],  # Може бути None, якщо користувач не має рейтингу
    summary="Отримання рейтингової інформації поточного користувача в групі",  # i18n
    description="""Повертає інформацію про рейтинг поточного користувача
    (наприклад, бали, позиція в загальному рейтингу групи) у вказаній групі."""  # i18n
)
# ПРИМІТКА: Важливою є перевірка активного членства користувача в групі перед
# запитом його рейтингу в цій групі.
async def get_my_rating_in_group(
        group_id: UUID = Path(..., description="ID групи"),  # i18n
        period_identifier: Optional[str] = Query(None,
                                                 description="Ідентифікатор періоду (напр., 'all_time', 'YYYY-MM')"),
        # i18n
        current_user: UserModel = Depends(get_current_active_user),
        rating_service: UserRatingService = Depends(get_user_rating_service),
        membership_service: GroupMembershipService = Depends(get_group_membership_service)  # Оновлено залежність
) -> Optional[UserGroupRatingResponse]:
    """
    Отримує рейтингову інформацію поточного користувача для конкретної групи.
    Користувач має бути членом цієї групи.
    """
    logger.info(
        f"Користувач ID '{current_user.id}' запитує свій рейтинг в групі ID '{group_id}'. Період: {period_identifier}.")

    # Перевірка членства в групі
    membership = await membership_service.get_membership_details(group_id=group_id, user_id=current_user.id)
    if not membership or not membership.is_active:
        # i18n
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ви не є активним членом цієї групи.")

    try:
        # UserRatingService.get_user_group_rating повертає UserGroupRatingResponse або None
        rating_info = await rating_service.get_user_group_rating(
            user_id=current_user.id,
            group_id=group_id,
            period_identifier=period_identifier  # Сервіс використає дефолт, якщо None
        )
        if not rating_info:
            logger.info(
                f"Рейтингову інформацію для користувача ID '{current_user.id}' в групі ID '{group_id}' (період: {period_identifier}) не знайдено.")
            # Це не помилка, просто може не бути рейтингу
        return rating_info
    except ValueError as e:  # Якщо сервіс кидає ValueError
        logger.warning(
            f"Помилка отримання рейтингу для користувача ID '{current_user.id}' в групі ID '{group_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при отриманні рейтингу для ID '{current_user.id}': {e}",
                     exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


# TODO: Розглянути ендпоінт для оновлення рейтингу користувача (POST /user/{user_id}/group/{group_id}/recalculate),
#  якщо потрібен примусовий перерахунок (зазвичай це має відбуватися автоматично або фоновим завданням).
#  Такий ендпоінт має бути доступний тільки для адміністраторів/суперюзерів.

logger.info(f"Роутер для рейтингів та лідербордів (`{router.prefix}`) визначено.")
