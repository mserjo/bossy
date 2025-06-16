# backend/app/src/api/v1/groups/settings.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління налаштуваннями конкретної групи.

Дозволяє адміністраторам групи або суперкористувачам переглядати та оновлювати
налаштування, специфічні для групи (наприклад, назва валюти бонусів).

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from uuid import UUID  # ID тепер UUID
from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession  # Не використовується прямо, якщо сесія в сервісі

# Повні шляхи імпорту
from backend.app.src.api.dependencies import get_api_db_session, get_current_active_user
# Використовуємо залежність, що перевіряє права адміна групи або суперюзера
from backend.app.src.api.v1.groups.groups import check_group_edit_permission
from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.groups.settings import (
    GroupSettingResponse,
    GroupSettingUpdate
)
from backend.app.src.services.groups.settings import GroupSettingService
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings as global_settings  # Для DEBUG

router = APIRouter(
    # Префікс /{group_id}/settings буде додано в __init__.py батьківського роутера groups
    # Теги також успадковуються/додаються звідти
)


# Залежність для отримання GroupSettingService
async def get_group_setting_service(session: AsyncSession = Depends(get_api_db_session)) -> GroupSettingService:
    """Залежність FastAPI для отримання екземпляра GroupSettingService."""
    return GroupSettingService(db_session=session)

# ПРИМІТКА: Доступ до перегляду налаштувань групи обмежений адміністраторами
# групи або суперюзерами через залежність `check_group_edit_permission`.
# Поведінка при відсутності налаштувань (створення за замовчуванням)
# залежить від реалізації сервісу, як зазначено в TODO.
@router.get(
    "/",  # Відповідає /{group_id}/settings/
    response_model=GroupSettingResponse,
    summary="Отримання налаштувань групи",  # i18n
    description="""Повертає налаштування для вказаної групи.
    Доступно адміністраторам групи або суперюзерам.""",  # i18n
    # Використовуємо check_group_edit_permission, оскільки перегляд налаштувань зазвичай є адмінською дією.
    # Якщо потрібен доступ для звичайних членів, створити окрему залежність check_group_view_permission.
    dependencies=[Depends(check_group_edit_permission)]
)
async def get_group_settings(
        group_id: UUID = Path(..., description="ID групи, для якої отримуються налаштування"),  # i18n
        # current_user_with_permission: UserModel = Depends(check_group_edit_permission), # Користувач вже в current_user з залежності
        settings_service: GroupSettingService = Depends(get_group_setting_service)
) -> GroupSettingResponse:
    """
    Отримує налаштування групи.
    Доступно адміністраторам групи та суперкористувачам.
    """
    logger.debug(f"Запит налаштувань для групи ID: {group_id}")

    # GroupSettingService.get_settings_for_group повертає GroupSettingResponse або None
    group_settings = await settings_service.get_settings_for_group(group_id=group_id)

    if not group_settings:
        # Це може означати, що група не існує (мало б перевіритися в check_group_edit_permission),
        # або налаштування для неї ще не створені.
        # TODO: Розглянути створення налаштувань за замовчуванням в сервісі, якщо їх немає.
        logger.warning(f"Налаштування для групи ID '{group_id}' не знайдено.")
        # i18n
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Налаштування для групи з ID {group_id} не знайдено. Можливо, їх потрібно створити."
        )
    return group_settings

# ПРИМІТКА: Оновлення налаштувань використовує логіку "створити або оновити" (upsert)
# через метод `create_or_update_group_settings` в сервісі. Права доступу
# контролюються залежністю `check_group_edit_permission`.
@router.put(
    "/",  # Відповідає /{group_id}/settings/
    response_model=GroupSettingResponse,
    summary="Оновлення налаштувань групи",  # i18n
    description="Дозволяє адміністраторам групи або суперюзерам оновити налаштування групи.",  # i18n
    dependencies=[Depends(check_group_edit_permission)]
)
async def update_group_settings(
        group_id: UUID = Path(..., description="ID групи, для якої оновлюються налаштування"),  # i18n
        settings_in: GroupSettingUpdate,  # Схема з полями, які можна оновлювати
        current_user_with_permission: UserModel = Depends(check_group_edit_permission),
        # Для аудиту та підтвердження прав
        settings_service: GroupSettingService = Depends(get_group_setting_service)
) -> GroupSettingResponse:
    """
    Оновлює налаштування групи.
    Доступно адміністраторам групи та суперкористувачам.
    Використовує метод сервісу `create_or_update_group_settings` для логіки upsert.
    """
    logger.info(
        f"Користувач ID '{current_user_with_permission.id}' намагається оновити налаштування для групи ID '{group_id}'.")
    try:
        updated_settings = await settings_service.create_or_update_group_settings(
            group_id=group_id,
            settings_data=settings_in,
            current_user_id=current_user_with_permission.id  # Для аудиту
        )
        # Сервіс має кидати ValueError, якщо група не знайдена.
        return updated_settings
    except ValueError as e:  # Наприклад, якщо група не знайдена (перевірка в сервісі)
        logger.warning(f"Помилка оновлення налаштувань для групи ID '{group_id}': {e}")
        # i18n (повідомлення `e` з сервісу)
        # Якщо помилка "група не знайдена", то 404, інакше 400.
        # Припускаємо, що `check_group_edit_permission` вже перевірив існування групи.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Неочікувана помилка при оновленні налаштувань для групи ID '{group_id}': {e}",
                     exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Внутрішня помилка сервера при оновленні налаштувань групи.")


# Примітка: Роутер для налаштувань групи підключається в groups/__init__.py
# до основного groups_router, який в свою чергу підключається до v1_router.
# Шлях до цих ендпоінтів буде, наприклад: /api/v1/groups/{group_id}/settings

logger.info("Роутер для налаштувань груп (`/groups/{group_id}/settings`) визначено.")
