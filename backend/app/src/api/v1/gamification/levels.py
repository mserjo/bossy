# backend/app/src/api/v1/gamification/levels.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління налаштуваннями рівнів та перегляду рівнів користувачів API v1.

Цей модуль надає API для:
- Адміністраторів групи: CRUD операції з налаштуваннями рівнів (визначення порогів для рівнів).
- Учасників групи: Перегляд свого поточного рівня та прогресу до наступного.
- Учасників групи: Перегляд рівня іншого учасника групи або списку рівнів всіх учасників.
"""

from fastapi import APIRouter, Depends, Path, Query, status, HTTPException, Response
from typing import List, Optional

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.gamification.level import LevelSchema, LevelCreateSchema, LevelUpdateSchema, UserLevelSchema
from backend.app.src.services.gamification.level_service import LevelService
from backend.app.src.services.gamification.user_level_service import UserLevelService
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.api.v1.groups.groups import group_admin_permission, group_member_permission
from backend.app.src.models.auth.user import UserModel
from backend.app.src.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE

logger = get_logger(__name__)
router = APIRouter()

# Префікс для всіх ендпоінтів цього роутера буде /groups/{group_id}/gamification/levels

# --- Ендпоінти для налаштування рівнів (адміністратором групи) ---
config_router = APIRouter(prefix="/config", tags=["Gamification", "Levels Configuration"])

@config_router.post(
    "",
    response_model=LevelSchema,
    status_code=status.HTTP_201_CREATED,
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

    if hasattr(level_in, 'group_id') and level_in.group_id is not None and level_in.group_id != group_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ID групи в тілі запиту ({level_in.group_id}) не співпадає з ID групи у шляху ({group_id})."
        )
    # Якщо group_id немає в схемі створення, сервіс має його встановити
    # або можна додати group_id до схеми і перевіряти тут.
    # Для даного прикладу, припустимо, що сервіс очікує group_id як окремий параметр.

    new_level_config = await service.create_level_config(level_create_data=level_in, group_id=group_id)
    return new_level_config

@config_router.get(
    "",
    response_model=List[LevelSchema],
    summary="Отримати список налаштувань рівнів для групи"
)
async def list_level_configurations(
    group_id: int = Path(..., description="ID групи"),
    access_check: dict = Depends(group_member_permission),
    db_session: DBSession = Depends()
):
    current_user: UserModel = access_check["current_user"]
    logger.info(f"Користувач {current_user.email} запитує налаштування рівнів для групи {group_id}.")
    service = LevelService(db_session)
    level_configs = await service.get_level_configs_for_group(group_id=group_id)
    return level_configs

@config_router.put(
    "/{level_config_id}",
    response_model=LevelSchema,
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
        group_id_context=group_id
    )
    if not updated_level_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Налаштування рівня не знайдено.")
    return updated_level_config

@config_router.delete(
    "/{level_config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
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

# --- Ендпоінти для перегляду рівнів користувачів ---
user_levels_router = APIRouter(tags=["Gamification", "User Levels"])

@user_levels_router.get(
    "/me", # Відносно /groups/{group_id}/gamification/levels
    response_model=UserLevelSchema,
    summary="Отримати свій поточний рівень та прогрес у групі"
)
async def get_my_level_in_group(
    group_id: int = Path(..., description="ID групи"),
    access_check: dict = Depends(group_member_permission),
    db_session: DBSession = Depends()
):
    current_user: UserModel = access_check["current_user"]
    logger.info(f"Користувач {current_user.email} запитує свій рівень в групі {group_id}.")
    user_level_service = UserLevelService(db_session)
    user_level_data = await user_level_service.get_user_level_and_progress(
        user_id=current_user.id,
        group_id=group_id
    )
    if not user_level_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Дані про рівень не знайдено.")
    return user_level_data

@user_levels_router.get(
    "/users/{user_id_in_group}/level", # Відносно /groups/{group_id}/gamification/levels
    response_model=UserLevelSchema,
    summary="Отримати рівень конкретного користувача в групі"
)
async def get_user_level_in_group(
    group_id: int = Path(..., description="ID групи"),
    user_id_in_group: int = Path(..., description="ID користувача, чий рівень запитується"),
    access_check: dict = Depends(group_member_permission), # Члени групи можуть бачити рівні інших
    db_session: DBSession = Depends()
):
    current_user: UserModel = access_check["current_user"]
    logger.info(f"Користувач {current_user.email} запитує рівень користувача ID {user_id_in_group} в групі {group_id}.")
    user_level_service = UserLevelService(db_session)
    user_level_data = await user_level_service.get_user_level_and_progress(
        user_id=user_id_in_group,
        group_id=group_id
    )
    if not user_level_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Дані про рівень для вказаного користувача не знайдено.")
    return user_level_data

@user_levels_router.get(
    "/users/levels", # Відносно /groups/{group_id}/gamification/levels
    response_model=List[UserLevelSchema], # Або схема з пагінацією
    summary="Отримати список рівнів всіх користувачів у групі"
)
async def list_all_user_levels_in_group(
    group_id: int = Path(..., description="ID групи"),
    access_check: dict = Depends(group_member_permission),
    db_session: DBSession = Depends(),
    page: int = Query(DEFAULT_PAGE, ge=1, description="Номер сторінки"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100, description="Розмір сторінки")
):
    current_user: UserModel = access_check["current_user"]
    logger.info(f"Користувач {current_user.email} запитує список рівнів всіх користувачів у групі {group_id}.")
    user_level_service = UserLevelService(db_session)

    user_levels_data = await user_level_service.get_all_user_levels_in_group(
        group_id=group_id,
        skip=(page - 1) * page_size,
        limit=page_size
    )
    if isinstance(user_levels_data, dict): # Якщо сервіс повертає пагіновані дані
        levels = user_levels_data.get("user_levels", [])
        # total = user_levels_data.get("total", 0) # Для заголовків пагінації
    else:
        levels = user_levels_data

    return levels

# Підключення роутерів до основного роутера цього модуля
router.include_router(config_router)
router.include_router(user_levels_router)

# Основний роутер 'router' буде підключений в backend/app/src/api/v1/gamification/__init__.py
# з префіксом /levels.
# Тоді шляхи будуть:
# /groups/{group_id}/gamification/levels/config/...
# /groups/{group_id}/gamification/levels/me
# /groups/{group_id}/gamification/levels/users/{user_id_in_group}/level
# /groups/{group_id}/gamification/levels/users/levels
