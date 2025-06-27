# backend/app/src/api/external/tracker.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для прийому вебхуків від таск-трекерів.

Цей модуль містить FastAPI роутери для обробки вебхуків, надісланих
популярними таск-трекерами, такими як Jira, Trello тощо.
Вебхуки можуть сповіщати про створення, оновлення завдань, зміну їх статусів,
нові коментарі та інші події в трекері. Це дозволяє інтегрувати систему
з робочими процесами управління проектами.

Кожен ендпоінт має бути захищений та валідований відповідно до вимог
конкретного таск-трекера.
"""

from fastapi import APIRouter, Request, HTTPException, status, Header, Body
from typing import Any, Dict, Optional

# from backend.app.src.config.logging import get_logger
# from backend.app.src.services.integrations.jira_service import process_jira_webhook # Приклад
# from backend.app.src.services.integrations.trello_service import process_trello_webhook # Приклад

# logger = get_logger(__name__)
router = APIRouter()

# TODO: Реалізувати валідацію та обробку для кожного таск-трекера.

@router.post("/jira", tags=["Webhooks", "Tracker"])
async def handle_jira_webhook(
    request: Request,
    # Jira може використовувати різні методи автентифікації для вебхуків
    # (наприклад, секретний URL, базову автентифікацію, JWT токени в заголовках)
    # Тут приклад для простого секретного токена в заголовку
    x_jira_event_type: Optional[str] = Header(None, alias="X-Jira-Event-Type-Name"), # Не стандартний, але корисний
    # authorization: Optional[str] = Header(None), # Для базової автентифікації або Bearer токена
    payload: Dict[str, Any] = Body(...)
):
    """
    Обробляє вебхуки від Jira.

    Jira надсилає POST запити з JSON payload, що описують подію.
    Автентифікація може бути налаштована різними способами.

    Args:
        request (Request): Об'єкт запиту FastAPI.
        x_jira_event_type (Optional[str]): Тип події Jira (якщо передається).
        payload (Dict[str, Any]): Тіло запиту з даними про подію Jira.
    """
    # logger.info(f"Отримано вебхук Jira. Тип події (якщо є): {x_jira_event_type}")
    # logger.debug(f"Payload Jira: {payload}")

    # TODO: Реалізувати механізм автентифікації/авторизації для Jira вебхуків.
    # Це може бути перевірка секретного токена, IP-адреси, JWT тощо.
    # Залежить від налаштувань вебхука в Jira.
    # if not is_valid_jira_webhook_request(request, payload):
    #     logger.warning("Невалідний або неавторизований запит вебхука Jira.")
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Неавторизований вебхук Jira")

    # TODO: Передача payload та типу події на обробку відповідному сервісу.
    # event_name = payload.get("webhookEvent") # Стандартне поле Jira для типу події
    # await process_jira_webhook(event_name, payload)

    return {"status": "success", "message": "Вебхук Jira прийнято."}


@router.api_route("/trello", methods=["POST", "HEAD"], tags=["Webhooks", "Tracker"])
async def handle_trello_webhook(
    request: Request,
    # Trello використовує підпис для валідації, що передається в заголовку X-Trello-Webhook
    x_trello_webhook: Optional[str] = Header(None, alias="X-Trello-Webhook"),
    payload: Optional[Dict[str, Any]] = Body(None) # Trello надсилає JSON payload
):
    """
    Обробляє вебхуки від Trello.

    Trello надсилає POST запити при змінах. Також Trello надсилає HEAD запит
    при створенні вебхука для перевірки доступності URL.

    Args:
        request (Request): Об'єкт запиту FastAPI.
        x_trello_webhook (Optional[str]): Підпис вебхука Trello для валідації.
        payload (Optional[Dict[str, Any]]): Тіло запиту з даними про подію Trello.
    """
    if request.method == "HEAD":
        # Trello очікує 200 OK на HEAD запит при створенні вебхука.
        # logger.info("Отримано HEAD запит від Trello для валідації вебхука.")
        return Response(status_code=status.HTTP_200_OK)

    # Обробка POST запиту
    # logger.info("Отримано POST запит (вебхук) від Trello.")
    # if not payload:
    #     logger.warning("Отримано порожній POST запит від Trello.")
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Порожній payload від Trello")

    # logger.debug(f"Payload Trello: {payload}")

    # TODO: Валідація підпису Trello.
    # Потрібен callback URL (URL цього ендпоінта) та секрет Trello API.
    # trello_api_secret = "YOUR_TRELLO_API_SECRET" # Отримати з конфігурації
    # callback_url = str(request.url) # Повний URL цього ендпоінта
    # raw_body = await request.body()
    # if not verify_trello_signature(raw_body, x_trello_webhook, callback_url, trello_api_secret):
    #     logger.warning("Невалідний підпис вебхука Trello.")
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Невалідний підпис Trello")

    # TODO: Передача payload на обробку відповідному сервісу.
    # await process_trello_webhook(payload)

    return {"status": "success", "message": "Вебхук Trello прийнято."}


# TODO: Додати ендпоінти для інших таск-трекерів, якщо потрібно.

# Підключення цього роутера в backend/app/src/api/external/__init__.py:
# from backend.app.src.api.external.tracker import router as tracker_webhook_router
# external_api_router.include_router(tracker_webhook_router, prefix="/tracker")
