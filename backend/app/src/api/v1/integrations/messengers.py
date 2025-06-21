# backend/app/src/api/v1/integrations/messengers.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління інтеграціями з платформами месенджерів.

Дозволяє користувачам налаштовувати отримання сповіщень через месенджери,
пов'язуючи свій обліковий запис з ID на відповідній платформі (наприклад, Telegram Chat ID).
Також може включати налаштування для груп (наприклад, куди надсилати групові сповіщення).

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.src.api.dependencies import get_api_db_session, get_current_active_user, get_current_active_superuser
# TODO: Створити/використати залежності для перевірки прав адміна групи
from backend.app.src.api.v1.groups.groups import check_group_edit_permission  # Тимчасово
from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.integrations.messenger import (
    UserMessengerConnectionCreate,  # Перейменовано для ясності: користувач надає свій platform_id
    UserMessengerConnectionResponse,
    GroupMessengerConfigCreate,  # Для налаштувань на рівні групи
    GroupMessengerConfigResponse,
    MessengerPlatformProviderResponse  # Для списку доступних провайдерів
)
# from backend.app.src.core.pagination import PagedResponse, PageParams # Якщо потрібна пагінація
# TODO: Замінити MessengerIntegrationService на конкретні сервіси або сервіс-фабрику
from backend.app.src.services.integrations.messenger_base import BaseMessengerIntegrationService  # Для типізації
from backend.app.src.services.integrations.user_integration_credential_service import \
    UserIntegrationCredentialService  # Для зберігання зв'язків
from backend.app.src.services.dictionaries.messengers import \
    MessengerPlatformService  # Для отримання списку провайдерів
from backend.app.src.config import settings as global_settings
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

router = APIRouter()


# --- Залежності для сервісів ---
# ПРИМІТКА: Цей сервіс (`UserIntegrationCredentialService`) є ключовим для роботи
# інтеграцій з месенджерами та наразі не реалізований. Поточна залежність
# повертає None, що робить залежні ендпоінти нефункціональними.
async def get_user_integration_credential_service(
        session: AsyncSession = Depends(get_api_db_session)) -> UserIntegrationCredentialService:
    """Залежність FastAPI для UserIntegrationCredentialService."""
    # TODO: Створити цей сервіс, відповідальний за CRUD UserIntegration моделі.
    # return UserIntegrationCredentialService(db_session=session)
    logger.warning("[ЗАГЛУШКА] UserIntegrationCredentialService не реалізовано, повертається None.")
    return None  # type: ignore


async def get_messenger_platform_dict_service(
        session: AsyncSession = Depends(get_api_db_session)) -> MessengerPlatformService:
    """Залежність для MessengerPlatformService (довідник)."""
    return MessengerPlatformService(db_session=session)


# --- Ендпоінти для управління підключеннями месенджерів користувача ---

@router.get(
    "/user/providers",
    response_model=List[MessengerPlatformProviderResponse],
    summary="Список доступних платформ месенджерів",  # i18n
    description="Повертає список усіх доступних для інтеграції платформ месенджерів, які налаштовані в системі."  # i18n
)
async def list_available_messenger_platforms(
        provider_service: MessengerPlatformService = Depends(get_messenger_platform_dict_service)
) -> List[MessengerPlatformProviderResponse]:
    """Отримує список всіх доступних платформ месенджерів з довідника."""
    # TODO: Додати пагінацію, якщо список може бути великим (малоймовірно для провайдерів)
    return await provider_service.get_all(limit=100)  # Припускаємо, що get_all повертає Pydantic схеми


