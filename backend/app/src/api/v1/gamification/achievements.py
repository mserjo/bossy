# backend/app/src/api/v1/gamification/achievements.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для перегляду досягнень користувачів API v1.

Цей модуль надає API для:
- Перегляду списку досягнень (зароблених бейджів) поточного користувача в групі.
- Можливо, перегляду досягнень іншого користувача (якщо дозволено правами або налаштуваннями приватності).
- Можливо, перегляду загального списку всіх можливих досягнень (якщо вони відрізняються від бейджів).
  (Поточна структура передбачає, що "досягнення" - це екземпляр заробленого "бейджа").
"""

from fastapi import APIRouter, Depends, Path
from typing import List, Optional

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.gamification.achievement import UserAchievementSchema # Схема для заробленого бейджа
from backend.app.src.services.gamification.achievement_service import AchievementService
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.api.v1.groups.groups import group_member_permission # Для перевірки членства в групі
from backend.app.src.models.auth.user import UserModel

logger = get_logger(__name__)
router = APIRouter()

# Ендпоінти для перегляду досягнень
# Префікс /groups/{group_id}/gamification/achievements

@router.get(
    "/me", # Відносно /groups/{group_id}/gamification/achievements
    response_model=List[UserAchievementSchema],
    tags=["Gamification", "User Achievements"],
    summary="Отримати список моїх досягнень (зароблених бейджів) у групі"
)
async def get_my_achievements_in_group(
    group_id: int = Path(..., description="ID групи"),
    access_check: dict = Depends(group_member_permission),
    db_session: DBSession = Depends()
):
    current_user: UserModel = access_check["current_user"]
    logger.info(f"Користувач {current_user.email} запитує свої досягнення в групі {group_id}.")
    service = AchievementService(db_session)
    achievements = await service.get_user_achievements_in_group(
        user_id=current_user.id,
        group_id=group_id
    )
    return achievements

@router.get(
    "/user/{user_id_target}", # Відносно /groups/{group_id}/gamification/achievements
    response_model=List[UserAchievementSchema],
    tags=["Gamification", "User Achievements"],
    summary="Отримати список досягнень вказаного користувача у групі"
)
async def get_user_achievements_in_group(
    group_id: int = Path(..., description="ID групи"),
    user_id_target: int = Path(..., description="ID користувача, чиї досягнення запитуються"),
    access_check: dict = Depends(group_member_permission), # Перевірка, що запитувач є членом групи
    db_session: DBSession = Depends()
):
    requesting_user: UserModel = access_check["current_user"]
    logger.info(
        f"Користувач {requesting_user.email} запитує досягнення користувача ID {user_id_target} "
        f"в групі {group_id}."
    )
    # TODO: Додати перевірку налаштувань приватності: чи дозволено переглядати досягнення інших.
    # Наразі, якщо запитувач є членом групи, він може бачити досягнення іншого члена тієї ж групи.

    service = AchievementService(db_session)
    # Перевірка, чи user_id_target також є членом групи (може бути в сервісі)
    is_target_member = await service.is_user_member_of_group(user_id=user_id_target, group_id=group_id)
    if not is_target_member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Вказаний користувач не є членом цієї групи.")

    achievements = await service.get_user_achievements_in_group(
        user_id=user_id_target,
        group_id=group_id
    )
    return achievements

# Роутер буде підключений в backend/app/src/api/v1/gamification/__init__.py
