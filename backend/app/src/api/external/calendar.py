# backend/app/src/api/external/calendar.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для прийому вебхуків від календарних сервісів.

Цей модуль містить FastAPI роутери для обробки вебхуків, надісланих
зовнішніми календарними сервісами, такими як Google Calendar, Outlook Calendar тощо.
Вебхуки можуть сповіщати про створення, оновлення або видалення подій,
що дозволяє системі синхронізувати дані з календарями користувачів.

Кожен ендпоінт має бути захищений відповідними механізмами автентифікації
та валідації, специфічними для конкретного календарного сервісу.
"""

from fastapi import APIRouter, Request, HTTPException, status, Header, Body
from typing import Any, Dict, Optional

# from backend.app.src.config.logging import get_logger
# from backend.app.src.services.integrations.google_calendar_service import process_google_calendar_webhook # Приклад
# from backend.app.src.services.integrations.outlook_calendar_service import process_outlook_calendar_webhook # Приклад

# logger = get_logger(__name__)
router = APIRouter()

# TODO: Реалізувати валідацію та обробку для кожного типу календарного сервісу.

@router.post("/google", tags=["Webhooks", "Calendar"])
async def handle_google_calendar_webhook(
    request: Request,
    # Google Calendar надсилає спеціальні заголовки для валідації
    x_goog_channel_id: Optional[str] = Header(None, alias="X-Goog-Channel-ID"),
    x_goog_resource_id: Optional[str] = Header(None, alias="X-Goog-Resource-ID"),
    x_goog_resource_state: Optional[str] = Header(None, alias="X-Goog-Resource-State"), # sync, exists, not_exists
    # Тіло запиту може бути різним, залежно від налаштувань
    payload: Dict[str, Any] = Body(None) # Може бути порожнім для 'sync'
):
    """
    Обробляє вебхуки від Google Calendar.

    Вебхуки Google Calendar використовуються для сповіщень про зміни в ресурсах.
    Потрібна валідація запиту (наприклад, перевірка channel ID, resource ID).

    Args:
        request (Request): Об'єкт запиту FastAPI.
        x_goog_channel_id (Optional[str]): Ідентифікатор каналу сповіщень.
        x_goog_resource_id (Optional[str]): Ідентифікатор ресурсу, що змінився.
        x_goog_resource_state (Optional[str]): Стан ресурсу ('sync', 'exists', 'not_exists').
        payload (Dict[str, Any]): Тіло запиту (може бути відсутнім).
    """
    # logger.info(
    #     f"Отримано вебхук Google Calendar: ChannelID={x_goog_channel_id}, "
    #     f"ResourceID={x_goog_resource_id}, State={x_goog_resource_state}"
    # )
    # if payload:
    #     logger.debug(f"Payload Google Calendar: {payload}")

    # TODO: Валідація запиту. Перевірити, чи Channel ID та Resource ID відомі системі.
    # if not is_valid_google_channel(x_goog_channel_id, x_goog_resource_id):
    #     logger.warning("Невалідний або невідомий вебхук Google Calendar.")
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Невалідний вебхук")

    if x_goog_resource_state == "sync":
        # Це повідомлення про успішну реєстрацію вебхука, зазвичай не потребує обробки даних.
        # logger.info(f"Вебхук Google Calendar успішно синхронізовано: ChannelID={x_goog_channel_id}")
        return {"status": "success", "message": "Вебхук синхронізовано."}

    # TODO: Якщо стан 'exists' або 'not_exists', потрібно запустити процес синхронізації
    # для відповідного ресурсу (календаря).
    # Це може бути постановка завдання в чергу Celery.
    # await process_google_calendar_webhook(
    #     channel_id=x_goog_channel_id,
    #     resource_id=x_goog_resource_id,
    #     resource_state=x_goog_resource_state,
    #     payload=payload
    # )

    return {"status": "success", "message": "Вебхук Google Calendar прийнято до обробки."}


@router.post("/outlook", tags=["Webhooks", "Calendar"])
async def handle_outlook_calendar_webhook(
    request: Request,
    validation_token: Optional[str] = None, # Outlook надсилає validationToken при створенні підписки
    payload: Optional[Dict[str, Any]] = Body(None) # Для сповіщень
):
    """
    Обробляє вебхуки від Outlook Calendar (Microsoft Graph API).

    При створенні підписки Outlook надсилає запит з `validationToken` в URL.
    Сповіщення про зміни надходять як POST запити з JSON payload.

    Args:
        request (Request): Об'єкт запиту FastAPI.
        validation_token (Optional[str]): Токен валідації (передається як query parameter).
        payload (Optional[Dict[str, Any]]): Тіло запиту з інформацією про зміни.
    """
    # Outlook може надсилати validationToken як query parameter при налаштуванні вебхука
    query_validation_token = request.query_params.get("validationToken")

    if query_validation_token:
        # logger.info(f"Отримано запит на валідацію вебхука Outlook Calendar: Token={query_validation_token}")
        # Відповідь має бути validationToken з типом text/plain
        return Response(content=query_validation_token, media_type="text/plain")

    if payload:
        # logger.info("Отримано сповіщення від Outlook Calendar.")
        # logger.debug(f"Payload Outlook Calendar: {payload}")
        # TODO: Обробка сповіщення про зміни.
        # `payload` зазвичай містить масив `value` з об'єктами сповіщень.
        # Кожен об'єкт містить інформацію про тип зміни, ресурс тощо.
        # await process_outlook_calendar_webhook(payload)
        pass
    else:
        # logger.warning("Отримано порожній запит Outlook Calendar (не валідація).")
        # Це може бути непередбачувана ситуація.
        pass


    return {"status": "success", "message": "Вебхук Outlook Calendar прийнято до обробки."}


# TODO: Додати ендпоінти для інших календарних сервісів, якщо потрібно.

# Підключення цього роутера в backend/app/src/api/external/__init__.py:
# from backend.app.src.api.external.calendar import router as calendar_webhook_router
# external_api_router.include_router(calendar_webhook_router, prefix="/calendar")