@router.post(
    "/user/connections",  # Раніше було /user/config
    response_model=UserMessengerConnectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Підключення месенджера для користувача",  # i18n
    description="""Дозволяє користувачу пов'язати свій обліковий запис системи з акаунтом месенджера
    (наприклад, надати свій Telegram Chat ID після взаємодії з ботом)."""  # i18n
)
# ПРИМІТКА: Цей ендпоінт наразі є заглушкою через відсутність
# `UserIntegrationCredentialService`. Потребує повної реалізації.
async def connect_user_messenger(  # Перейменовано з configure_user_messenger_integration
        connection_in: UserMessengerConnectionCreate,  # Включає platform_code та platform_user_id
        current_user: UserModel = Depends(get_current_active_user),
        # user_integration_service: UserIntegrationCredentialService = Depends(get_user_integration_credential_service) # Розкоментувати
) -> UserMessengerConnectionResponse:
    """
    Зберігає зв'язок між користувачем системи та його ID на платформі месенджера.
    `platform_user_id` користувач зазвичай отримує від бота (наприклад, `/start` команда повертає Chat ID).
    """
    logger.info(
        f"Користувач ID '{current_user.id}' намагається підключити месенджер: {connection_in.platform_code}, Platform User ID: {connection_in.platform_user_id}.")

    # TODO: Замінити заглушку на реальний виклик user_integration_service
    # if not user_integration_service:
    #     raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Сервіс інтеграцій тимчасово недоступний.") # i18n

    # try:
    #     # Сервіс має обробляти створення/оновлення запису UserIntegration
    #     # та валідувати platform_code через довідник MessengerPlatform.
    #     connection_record = await user_integration_service.link_user_to_messenger(
    #         user_id=current_user.id,
    #         platform_code=connection_in.platform_code,
    #         platform_user_id=connection_in.platform_user_id
    #     )
    #     return connection_record # Сервіс повертає UserMessengerConnectionResponse
    # except ValueError as e:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) # i18n
    # except Exception as e:
    #     logger.error(f"Неочікувана помилка: {e}", exc_info=global_settings.DEBUG)
    #     raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.") # i18n

    logger.warning(
        f"[ЗАГЛУШКА] Підключення месенджера для {current_user.id}. Потрібна реалізація UserIntegrationCredentialService.")
    # i18n
    return UserMessengerConnectionResponse(
        user_id=current_user.id,
        platform_code=connection_in.platform_code,
        platform_user_id=connection_in.platform_user_id,
        display_name=f"Mock {connection_in.platform_code} User",  # i18n
        linked_at=datetime.now(timezone.utc)
    )


@router.get(
    "/user/connections",  # Раніше було /user/config
    response_model=List[UserMessengerConnectionResponse],
    summary="Перегляд підключених месенджерів користувача",  # i18n
    description="Повертає список поточних підключень до месенджерів для аутентифікованого користувача."  # i18n
)
# ПРИМІТКА: Цей ендпоінт наразі повертає мок-дані через відсутність
# `UserIntegrationCredentialService`. Потребує повної реалізації.
async def get_user_messenger_connections(  # Перейменовано
        current_user: UserModel = Depends(get_current_active_user),
        # user_integration_service: UserIntegrationCredentialService = Depends(get_user_integration_credential_service) # Розкоментувати
) -> List[UserMessengerConnectionResponse]:
    """Отримує список підключених месенджерів для поточного користувача."""
    logger.info(f"Користувач ID '{current_user.id}' запитує свої підключення до месенджерів.")
    # TODO: Замінити заглушку на реальний виклик user_integration_service
    # if not user_integration_service:
    #     raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Сервіс інтеграцій тимчасово недоступний.") # i18n
    # connections = await user_integration_service.get_user_messenger_connections(user_id=current_user.id)
    # return connections

    logger.warning(f"[ЗАГЛУШКА] Повернення мок-даних для підключень месенджерів користувача {current_user.id}.")
    return [
        UserMessengerConnectionResponse(user_id=current_user.id, platform_code="TELEGRAM",
                                        platform_user_id="mock_tg_chat_id", display_name="Telegram User Mock",
                                        linked_at=datetime.now(timezone.utc))  # i18n
    ]


