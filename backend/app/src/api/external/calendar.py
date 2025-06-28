# backend/app/src/api/external/calendar.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для прийому вебхуків від календарних сервісів (API v1).

Цей модуль містить FastAPI роутери для обробки вебхуків, надісланих
зовнішніми календарними сервісами, такими як Google Calendar, Outlook Calendar тощо.
Вебхуки сповіщають про створення, оновлення або видалення подій,
що дозволяє системі синхронізувати дані з календарями користувачів.

Безпека: Кожен ендпоінт має бути захищений валідацією запиту,
специфічною для провайдера (перевірка підписів, токенів).
Обробка даних з вебхука має бути швидкою, а тривалі операції
(синхронізація) слід виносити у фонові завдання.
"""

from fastapi import APIRouter, Request, HTTPException, status, Header, Body, Response as FastAPIResponse
from typing import Any, Dict, Optional

from backend.app.src.config.logging import get_logger
# TODO: Імпортувати сервіси/функції для обробки вебхуків та постановки завдань в чергу
# from backend.app.src.services.integrations.google_calendar_service import queue_google_webhook_processing
# from backend.app.src.services.integrations.outlook_calendar_service import queue_outlook_webhook_processing
# from backend.app.src.core.security import verify_google_webhook, verify_outlook_webhook # Функції валідації

logger = get_logger(__name__)
router = APIRouter()

@router.post("/google", tags=["Webhooks", "Calendar"], summary="Обробка вебхуків Google Calendar")
async def handle_google_calendar_webhook(
    request: Request,
    x_goog_channel_id: Optional[str] = Header(None, alias="X-Goog-Channel-ID"),
    x_goog_resource_id: Optional[str] = Header(None, alias="X-Goog-Resource-ID"),
    x_goog_resource_state: Optional[str] = Header(None, alias="X-Goog-Resource-State"),
    x_goog_channel_token: Optional[str] = Header(None, alias="X-Goog-Channel-Token"), # Для валідації
    payload: Dict[str, Any] = Body(None)
):
    logger.info(
        f"Отримано вебхук Google Calendar: ChannelID={x_goog_channel_id}, "
        f"ResourceID={x_goog_resource_id}, State={x_goog_resource_state}, Token: {'present' if x_goog_channel_token else 'absent'}"
    )
    if payload:
        logger.debug(f"Payload Google Calendar: {payload}")

    # TODO: Реалізувати надійну валідацію вебхука Google
    # if not await verify_google_webhook(request, x_goog_channel_id, x_goog_channel_token):
    #     logger.warning("Невалідний вебхук Google Calendar (помилка валідації).")
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Невалідний запит вебхука.")

    if x_goog_resource_state == "sync":
        logger.info(f"Вебхук Google Calendar успішно синхронізовано (канал підтверджено): ChannelID={x_goog_channel_id}")
        return {"status": "success", "message": "Вебхук синхронізовано."}

    if x_goog_resource_state in ["exists", "not_exists"]: # 'exists' означає зміни
        logger.info(f"Вебхук Google Calendar: є зміни для ресурсу {x_goog_resource_id} (стан: {x_goog_resource_state}).")
        # TODO: Поставити завдання в чергу для асинхронної обробки/синхронізації
        # await queue_google_webhook_processing(
        #     channel_id=x_goog_channel_id,
        #     resource_id=x_goog_resource_id,
        #     resource_state=x_goog_resource_state,
        #     payload=payload
        # )
        return {"status": "success", "message": "Вебхук Google Calendar прийнято до обробки."}

    logger.warning(f"Отримано вебхук Google Calendar з невідомим станом: {x_goog_resource_state}")
    return {"status": "ignored", "message": f"Стан '{x_goog_resource_state}' не обробляється."}


@router.post("/outlook", tags=["Webhooks", "Calendar"], summary="Обробка вебхуків Outlook Calendar")
async def handle_outlook_calendar_webhook(
    request: Request,
    # Outlook надсилає validationToken як query parameter при створенні/оновленні підписки
    # Сповіщення про зміни приходять як POST з JSON payload
):
    query_validation_token = request.query_params.get("validationToken")

    if query_validation_token:
        logger.info(f"Отримано запит на валідацію вебхука Outlook Calendar: Token={query_validation_token}")
        # Відповідь має бути validationToken з типом text/plain та статусом 200 OK
        return FastAPIResponse(content=query_validation_token, media_type="text/plain")

    try:
        payload = await request.json()
        logger.info("Отримано сповіщення від Outlook Calendar.")
        logger.debug(f"Payload Outlook Calendar: {payload}")

        # TODO: Реалізувати валідацію вебхука Outlook (наприклад, перевірка clientState, якщо використовується)
        # if not await verify_outlook_webhook(request, payload): # Потрібна функція валідації
        #     logger.warning("Невалідний вебхук Outlook Calendar.")
        #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Невалідний запит вебхука.")

        # TODO: Обробка сповіщення про зміни.
        # `payload` зазвичай містить масив `value` з об'єктами сповіщень.
        # Кожен об'єкт містить інформацію про тип зміни, ресурс тощо.
        # Поставити завдання в чергу для асинхронної обробки.
        # await queue_outlook_webhook_processing(payload)

        return {"status": "success", "message": "Вебхук Outlook Calendar прийнято до обробки."}
    except Exception as e:
        body_bytes = await request.body()
        logger.error(f"Помилка обробки вебхука Outlook Calendar. Тіло запиту: {body_bytes.decode_error('ignore', errors='replace')}. Помилка: {e}", exc_info=True)
        # Повертаємо 202 Accepted, щоб Microsoft Graph не намагався повторно надсилати,
        # якщо помилка на нашому боці, а не в запиті. Або 500, якщо це дійсно наша проблема.
        # Якщо помилка парсингу JSON, то FastAPI автоматично поверне 400.
        # Якщо це не помилка валідації, а внутрішня, то 500.
        # Для вебхуків часто краще відповідати 2xx, щоб уникнути повторних спроб відправника.
        # Але якщо це помилка самого вебхука (невалідний формат), то 400.
        # Тут, якщо json() не вдався, FastAPI вже повернув 400. Якщо інша помилка - 500.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при обробці вебхука.")


# Цей роутер буде підключений в backend/app/src/api/external/__init__.py
# з префіксом /calendar. Тоді шляхи будуть /external/calendar/google тощо.
