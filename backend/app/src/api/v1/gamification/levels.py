# backend/app/src/api/v1/gamification/levels.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління налаштуваннями рівнів та перегляду рівнів користувачів API v1.

Цей модуль надає API для:
- Адміністраторів групи: CRUD операції з налаштуваннями рівнів (визначення порогів для рівнів).
- Учасників групи: Перегляд свого поточного рівня та прогресу до наступного.
- Учасників групи: Можливо, перегляд списку всіх доступних рівнів та їх умов.
"""

from fastapi import APIRouter, Depends, Path, status
from typing import List, Optional

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.gamification.level import LevelSchema, LevelCreateSchema, LevelUpdateSchema, UserLevelSchema
from backend.app.src.services.gamification.level_service import LevelService
from backend.app.src.services.gamification.user_level_service import UserLevelService
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.api.v1.groups.groups import group_admin_permission, group_member_permission
from backend.app.src.models.auth.user import UserModel

logger = get_logger(__name__)
router = APIRouter()

# Ендпоінти для налаштування рівнів (адміністратором групи)
# Префікс /groups/{group_id}/gamification/levels-config (приклад)

@router.post(
    "/config", # Відносно /groups/{group_id}/gamification/levels
    response_model=LevelSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Gamification", "Levels Configuration"],
    summary="Створити нове налаштування рівня (адміністратор групи)"
)
async def create_level_configuration(
    group_id: int = Path(..., description="ID групи"),
    level_in: LevelCreateSchema,
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends()
):
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(f"Адмін {current_admin.email} створює налаштування рівня '{level_in.name}' для групи {group_id}.")
    service = LevelService(db_session)
    # Переконатися, що level_in має group_id або сервіс його встановлює
    if not hasattr(level_in, 'group_id') or level_in.group_id != group_id:
         # Або встановити тут: level_in.group_id = group_id
        logger.warning(f"Невідповідність group_id у запиті на створення рівня для групи {group_id}.")
        # Можна кинути помилку або дозволити сервісу встановити group_id

    new_level_config = await service.create_level_config(level_create_data=level_in, group_id=group_id)
    return new_level_config

@router.get(
    "/config",
    response_model=List[LevelSchema],
    tags=["Gamification", "Levels Configuration"],
    summary="Отримати список налаштувань рівнів для групи"
)
async def list_level_configurations(
    group_id: int = Path(..., description="ID групи"),
    access_check: dict = Depends(group_member_permission), # Учасники можуть бачити налаштування рівнів
    db_session: DBSession = Depends()
):
    current_user: UserModel = access_check["current_user"]
    logger.info(f"Користувач {current_user.email} запитує налаштування рівнів для групи {group_id}.")
    service = LevelService(db_session)
    level_configs = await service.get_level_configs_for_group(group_id=group_id)
    return level_configs

@router.put(
    "/config/{level_config_id}",
    response_model=LevelSchema,
    tags=["Gamification", "Levels Configuration"],
    summary="Оновити налаштування рівня (адміністратор групи)"
)
async def update_level_configuration(
    group_id: int = Path(..., description="ID групи"),
    level_config_id: int = Path(..., description="ID налаштування рівня"),
    level_in: LevelUpdateSchema,
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends()
):
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(f"Адмін {current_admin.email} оновлює налаштування рівня ID {level_config_id} для групи {group_id}.")
    service = LevelService(db_session)
    updated_level_config = await service.update_level_config(
        level_config_id=level_config_id,
        level_update_data=level_in,
        group_id_context=group_id # Для перевірки, що налаштування належить групі
    )
    if not updated_level_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Налаштування рівня не знайдено.")
    return updated_level_config

@router.delete(
    "/config/{level_config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Gamification", "Levels Configuration"],
    summary="Видалити налаштування рівня (адміністратор групи)"
)
async def delete_level_configuration(
    group_id: int = Path(..., description="ID групи"),
    level_config_id: int = Path(..., description="ID налаштування рівня"),
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends()
):
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(f"Адмін {current_admin.email} видаляє налаштування рівня ID {level_config_id} для групи {group_id}.")
    service = LevelService(db_session)
    success = await service.delete_level_config(level_config_id=level_config_id, group_id_context=group_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Налаштування рівня не знайдено або не вдалося видалити.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Ендпоінти для перегляду рівня користувача
# Префікс /groups/{group_id}/gamification/my-level (приклад)

@router.get(
    "/my-level", # Відносно /groups/{group_id}/gamification/levels
    response_model=UserLevelSchema, # Або спеціальна схема, що включає прогрес
    tags=["Gamification", "User Levels"],
    summary="Отримати свій поточний рівень та прогрес у групі"
)
async def get_my_level_in_group(
    group_id: int = Path(..., description="ID групи"),
    access_check: dict = Depends(group_member_permission),
    db_session: DBSession = Depends()
):
    current_user: UserModel = access_check["current_user"]
    logger.info(f"Користувач {current_user.email} запитує свій рівень в групі {group_id}.")
    user_level_service = UserLevelService(db_session) # Сервіс для роботи з рівнями користувачів

    # Сервіс може повертати поточний рівень користувача, його очки та прогрес до наступного рівня
    user_level_data = await user_level_service.get_user_level_and_progress(
        user_id=current_user.id,
        group_id=group_id
    )
    if not user_level_data:
        # Можливо, користувач ще не має рівня (0 очок)
        # Сервіс може повернути дефолтний "нульовий" рівень або помилку 404
        logger.info(f"Дані про рівень для користувача {current_user.email} в групі {group_id} не знайдено, можливо, це новий користувач.")
        # Залежно від логіки, можна повернути 404 або базовий рівень
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Дані про рівень не знайдено.")

    return user_level_data

# Роутер буде підключений в backend/app/src/api/v1/gamification/__init__.py
# з префіксом /levels (або іншим, як /level-settings та /my-level)
