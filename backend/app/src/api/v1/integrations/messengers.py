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

from fastapi import APIRouter, Depends, status
from typing import List, Dict, Any

from backend.app.src.config.logging import get_logger
# TODO: Імпортувати схеми для налаштувань інтеграції з месенджерами
# from backend.app.src.schemas.integrations.messenger import MessengerIntegrationSchema, MessengerNotificationSettingsSchema
# TODO: Імпортувати сервіс(и) для інтеграції з месенджерами
# from backend.app.src.services.integrations.telegram_messenger_service import TelegramMessengerService
# TODO: Імпортувати залежності (DBSession, CurrentActiveUser)

logger = get_logger(__name__)
router = APIRouter()

# Ендпоінти можуть бути префіксовані як /integrations/messengers
# або /users/me/integrations/messengers

@router.post(
    "/telegram/connect", # Приклад для Telegram
    # response_model=MessengerIntegrationSchema,
    status_code=status.HTTP_200_OK,
    tags=["Integrations", "Messengers"],
    summary="Підключити Telegram для сповіщень (заглушка)"
)
async def connect_telegram_messenger(
    # current_user: UserModel = Depends(CurrentActiveUser),
    # db_session: DBSession = Depends(),
    # telegram_chat_id: str = Body(None, description="Chat ID користувача в Telegram, якщо відомий")
):
    """
    Налаштовує інтеграцію з Telegram для поточного користувача.
    Може включати інструкції для користувача щодо активації бота або надання Chat ID.
    """
    logger.info(f"Користувач (ID TODO) підключає Telegram (заглушка).")
    # TODO: Реалізувати логіку підключення Telegram.
    # Це може бути збереження chat_id, якщо користувач його надає,
    # або генерація унікального коду для введення боту.
    return {"message": "Інтеграція з Telegram налаштовується (заглушка).", "status": "pending_user_action"}

@router.get(
    "", # Тобто /integrations/messengers або /users/me/integrations/messengers
    # response_model=List[MessengerIntegrationSchema],
    tags=["Integrations", "Messengers"],
    summary="Отримати список підключених месенджер-інтеграцій (заглушка)"
)
async def list_messenger_integrations(
    # current_user: UserModel = Depends(CurrentActiveUser),
    # db_session: DBSession = Depends()
):
    logger.info(f"Користувач (ID TODO) запитує список месенджер-інтеграцій (заглушка).")
    # TODO: Реалізувати отримання списку підключених месенджерів
    return [
        {"id": "tg_user123", "provider": "telegram", "status": "active", "details": "Chat ID: XXXXXX"},
        {"id": "slack_user456", "provider": "slack", "status": "inactive"}
    ]

@router.put(
    "/{integration_id}/settings",
    # response_model=MessengerNotificationSettingsSchema,
    tags=["Integrations", "Messengers"],
    summary="Оновити налаштування сповіщень для месенджер-інтеграції (заглушка)"
)
async def update_messenger_notification_settings(
    integration_id: str,
    # settings_data: MessengerNotificationSettingsUpdateSchema,
    # current_user: UserModel = Depends(CurrentActiveUser),
    # db_session: DBSession = Depends()
):
    logger.info(f"Користувач (ID TODO) оновлює налаштування для месенджер-інтеграції ID {integration_id} (заглушка).")
    # TODO: Реалізувати логіку оновлення налаштувань (які типи сповіщень надсилати)
    return {"integration_id": integration_id, "settings": {"task_alerts": True, "bonus_updates": False}, "message": "Налаштування оновлено."}


@router.delete(
    "/{integration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Integrations", "Messengers"],
    summary="Відключити месенджер-інтеграцію (заглушка)"
)
async def disconnect_messenger_integration(
    integration_id: str,
    # current_user: UserModel = Depends(CurrentActiveUser),
    # db_session: DBSession = Depends()
):
    logger.info(f"Користувач (ID TODO) відключає месенджер-інтеграцію ID {integration_id} (заглушка).")
    # TODO: Реалізувати логіку відключення
    return

# Роутер буде підключений в backend/app/src/api/v1/integrations/__init__.py
