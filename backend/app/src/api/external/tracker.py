# backend/app/src/api/external/tracker.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для прийому вебхуків від таск-трекерів (API v1).

Цей модуль містить FastAPI роутери для обробки вебхуків, надісланих
популярними таск-трекерами, такими як Jira, Trello тощо.
Вебхуки можуть сповіщати про створення, оновлення завдань, зміну їх статусів,
нові коментарі та інші події в трекері. Це дозволяє інтегрувати систему
з робочими процесами управління проектами.

Безпека: Кожен ендпоінт має бути захищений валідацією запиту,
специфічною для провайдера. Обробка даних має бути швидкою,
а тривалі операції (синхронізація) слід виносити у фонові завдання.
Ідентифікація конкретної інтеграції (користувача/групи) є важливою.
"""

from fastapi import APIRouter, Request, HTTPException, status, Header, Body, Response as FastAPIResponse, Path
from typing import Any, Dict, Optional

from backend.app.src.config.logging import get_logger
# TODO: Імпортувати сервіси/функції для обробки вебхуків та постановки завдань в чергу
# from backend.app.src.services.integrations.jira_service import queue_jira_webhook_processing
# from backend.app.src.services.integrations.trello_service import queue_trello_webhook_processing
# from backend.app.src.core.security import verify_jira_webhook, verify_trello_signature
# from backend.app.src.core.config import settings # Для секретів

logger = get_logger(__name__)
router = APIRouter()

@router.post("/jira/{integration_identifier}", tags=["Webhooks", "Tracker"], summary="Обробка вебхуків Jira")
async def handle_jira_webhook(
    request: Request,
    integration_identifier: str = Path(..., description="Унікальний ідентифікатор налаштованої інтеграції Jira"),
    # x_jira_event_type: Optional[str] = Header(None, alias="X-Jira-Event-Type-Name"), # Нестандартний, але може бути корисним
    payload: Dict[str, Any] = Body(...)
):
    logger.info(f"Отримано вебхук Jira для інтеграції: {integration_identifier}. Подія: {payload.get('webhookEvent')}")
    logger.debug(f"Payload Jira: {payload}")

    # TODO: Реалізувати надійну валідацію вебхука Jira:
    # 1. Знайти конфігурацію інтеграції за `integration_identifier`.
    # 2. Використати збережений секрет або інший механізм для валідації запиту
    #    (наприклад, Basic Auth, JWT, перевірка IP, якщо Jira On-Premise).
    # if not await verify_jira_webhook(request, integration_identifier, payload):
    #     logger.warning(f"Невалідний вебхук Jira для інтеграції {integration_identifier}.")
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Невалідний запит вебхука Jira.")

    # TODO: Поставити `payload` та `event_name = payload.get("webhookEvent")` в чергу
    # для асинхронної обробки, пов'язаної з `integration_identifier`.
    # await queue_jira_webhook_processing(integration_identifier, payload.get("webhookEvent"), payload)

    return {"status": "success", "message": "Вебхук Jira прийнято до обробки."}


@router.api_route("/trello/{integration_identifier}", methods=["POST", "HEAD"], tags=["Webhooks", "Tracker"], summary="Обробка вебхуків Trello")
async def handle_trello_webhook(
    request: Request,
    integration_identifier: str = Path(..., description="Унікальний ідентифікатор налаштованої інтеграції Trello"),
    x_trello_webhook: Optional[str] = Header(None, alias="X-Trello-Webhook"), # Підпис Trello
):
    if request.method == "HEAD":
        logger.info(f"Отримано HEAD запит від Trello для валідації вебхука інтеграції: {integration_identifier}.")
        # Trello очікує 200 OK на HEAD запит при створенні/оновленні вебхука.
        # Тут можна додатково перевірити, чи існує `integration_identifier`.
        return FastAPIResponse(status_code=status.HTTP_200_OK)

    # Обробка POST запиту
    logger.info(f"Отримано POST вебхук від Trello для інтеграції: {integration_identifier}.")

    raw_body = await request.body()
    try:
        payload = await request.json() # Trello надсилає JSON
        logger.debug(f"Payload Trello: {payload}")
    except Exception as e:
        logger.error(f"Помилка розбору JSON з Trello вебхука для {integration_identifier}: {e}. Тіло: {raw_body.decode(errors='replace')}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некоректний JSON payload від Trello.")

    # TODO: Реалізувати надійну валідацію підпису Trello:
    # 1. Знайти конфігурацію інтеграції за `integration_identifier`, отримати Trello API Secret.
    # 2. Сформувати callback URL (URL цього ендпоінта).
    # callback_url = str(request.url)
    # if not await verify_trello_signature(raw_body, x_trello_webhook, callback_url, trello_api_secret_for_integration):
    #     logger.warning(f"Невалідний підпис вебхука Trello для інтеграції {integration_identifier}.")
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Невалідний підпис Trello.")

    # TODO: Поставити `payload` в чергу для асинхронної обробки,
    # пов'язаної з `integration_identifier`.
    # await queue_trello_webhook_processing(integration_identifier, payload)

    return {"status": "success", "message": "Вебхук Trello прийнято до обробки."}


# TODO: Додати ендпоінти для інших таск-трекерів (Asana, GitHub Issues тощо), якщо планується.
# Кожен матиме свій механізм вебхуків та валідації.

# Цей роутер буде підключений в backend/app/src/api/external/__init__.py
# з префіксом /tracker. Тоді шляхи будуть /external/tracker/jira/{integration_id} тощо.
