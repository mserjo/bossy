# backend/app/src/api/v1/groups/settings.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління налаштуваннями конкретної групи API v1.

Цей модуль надає API для адміністраторів групи для перегляду та зміни
різноманітних налаштувань, специфічних для їхньої групи, наприклад:
- Назва валюти бонусів.
- Правила максимального боргу.
- Дозволи на певні дії для учасників групи.
- Налаштування приватності групи.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.groups.settings import GroupSettingsSchema, GroupSettingsUpdateSchema
from backend.app.src.services.groups.group_settings_service import GroupSettingsService
from backend.app.src.api.dependencies import DBSession
from backend.app.src.api.v1.groups.groups import group_admin_permission # Залежність для перевірки прав адміна
from backend.app.src.models.groups.group import GroupModel # Для type hint залежності group_admin_permission
from backend.app.src.models.auth.user import UserModel # Для current_user з group_admin_permission

logger = get_logger(__name__)
router = APIRouter()

@router.get(
    "/{group_id}/settings",
    response_model=GroupSettingsSchema,
    tags=["Groups", "Group Settings"],
    summary="Отримати налаштування групи"
)
async def get_group_settings(
    group_id: int, # group_id з шляху використовується залежністю group_admin_permission
    # Залежність group_admin_permission вже перевіряє, що користувач є адміном групи group_id,
    # і може повернути об'єкт групи, якщо це зручно, або просто пройти, якщо права є.
    # Для отримання налаштувань нам потрібен group_id, який вже є.
    # І поточний користувач для логування (отримується в group_admin_permission).
    # Також потрібна сесія БД.
    group_with_admin_rights: dict = Depends(group_admin_permission), # Припускаємо, що залежність повертає dict з group та current_user
    db_session: DBSession = Depends()
):
    """
    Повертає поточні налаштування для вказаної групи.
    Доступно лише адміністраторам цієї групи.
    """
    current_user: UserModel = group_with_admin_rights["current_user"]
    logger.info(f"Адміністратор {current_user.email} запитує налаштування для групи ID {group_id}.")

    settings_service = GroupSettingsService(db_session)
    group_settings = await settings_service.get_settings_by_group_id(group_id=group_id)

    if not group_settings:
        # Це мало б бути оброблено на рівні group_admin_permission, якщо група не існує.
        # Але якщо налаштування можуть бути відсутні для існуючої групи:
        logger.warning(f"Налаштування для групи ID {group_id} не знайдено.")
        # Можна повернути дефолтні або створити їх тут, або кинути 404
        # Для прикладу, створимо, якщо їх немає (сервіс повинен це обробляти)
        # group_settings = await settings_service.create_default_settings_for_group(group_id)
        # if not group_settings: # Якщо і дефолтні не вдалося створити
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Налаштування для групи не знайдено.")

    return group_settings

@router.put(
    "/{group_id}/settings",
    response_model=GroupSettingsSchema,
    tags=["Groups", "Group Settings"],
    summary="Оновити налаштування групи"
)
async def update_group_settings(
    group_id: int, # group_id з шляху
    settings_data: GroupSettingsUpdateSchema,
    group_with_admin_rights: dict = Depends(group_admin_permission), # Перевірка прав
    db_session: DBSession = Depends()
):
    """
    Оновлює налаштування для вказаної групи.
    Доступно лише адміністраторам цієї групи.
    """
    current_user: UserModel = group_with_admin_rights["current_user"]
    logger.info(f"Адміністратор {current_user.email} оновлює налаштування для групи ID {group_id}.")

    settings_service = GroupSettingsService(db_session)
    try:
        updated_settings = await settings_service.update_settings_for_group(
            group_id=group_id,
            settings_in=settings_data
        )
        if not updated_settings:
             # Малоймовірно, якщо group_admin_permission пройшла, але для повноти
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Групу не знайдено для оновлення налаштувань.")
        logger.info(f"Налаштування для групи ID {group_id} успішно оновлено.")
        return updated_settings
    except HTTPException as e:
        logger.warning(f"Помилка оновлення налаштувань групи ID {group_id}: {e.detail}")
        raise e
    except Exception as e_gen:
        logger.error(f"Неочікувана помилка при оновленні налаштувань групи ID {group_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при оновленні налаштувань групи.")

# Роутер буде підключений в backend/app/src/api/v1/groups/__init__.py