@router.delete(
    "/user/connections/{platform_code}",  # Раніше було /user/config/{config_id}
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення підключення до месенджера користувача",  # i18n
    description="Дозволяє користувачу видалити своє підключення до вказаної платформи месенджера."  # i18n
)
# ПРИМІТКА: Цей ендпоінт також є заглушкою через відсутність
# `UserIntegrationCredentialService` для реального видалення даних підключення.
async def delete_user_messenger_connection(  # Перейменовано
        platform_code: str = Path(..., description="Код платформи месенджера для відключення (напр., 'TELEGRAM')"),
        # i18n
        current_user: UserModel = Depends(get_current_active_user),
        # user_integration_service: UserIntegrationCredentialService = Depends(get_user_integration_credential_service) # Розкоментувати
):
    """
    Видаляє підключення до месенджера для поточного користувача.
    Сервіс має перевірити, що конфігурація належить користувачу.
    """
    logger.info(f"Користувач ID '{current_user.id}' намагається відключити месенджер: {platform_code}.")
    # TODO: Замінити заглушку на реальний виклик user_integration_service
    # if not user_integration_service:
    #     raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Сервіс інтеграцій тимчасово недоступний.") # i18n
    # success = await user_integration_service.unlink_user_from_messenger(
    #     user_id=current_user.id,
    #     platform_code=platform_code
    # )
    # if not success:
    #     # i18n
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Підключення до {platform_code} не знайдено або не вдалося видалити.")

    logger.warning(f"[ЗАГЛУШКА] Відключення месенджера {platform_code} для {current_user.id}.")
    return None  # HTTP 204 No Content


# --- Ендпоінти для конфігурації месенджерів на рівні групи (заглушки) ---
# TODO: Переглянути та реалізувати логіку для групових налаштувань месенджерів.
#  Це може включати налаштування бота для групи, каналу для сповіщень тощо.

@router.post(
    "/group/{group_id}/config",
    response_model=GroupMessengerConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Налаштування інтеграції месенджера для групи (Адмін/Суперюзер) - ЗАГЛУШКА",  # i18n
    description="Дозволяє адміністратору групи налаштувати інтеграцію з месенджером для групових сповіщень (ЗАГЛУШКА).",
    # i18n
    dependencies=[Depends(get_current_active_superuser)],  # Тимчасово, потрібна гранульована перевірка
    deprecated=True
)
async def configure_group_messenger_integration(
        group_id: UUID = Path(..., description="ID групи"),  # i18n
        config_in: GroupMessengerConfigCreate,  # Включає platform_code, channel_id/webhook_url для групи
        current_admin_or_superuser: UserModel = Depends(get_current_active_superuser),
        # messenger_service: BaseMessengerIntegrationService = Depends(...) # Потрібен відповідний сервіс
):
    logger.warning(
        f"[ЗАГЛУШКА] Налаштування месенджера для групи {group_id} не реалізовано. Дані: {config_in.model_dump_minimal()}")
    # i18n
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED,
                        detail="Функціонал налаштування месенджера для групи ще не реалізовано.")


@router.get(
    "/group/{group_id}/config",
    response_model=List[GroupMessengerConfigResponse],
    summary="Перегляд інтеграцій месенджера для групи (Адмін/Суперюзер) - ЗАГЛУШКА",  # i18n
    description="Повертає список налаштувань інтеграції з месенджерами для вказаної групи (ЗАГЛУШКА).",  # i18n
    dependencies=[Depends(get_current_active_superuser)],  # Тимчасово
    deprecated=True
)
async def get_group_messenger_integrations(
        group_id: UUID = Path(..., description="ID групи"),  # i18n
        current_admin_or_superuser: UserModel = Depends(get_current_active_superuser),
):
    logger.warning(f"[ЗАГЛУШКА] Перегляд налаштувань месенджера для групи {group_id} не реалізовано.")
    return []


logger.info(f"Роутер для інтеграцій з месенджерами (`{router.prefix}`) визначено.")
