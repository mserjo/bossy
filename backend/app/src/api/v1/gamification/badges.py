# backend/app/src/api/v1/gamification/badges.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління бейджами API v1.

Цей модуль надає API для:
- Адміністраторів групи: CRUD операції з бейджами (створення, опис, іконка, умови отримання).
- Учасників групи: Перегляд списку всіх доступних бейджів у групі.
"""

from fastapi import APIRouter, Depends, Path, status, Response
from typing import List, Optional

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.gamification.badge import BadgeSchema, BadgeCreateSchema, BadgeUpdateSchema
from backend.app.src.services.gamification.badge_service import BadgeService
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.api.v1.groups.groups import group_admin_permission, group_member_permission
from backend.app.src.models.auth.user import UserModel

logger = get_logger(__name__)
router = APIRouter()

# Ендпоінти для CRUD операцій з бейджами (адміністратором групи)
# Префікс /groups/{group_id}/gamification/badges

@router.post(
    "", # Відносно /groups/{group_id}/gamification/badges
    response_model=BadgeSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Gamification", "Badges"],
    summary="Створити новий бейдж (адміністратор групи)"
)
async def create_badge(
    group_id: int = Path(..., description="ID групи"),
    badge_in: BadgeCreateSchema,
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends()
):
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(f"Адмін {current_admin.email} створює бейдж '{badge_in.name}' для групи {group_id}.")
    service = BadgeService(db_session)
    # Переконатися, що badge_in має group_id або сервіс його встановлює
    if not hasattr(badge_in, 'group_id') or badge_in.group_id != group_id:
        logger.warning(f"Невідповідність group_id у запиті на створення бейджа для групи {group_id}.")
        # Можна кинути помилку або дозволити сервісу встановити group_id

    new_badge = await service.create_badge(badge_create_data=badge_in, group_id=group_id)
    return new_badge

@router.get(
    "",
    response_model=List[BadgeSchema],
    tags=["Gamification", "Badges"],
    summary="Отримати список всіх бейджів у групі"
)
async def list_badges_in_group(
    group_id: int = Path(..., description="ID групи"),
    access_check: dict = Depends(group_member_permission), # Учасники можуть бачити бейджі
    db_session: DBSession = Depends()
):
    current_user: UserModel = access_check["current_user"]
    logger.info(f"Користувач {current_user.email} запитує список бейджів для групи {group_id}.")
    service = BadgeService(db_session)
    badges = await service.get_badges_for_group(group_id=group_id)
    return badges

@router.get(
    "/{badge_id}",
    response_model=BadgeSchema,
    tags=["Gamification", "Badges"],
    summary="Отримати деталі конкретного бейджа"
)
async def get_badge_details(
    group_id: int = Path(..., description="ID групи"),
    badge_id: int = Path(..., description="ID бейджа"),
    access_check: dict = Depends(group_member_permission),
    db_session: DBSession = Depends()
):
    current_user: UserModel = access_check["current_user"]
    logger.info(f"Користувач {current_user.email} запитує деталі бейджа ID {badge_id} з групи {group_id}.")
    service = BadgeService(db_session)
    badge = await service.get_badge_by_id_and_group_id(badge_id=badge_id, group_id=group_id)
    if not badge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Бейдж не знайдено.")
    return badge

@router.put(
    "/{badge_id}",
    response_model=BadgeSchema,
    tags=["Gamification", "Badges"],
    summary="Оновити бейдж (адміністратор групи)"
)
async def update_badge(
    group_id: int = Path(..., description="ID групи"),
    badge_id: int = Path(..., description="ID бейджа"),
    badge_in: BadgeUpdateSchema,
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends()
):
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(f"Адмін {current_admin.email} оновлює бейдж ID {badge_id} для групи {group_id}.")
    service = BadgeService(db_session)
    updated_badge = await service.update_badge(
        badge_id=badge_id,
        badge_update_data=badge_in,
        group_id_context=group_id
    )
    if not updated_badge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Бейдж не знайдено для оновлення.")
    return updated_badge

@router.delete(
    "/{badge_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Gamification", "Badges"],
    summary="Видалити бейдж (адміністратор групи)"
)
async def delete_badge(
    group_id: int = Path(..., description="ID групи"),
    badge_id: int = Path(..., description="ID бейджа"),
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends()
):
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(f"Адмін {current_admin.email} видаляє бейдж ID {badge_id} для групи {group_id}.")
    service = BadgeService(db_session)
    success = await service.delete_badge(badge_id=badge_id, group_id_context=group_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Бейдж не знайдено або не вдалося видалити.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Роутер буде підключений в backend/app/src/api/v1/gamification/__init__.py
