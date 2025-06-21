# backend/app/src/api/v1/system/settings.py
# -*- coding: utf-8 -*-
"""
API ендпоінти для управління загальними налаштуваннями системи (System Settings).

Надає CRUD-операції для перегляду та модифікації
глобальних параметрів системи. Читання доступне автентифікованим користувачам
(з фільтрацією публічних налаштувань), запис - тільки суперкористувачам.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""

from typing import List, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Body

# Залежності API та моделі користувача
from backend.app.src.api.dependencies import get_current_active_superuser, get_current_active_user, get_system_setting_service
from backend.app.src.models.auth import User as UserModel

# Схеми Pydantic для налаштувань
from backend.app.src.schemas.system.settings import (
    SystemSettingResponseSchema,
    SystemSettingUpdateSchema,
    SystemSettingCreateSchema
)

# Сервіс системних налаштувань
from backend.app.src.services.system.settings import SystemSettingService
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

router = APIRouter()


# TODO: Визначити, які налаштування є суто для читання (read-only) з конфігураційних файлів,
# а які можуть динамічно змінюватися та зберігатися в БД.
# TODO: Додати валідацію типів значень для налаштувань при створенні/оновленні (можливо в сервісі або через Pydantic).

# --- Ендпоінти ---

# ПРИМІТКА: Фільтрація публічних налаштувань для звичайних користувачів
# та надання повного доступу для суперкористувачів реалізується
# в методах `SystemSettingService`.
@router.get(
    "/",
    response_model=List[SystemSettingResponseSchema],
    summary="Отримати список системних налаштувань",  # i18n
    description="""Дозволяє отримати список системних налаштувань.
