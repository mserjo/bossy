# backend/app/src/api/v1/integrations/messengers.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для налаштування інтеграцій з месенджерами API v1.

Цей модуль надає API для користувачів для:
- Підключення/авторизації своїх акаунтів у месенджерах (Telegram, Slack, Viber тощо)
  для отримання сповіщень та/або взаємодії з ботом.
- Обробки OAuth2 callback (для деяких месенджерів, наприклад, Slack).
- Перегляду статусу підключених месенджерів.
- Налаштування типів сповіщень, що надсилатимуться в конкретний месенджер.
- Відключення інтеграції з месенджером.
- Надсилання тестового повідомлення для перевірки інтеграції.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query, Body, Response as FastAPIResponse
from typing import List, Optional, Dict, Any

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.integrations.messenger import (
    MessengerIntegrationSchema,
    MessengerConnectionInfoSchema,
    MessengerNotificationSettingsSchema,
    MessengerNotificationSettingsUpdateSchema,
    TestMessageRequestSchema # Для тестового повідомлення
)
from backend.app.src.services.integrations.messenger_service_factory import MessengerServiceFactory
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.models.auth.user import UserModel

logger = get_logger(__name__)
router = APIRouter()

# Префікс /messengers вже встановлено в integrations/__init__.py

@router.post(
    "/{provider}/initiate-connection",
    response_model=MessengerConnectionInfoSchema,
    tags=["Integrations", "Messengers"],
    summary="Ініціювати підключення до месенджера"
)
async def initiate_messenger_connection(
    provider: str = Path(..., description="Провайдер месенджера (напр., 'telegram', 'slack', 'viber')"),
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} ініціює підключення до месенджера: {provider}.")
    try:
        messenger_service = MessengerServiceFactory.get_service(provider, db_session=db_session, user_id=current_user.id)
        connection_info = await messenger_service.initiate_connection_process()
        # connection_info може містити auth_url для OAuth або інструкції для бота
        return connection_info
    except ValueError as ve: # Провайдер не підтримується
        logger.warning(f"Спроба підключення до непідтримуваного месенджера '{provider}' користувачем {current_user.email}: {str(ve)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Помилка ініціації підключення до месенджера {provider} для {current_user.email}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Помилка сервера при ініціації підключення до {provider}.")

# TODO: Додати ендпоінт /{provider}/callback для месенджерів, що використовують OAuth2 (наприклад, Slack).
# Аналогічно до calendars.py, цей ендпоінт буде обробляти код авторизації та стан.
# @router.get(
#     "/{provider}/callback",
#     response_model=MessengerIntegrationSchema,
#     tags=["Integrations", "Messengers"],
#     summary="Обробка OAuth2 callback від месенджер-сервісу"
# )
# async def messenger_service_oauth_callback(...):
#     # ... логіка обробки callback ...
#     pass

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
    # messenger_service = MessengerServiceFactory.get_generic_service(db_session, user_id=current_user.id)
    # integrations = await messenger_service.get_user_messenger_integrations()
    # return integrations
    # Заглушка:
    return [
        MessengerIntegrationSchema(id=1, user_id=current_user.id, provider_name="telegram", account_identifier="telegram_chat_123", is_active=True, default_for_notifications=True),
        MessengerIntegrationSchema(id=2, user_id=current_user.id, provider_name="slack", account_identifier="slack_user_XYZ", is_active=False, default_for_notifications=False),
    ]

@router.get(
    "/{integration_id}/settings",
    response_model=MessengerNotificationSettingsSchema,
    tags=["Integrations", "Messengers"],
    summary="Отримати налаштування сповіщень для месенджер-інтеграції"
)
async def get_messenger_integration_settings(
    integration_id: int = Path(..., description="ID запису інтеграції месенджера в БД"),
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} запитує налаштування для месенджер-інтеграції ID {integration_id}.")
    # messenger_service = MessengerServiceFactory.get_service_by_integration_id(integration_id, db_session, user_id=current_user.id)
    # settings = await messenger_service.get_notification_settings()
    # if not settings:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Налаштування для цієї інтеграції не знайдено.")
    # return settings
    # Заглушка:
    return MessengerNotificationSettingsSchema(
        integration_id=integration_id,
        user_id=current_user.id, # Додав user_id до схеми для повноти
        receive_task_updates=True,
        receive_bonus_changes=True,
        receive_new_tasks_in_group=False,
        receive_system_alerts=True
    )

@router.put(
    "/{integration_id}/settings",
    response_model=MessengerNotificationSettingsSchema,
    tags=["Integrations", "Messengers"],
    summary="Оновити налаштування сповіщень для месенджер-інтеграції"
)
async def update_my_messenger_integration_settings(
    settings_in: MessengerNotificationSettingsUpdateSchema,
    integration_id: int = Path(..., description="ID інтеграції месенджера"),
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} оновлює налаштування для месенджер-інтеграції ID {integration_id}.")
    # messenger_service = MessengerServiceFactory.get_service_by_integration_id(integration_id, db_session, user_id=current_user.id)
    # updated_settings = await messenger_service.update_notification_settings(settings_in)
    # if not updated_settings:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Не вдалося оновити налаштування: інтеграцію не знайдено.")
    # return updated_settings
    # Заглушка:
    updated_data = settings_in.model_dump(exclude_unset=True)
    # Повертаємо повну схему, імітуючи оновлення існуючих даних
    return MessengerNotificationSettingsSchema(integration_id=integration_id, user_id=current_user.id, **updated_data)

@router.post(
    "/{integration_id}/send-test-message",
    status_code=status.HTTP_200_OK, # Або 202, якщо відправка асинхронна
    tags=["Integrations", "Messengers"],
    summary="Надіслати тестове повідомлення через інтеграцію"
)
async def send_test_messenger_message(
    integration_id: int = Path(..., description="ID інтеграції месенджера"),
    test_message_data: Optional[TestMessageRequestSchema] = Body(None, description="Опціональне повідомлення для тесту"),
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} надсилає тестове повідомлення для інтеграції ID {integration_id}.")
    message_text = test_message_data.message if test_message_data else "Це тестове повідомлення від системи Bossy."
    # messenger_service = MessengerServiceFactory.get_service_by_integration_id(integration_id, db_session, user_id=current_user.id)
    # success = await messenger_service.send_message(text=message_text)
    # if not success:
    #     raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не вдалося надіслати тестове повідомлення.")
    return {"message": "Тестове повідомлення надіслано (або поставлено в чергу на відправку).", "text_sent": message_text}


@router.delete(
    "/{integration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Integrations", "Messengers"],
    summary="Відключити месенджер-інтеграцію"
)
async def disconnect_my_messenger_integration(
    integration_id: int = Path(..., description="ID інтеграції месенджера"),
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} відключає месенджер-інтеграцію ID {integration_id}.")
    # messenger_service = MessengerServiceFactory.get_service_by_integration_id(integration_id, db_session, user_id=current_user.id)
    # success = await messenger_service.disconnect()
    # if not success:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Інтеграцію не знайдено або не вдалося відключити.")
    return FastAPIResponse(status_code=status.HTTP_204_NO_CONTENT)
