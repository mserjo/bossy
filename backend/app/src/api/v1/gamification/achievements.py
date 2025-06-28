# backend/app/src/api/v1/gamification/achievements.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для перегляду досягнень користувачів API v1.

Цей модуль надає API для:
- Перегляду списку досягнень (зароблених бейджів) поточного користувача в групі.
- Перегляду досягнень іншого користувача в групі.
- Перегляду всіх досягнень в групі.
"""

from fastapi import APIRouter, Depends, Path, Query, status, HTTPException
from typing import List, Optional

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.gamification.achievement import UserAchievementSchema
from backend.app.src.services.gamification.achievement_service import AchievementService
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.api.v1.groups.groups import group_member_permission
from backend.app.src.models.auth.user import UserModel
from backend.app.src.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE

logger = get_logger(__name__)
router = APIRouter()

# Префікс для цих ендпоінтів буде /groups/{group_id}/gamification/achievements

@router.get(
    "/me",
    response_model=List[UserAchievementSchema],
    tags=["Gamification", "User Achievements"],
    summary="Отримати список моїх досягнень (зароблених бейджів) у групі"
)
async def get_my_achievements_in_group(
    group_id: int = Path(..., description="ID групи"),
    access_check: dict = Depends(group_member_permission),
    db_session: DBSession = Depends(),
    page: int = Query(DEFAULT_PAGE, ge=1, description="Номер сторінки"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100, description="Розмір сторінки")
):
    current_user: UserModel = access_check["current_user"]
    logger.info(f"Користувач {current_user.email} запитує свої досягнення в групі {group_id} (стор: {page}, розм: {page_size}).")
    service = AchievementService(db_session)
    achievements_data = await service.get_user_achievements_in_group(
        user_id=current_user.id,
        group_id=group_id,
        skip=(page - 1) * page_size,
        limit=page_size
    )
    if isinstance(achievements_data, dict):
        achievements = achievements_data.get("achievements", [])
    else:
        achievements = achievements_data
    return achievements

@router.get(
    "/user/{user_id_target}",
    response_model=List[UserAchievementSchema],
    tags=["Gamification", "User Achievements"],
    summary="Отримати список досягнень вказаного користувача у групі"
)
async def get_user_achievements_in_group(
    group_id: int = Path(..., description="ID групи"),
    user_id_target: int = Path(..., description="ID користувача, чиї досягнення запитуються"),
    access_check: dict = Depends(group_member_permission),
    db_session: DBSession = Depends(),
    page: int = Query(DEFAULT_PAGE, ge=1, description="Номер сторінки"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100, description="Розмір сторінки")
):
    requesting_user: UserModel = access_check["current_user"]
    logger.info(
        f"Користувач {requesting_user.email} запитує досягнення користувача ID {user_id_target} "
        f"в групі {group_id} (стор: {page}, розм: {page_size})."
    )
    service = AchievementService(db_session)

    # Перевірка, чи цільовий користувач є членом групи (може бути частиною логіки сервісу)
    is_target_member = await service.is_user_member_of_group(user_id=user_id_target, group_id=group_id, db_session=db_session)
    if not is_target_member:
        # Або якщо сервіс сам кидає помилку, то ця перевірка тут не потрібна
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Вказаний користувач не є членом цієї групи.")

    achievements_data = await service.get_user_achievements_in_group(
        user_id=user_id_target,
        group_id=group_id,
        skip=(page - 1) * page_size,
        limit=page_size
    )
    if isinstance(achievements_data, dict):
        achievements = achievements_data.get("achievements", [])
    else:
        achievements = achievements_data
    return achievements

@router.get(
    "/all-in-group",
    response_model=List[UserAchievementSchema], # Або схема з пагінацією
    tags=["Gamification", "User Achievements"],
    summary="Отримати список всіх досягнень всіх користувачів у групі"
)
async def list_all_achievements_in_group(
    group_id: int = Path(..., description="ID групи"),
    access_check: dict = Depends(group_member_permission), # Доступ для членів групи
    db_session: DBSession = Depends(),
    page: int = Query(DEFAULT_PAGE, ge=1, description="Номер сторінки"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100, description="Розмір сторінки"),
    # Можливі фільтри: user_id, badge_id, date_from, date_to
    user_id: Optional[int] = Query(None, description="Фільтр за ID користувача"),
    badge_id: Optional[int] = Query(None, description="Фільтр за ID бейджа")
):
    current_user: UserModel = access_check["current_user"]
    logger.info(
        f"Користувач {current_user.email} запитує всі досягнення в групі {group_id} "
        f"(стор: {page}, розм: {page_size}, user_id: {user_id}, badge_id: {badge_id})."
    )
    service = AchievementService(db_session)
    achievements_data = await service.get_all_achievements_in_group(
        group_id=group_id,
        skip=(page - 1) * page_size,
        limit=page_size,
        user_id_filter=user_id,
        badge_id_filter=badge_id
    )
    if isinstance(achievements_data, dict):
        achievements = achievements_data.get("achievements", [])
    else:
        achievements = achievements_data
    return achievements

# Роутер буде підключений в backend/app/src/api/v1/gamification/__init__.py
# з префіксом /achievements.
# Тоді шляхи будуть:
# /groups/{group_id}/gamification/achievements/me
# /groups/{group_id}/gamification/achievements/user/{user_id_target}
# /groups/{group_id}/gamification/achievements/all-in-group
