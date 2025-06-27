# backend/app/src/api/v1/system/settings.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління налаштуваннями системи.

Цей модуль надає API для перегляду та зміни глобальних налаштувань системи.
Доступ до цих ендпоінтів зазвичай має лише суперкористувач.

Налаштування можуть включати:
- Ліміти запитів.
- Параметри інтеграцій за замовчуванням.
- Налаштування логування.
- Інші глобальні параметри системи.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Any # Any залишаємо для гнучкості значення налаштування

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.system.settings import SystemSettingSchema, SystemSettingUpdateSchema
from backend.app.src.services.system.system_settings_service import SystemSettingsService
from backend.app.src.api.dependencies import DBSession, CurrentSuperuser
from backend.app.src.models.auth.user import UserModel # Для type hint current_user

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/settings",
    response_model=List[SystemSettingSchema],
    tags=["System", "Settings"],
    summary="Отримати всі системні налаштування",
)
async def get_system_settings(
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    """
    Повертає список всіх системних налаштувань.
    Доступно лише суперкористувачам.
    """
    logger.info(f"Користувач {current_user.email} запитує всі системні налаштування.")
    settings_service = SystemSettingsService(db_session)
    settings = await settings_service.get_all_settings()
    return settings

@router.get(
    "/settings/{setting_name}",
    response_model=SystemSettingSchema,
    tags=["System", "Settings"],
    summary="Отримати конкретне системне налаштування за ім'ям",
)
async def get_system_setting_by_name(
    setting_name: str,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    """
    Повертає значення конкретного системного налаштування.
    Доступно лише суперкористувачам.
    """
    logger.info(f"Користувач {current_user.email} запитує системне налаштування: {setting_name}.")
    settings_service = SystemSettingsService(db_session)
    setting = await settings_service.get_setting_by_name(setting_name)
    if not setting:
        logger.warning(f"Системне налаштування '{setting_name}' не знайдено (запит від {current_user.email}).")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Налаштування не знайдено")
    return setting

@router.put(
    "/settings/{setting_name}",
    response_model=SystemSettingSchema,
    tags=["System", "Settings"],
    summary="Оновити системне налаштування",
)
async def update_system_setting(
    setting_name: str,
    setting_data: SystemSettingUpdateSchema,
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    """
    Оновлює значення конкретного системного налаштування.
    Доступно лише суперкористувачам.
    """
    logger.info(
        f"Користувач {current_user.email} запитує оновлення системного налаштування: "
        f"{setting_name} з даними: {setting_data.value}."
    )
    settings_service = SystemSettingsService(db_session)

    # У SystemSettingsService метод update_setting може приймати SystemSettingUpdateSchema
    # або окремо name та value. Припускаємо, що він приймає name та value.
    updated_setting = await settings_service.update_setting(
        setting_name=setting_name,
        new_value_data=setting_data # Передаємо всю схему, сервіс розбереться
    )
    if not updated_setting:
        logger.warning(
            f"Не вдалося оновити системне налаштування '{setting_name}' (не знайдено) "
            f"за запитом від {current_user.email}."
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Налаштування не знайдено для оновлення")

    logger.info(f"Системне налаштування '{setting_name}' успішно оновлено користувачем {current_user.email}.")
    return updated_setting

# Роутер буде підключений в backend/app/src/api/v1/system/__init__.py
# або безпосередньо в backend/app/src/api/v1/router.py
