# backend/app/src/api/v1/integrations/messengers.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для налаштування інтеграцій з месенджерами API v1.

Цей модуль надає API для користувачів для:
- Підключення/авторизації своїх акаунтів у месенджерах (Telegram, Slack, Viber тощо)
  для отримання сповіщень та/або взаємодії з ботом.
- Перегляду статусу підключених месенджерів.
- Налаштування типів сповіщень, що надсилатимуться в конкретний месенджер.
- Відключення інтеграції з месенджером.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Path, Body, Response as FastAPIResponse
from typing import List, Optional, Dict, Any

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.integrations.messenger import (
    MessengerIntegrationSchema,
    MessengerConnectionInfoSchema, # Для інформації про підключення (напр. код для бота)
    MessengerNotificationSettingsSchema, # Повна схема налаштувань
    MessengerNotificationSettingsUpdateSchema # Схема для оновлення налаштувань
)
from backend.app.src.services.integrations.messenger_service_factory import MessengerServiceFactory
# Або конкретні сервіси
# from backend.app.src.services.integrations.telegram_service import TelegramService
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.models.auth.user import UserModel

logger = get_logger(__name__)
router = APIRouter()

# Префікс /messengers вже встановлено в integrations/__init__.py

@router.post(
    "/{provider}/initiate-connection",
    response_model=MessengerConnectionInfoSchema, # Може повертати інструкції, код для бота
    tags=["Integrations", "Messengers"],
    summary="Ініціювати підключення до месенджера"
)
async def initiate_messenger_connection(
    provider: str = Path(..., description="Провайдер месенджера (напр., 'telegram', 'slack')"),
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    """
    Ініціює процес підключення до вказаного месенджера для поточного користувача.
    Може повернути унікальний код для активації бота або інструкції.
    """
    logger.info(f"Користувач {current_user.email} ініціює підключення до месенджера: {provider}.")
    try:
        messenger_service = MessengerServiceFactory.get_service(provider, db_session=db_session, user_id=current_user.id)
        connection_info = await messenger_service.initiate_connection_process()
        return connection_info # Наприклад, {"provider": "telegram", "bot_name": "@MyBossyBot", "activation_code": "USER_UNIQUE_CODE"}
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Помилка ініціації підключення до месенджера {provider} для {current_user.email}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")

# Callback для деяких месенджерів (наприклад, Slack OAuth) може знадобитися тут,
# аналогічно до календарів, але часто підключення бота відбувається через токен або код.

@router.get(
    "",
    response_model=List[MessengerIntegrationSchema],
    tags=["Integrations", "Messengers"],
    summary="Отримати список підключених месенджер-інтеграцій"
)
async def list_my_messenger_integrations(
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} запитує список своїх месенджер-інтеграцій.")
    # TODO: Реалізувати через відповідний сервіс (можливо, UserIntegrationService)
    # Заглушка:
    # messenger_service = MessengerServiceFactory.get_generic_service(db_session, user_id=current_user.id)
    # integrations = await messenger_service.get_user_messenger_integrations()
    # return integrations
    return [
        MessengerIntegrationSchema(id=1, user_id=current_user.id, provider_name="telegram", account_identifier="123456789_chat_id", is_active=True, default_for_notifications=True),
    ]

@router.get(
    "/{integration_id}/settings",
    response_model=MessengerNotificationSettingsSchema,
    tags=["Integrations", "Messengers"],
    summary="Отримати налаштування сповіщень для месенджер-інтеграції"
)
async def get_messenger_integration_settings(
    integration_id: int, # ID нашого запису інтеграції
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} запитує налаштування для месенджер-інтеграції ID {integration_id}.")
    # TODO: Сервіс має знайти інтеграцію, перевірити, що вона належить користувачу,
    # і повернути її налаштування сповіщень.
    # messenger_service = MessengerServiceFactory.get_service_by_integration_id(integration_id, db_session, user_id=current_user.id)
    # settings = await messenger_service.get_notification_settings()
    # if not settings:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Налаштування не знайдено.")
    # return settings
    return MessengerNotificationSettingsSchema(
        integration_id=integration_id,
        receive_task_updates=True,
        receive_bonus_changes=True,
        receive_new_tasks_in_group=False
    )


@router.put(
    "/{integration_id}/settings",
    response_model=MessengerNotificationSettingsSchema,
    tags=["Integrations", "Messengers"],
    summary="Оновити налаштування сповіщень для месенджер-інтеграції"
)
async def update_my_messenger_integration_settings(
    integration_id: int,
    settings_in: MessengerNotificationSettingsUpdateSchema,
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} оновлює налаштування для месенджер-інтеграції ID {integration_id}.")
    # TODO: Сервіс має знайти інтеграцію, перевірити власника, оновити налаштування.
    # messenger_service = MessengerServiceFactory.get_service_by_integration_id(integration_id, db_session, user_id=current_user.id)
    # updated_settings = await messenger_service.update_notification_settings(settings_in)
    # if not updated_settings:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Не вдалося оновити налаштування.")
    # return updated_settings
    # Заглушка
    updated_data = settings_in.model_dump(exclude_unset=True)
    return MessengerNotificationSettingsSchema(integration_id=integration_id, **updated_data)


@router.delete(
    "/{integration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Integrations", "Messengers"],
    summary="Відключити месенджер-інтеграцію"
)
async def disconnect_my_messenger_integration(
    integration_id: int,
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} відключає месенджер-інтеграцію ID {integration_id}.")
    # TODO: Сервіс має знайти інтеграцію, перевірити власника, видалити дані інтеграції.
    # messenger_service = MessengerServiceFactory.get_service_by_integration_id(integration_id, db_session, user_id=current_user.id)
    # success = await messenger_service.disconnect()
    # if not success:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Інтеграцію не знайдено або не вдалося відключити.")
    return FastAPIResponse(status_code=status.HTTP_204_NO_CONTENT)

# Роутер буде підключений в backend/app/src/api/v1/integrations/__init__.py
# з префіксом /messengers