Суперкористувачі бачать всі налаштування.
Інші автентифіковані користувачі бачать тільки публічні налаштування (`is_public=True`).""",  # i18n
    dependencies=[Depends(get_current_active_user)]  # Потрібен будь-який активний користувач
)
async def list_system_settings(
        service: SystemSettingService = Depends(get_system_setting_service),
        current_user: UserModel = Depends(get_current_active_user)
) -> List[SystemSettingResponseSchema]:
    """
    Повертає список системних налаштувань.
    Фільтрує непублічні налаштування для звичайних користувачів на рівні сервісу.
    """
    logger.info(
        f"Користувач '{current_user.username}' (ID: {current_user.id}, Суперюзер: {current_user.is_superuser}) запитує список системних налаштувань.")  # i18n

    settings_list = await service.get_all_settings(requesting_user=current_user)
    return settings_list


@router.get(
    "/{setting_key}",
    response_model=SystemSettingResponseSchema,
    summary="Отримати конкретне системне налаштування за ключем",  # i18n
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Налаштування не знайдено або доступ заборонено"}  # i18n
    },
    dependencies=[Depends(get_current_active_user)]  # Потрібен будь-який активний користувач
)
async def get_system_setting(
        setting_key: str,
        service: SystemSettingService = Depends(get_system_setting_service),
        current_user: UserModel = Depends(get_current_active_user)
) -> SystemSettingResponseSchema:
    """
    Повертає конкретне системне налаштування за його ключем.
    Якщо налаштування не публічне, доступне тільки суперкористувачам (логіка в сервісі).
    """
    logger.info(f"Користувач '{current_user.username}' запитує налаштування '{setting_key}'.")  # i18n

    setting = await service.get_setting_by_key(key=setting_key, requesting_user=current_user)

    if not setting:
        logger.warning(
            f"Налаштування '{setting_key}' не знайдено або доступ для користувача '{current_user.username}' обмежено.")  # i18n
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Налаштування з ключем '{setting_key}' не знайдено або доступ до нього обмежено."  # i18n
        )
    return setting


@router.post(
    "/",
    response_model=SystemSettingResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Створити нове системне налаштування (тільки для суперюзерів)",  # i18n
    description="Дозволяє суперкористувачам створювати нові системні налаштування. "  # i18n
                "Ключ налаштування має бути унікальним.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]
)
# ПРИМІТКА: Валідація типів значень для налаштувань, а також визначення
# налаштувань "тільки для читання" (якщо такі є серед створюваних/оновлюваних
# через API) має бути реалізовано в `SystemSettingService`,
# як зазначено в TODO на початку файлу.
async def create_system_setting(
        setting_data: SystemSettingCreateSchema,
        service: SystemSettingService = Depends(get_system_setting_service),
        current_superuser: UserModel = Depends(get_current_active_superuser)
) -> SystemSettingResponseSchema:
    """
    Створює нове системне налаштування. Доступно тільки суперкористувачам.
    """
    logger.info(
        f"Суперкористувач '{current_superuser.username}' створює нове налаштування: {setting_data.model_dump(exclude_unset=True)}")  # i18n

    try:
        # Передаємо UserModel як creating_user
        created_setting = await service.create_setting(setting_data=setting_data, creating_user=current_superuser)
    except HTTPException as e:  # Наприклад, конфлікт, якщо ключ вже існує (обробляється сервісом)
        logger.warning(
            f"Помилка при створенні налаштування '{setting_data.key}' користувачем '{current_superuser.username}': {e.detail}")  # i18n
        raise e
    except Exception as e:  # Інші непередбачені помилки
        logger.error(
            f"Непередбачена помилка при створенні налаштування '{setting_data.key}' користувачем '{current_superuser.username}': {e}",
            exc_info=True)  # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Внутрішня помилка сервера при створенні налаштування.")  # i18n

    logger.info(
        f"Налаштування '{created_setting.key}' успішно створено суперкористувачем '{current_superuser.username}'.")  # i18n
    return created_setting


@router.put(
    "/{setting_key}",
    response_model=SystemSettingResponseSchema,
    summary="Оновити значення системного налаштування (тільки для суперюзерів)",  # i18n
    description="Дозволяє суперкористувачам оновлювати значення існуючих системних налаштувань.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]
)
# ПРИМІТКА: Валідація типів значень для налаштувань, а також визначення
# налаштувань "тільки для читання" (якщо такі є серед створюваних/оновлюваних
# через API) має бути реалізовано в `SystemSettingService`,
# як зазначено в TODO на початку файлу.
async def update_system_setting(
        setting_key: str,
        setting_update_data: SystemSettingUpdateSchema = Body(...),
        service: SystemSettingService = Depends(get_system_setting_service),
        current_superuser: UserModel = Depends(get_current_active_superuser)
) -> SystemSettingResponseSchema:
    """
    Оновлює значення існуючого системного налаштування.
    Доступно тільки суперкористувачам.
    """
    logger.info(
        f"Суперкористувач '{current_superuser.username}' оновлює налаштування '{setting_key}' значенням: {setting_update_data.value}")  # i18n

    # Передаємо UserModel як updating_user
    updated_setting = await service.update_setting(
        key=setting_key,
        new_value_data=setting_update_data,
        updating_user=current_superuser
    )

    if not updated_setting:  # Сервіс поверне None, якщо налаштування не знайдено
        logger.warning(
            f"Налаштування '{setting_key}' не знайдено для оновлення суперкористувачем '{current_superuser.username}'.")  # i18n
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Налаштування з ключем '{setting_key}' не знайдено для оновлення."  # i18n
        )

    logger.info(
        f"Налаштування '{setting_key}' успішно оновлено суперкористувачем '{current_superuser.username}'.")  # i18n
    return updated_setting


@router.delete(
    "/{setting_key}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити системне налаштування (тільки для суперюзерів)",  # i18n
    description="Дозволяє суперкористувачам видаляти системні налаштування. "  # i18n
                "**Увага**: Ця дія незворотна і може вплинути на стабільність системи, якщо налаштування використовується.",
    # i18n
    dependencies=[Depends(get_current_active_superuser)]
)
async def delete_system_setting(
        setting_key: str,
        service: SystemSettingService = Depends(get_system_setting_service),
        current_superuser: UserModel = Depends(get_current_active_superuser)
):
    """
    Видаляє системне налаштування за його ключем.
    Доступно тільки суперкористувачам.
    Повертає 204 No Content у разі успішного видалення.
    Повертає 404 Not Found, якщо налаштування не знайдено (обробляється сервісом).
    """
    logger.info(
        f"Суперкористувач '{current_superuser.username}' запитує видалення налаштування '{setting_key}'.")  # i18n

    # Передаємо UserModel як deleting_user
    deleted_count = await service.delete_setting(key=setting_key,
                                                 deleting_user=current_superuser)  # Сервіс має повернути кількість видалених (0 або 1)

    if deleted_count == 0:  # Якщо сервіс не зміг видалити (не знайдено)
        logger.warning(
            f"Налаштування '{setting_key}' не знайдено для видалення суперкористувачем '{current_superuser.username}'.")  # i18n
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Налаштування з ключем '{setting_key}' не знайдено."  # i18n
        )

    logger.info(
        f"Налаштування '{setting_key}' успішно видалено суперкористувачем '{current_superuser.username}'.")  # i18n
    # Для DELETE з 204 No Content відповідь має бути порожньою
    return None


logger.info("Маршрутизатор для системних налаштувань API v1 (`settings.router`) визначено.")  # i18n
