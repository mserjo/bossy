# backend/app/src/api/external/messenger.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для прийому вебхуків від месенджерів.

Цей модуль містить FastAPI роутери для обробки вебхуків, надісланих
різними месенджерами (Telegram, Viber, Slack, Microsoft Teams тощо).
Вебхуки можуть сповіщати про нові повідомлення, команди від користувачів,
або інші події в месенджерах, що дозволяє реалізувати ботів або інтеграції.

Кожен ендпоінт має бути захищений та валідований відповідно до вимог
конкретного месенджера (наприклад, перевірка секретного токена, IP-адреси).
"""

from fastapi import APIRouter, Request, HTTPException, status, Header, Body
from typing import Any, Dict, Optional

# from backend.app.src.config.logging import get_logger
# from backend.app.src.services.integrations.telegram_service import process_telegram_webhook # Приклад
# from backend.app.src.services.integrations.slack_service import process_slack_webhook # Приклад

# logger = get_logger(__name__)
router = APIRouter()

# TODO: Реалізувати валідацію та обробку для кожного месенджера.

@router.post("/telegram/{bot_token}", tags=["Webhooks", "Messenger"])
async def handle_telegram_webhook(
    request: Request,
    bot_token: str, # Токен бота, може використовуватися для ідентифікації та безпеки
    payload: Dict[str, Any] = Body(...)
):
    """
    Обробляє вебхуки від Telegram Bot API.

    Telegram надсилає оновлення (нові повідомлення, команди тощо) на цей ендпоінт.
    Безпека може забезпечуватися за рахунок секретного шляху (токен бота в URL)
    та/або перевірки IP-адрес серверів Telegram.

    Args:
        request (Request): Об'єкт запиту FastAPI.
        bot_token (str): Токен Telegram бота, переданий у шляху.
        payload (Dict[str, Any]): Об'єкт Update від Telegram.
    """
    # logger.info(f"Отримано вебхук Telegram для токена (частково): ...{bot_token[-6:]}")
    # logger.debug(f"Payload Telegram: {payload}")

    # TODO: Валідація bot_token (наприклад, перевірити, чи такий бот зареєстрований в системі).
    # if not is_valid_telegram_bot_token(bot_token):
    #     logger.warning(f"Отримано вебхук для невідомого Telegram бота: {bot_token}")
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недійсний токен бота")

    # TODO: Перевірка IP-адреси запиту (опціонально, для додаткової безпеки).
    # client_host = request.client.host
    # if not is_telegram_server_ip(client_host):
    #     logger.warning(f"Вебхук Telegram отримано з неавторизованої IP-адреси: {client_host}")
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Неавторизована IP-адреса")

    # TODO: Передача payload на обробку відповідному сервісу/обробнику.
    # await process_telegram_webhook(bot_token, payload)

    # Telegram очікує відповідь 200 OK, тіло відповіді зазвичай ігнорується.
    return {"status": "success", "message": "Вебхук Telegram прийнято."}


@router.post("/slack", tags=["Webhooks", "Messenger"])
async def handle_slack_webhook(
    request: Request,
    # Slack використовує підписані секрети для валідації запитів
    x_slack_request_timestamp: Optional[str] = Header(None, alias="X-Slack-Request-Timestamp"),
    x_slack_signature: Optional[str] = Header(None, alias="X-Slack-Signature"),
    payload: Dict[str, Any] = Body(...) # Може бути `application/x-www-form-urlencoded` або `application/json`
):
    """
    Обробляє вебхуки (події) від Slack.

    Slack надсилає події (Events API) або інтерактивні компоненти на цей ендпоінт.
    Потрібна валідація підпису запиту (`X-Slack-Signature`).

    Args:
        request (Request): Об'єкт запиту FastAPI.
        x_slack_request_timestamp (Optional[str]): Часова мітка запиту від Slack.
        x_slack_signature (Optional[str]): Підпис запиту від Slack.
        payload (Dict[str, Any]): Тіло запиту.
    """
    # logger.info("Отримано вебхук Slack.")
    # raw_body = await request.body() # Потрібне сире тіло для перевірки підпису

    # TODO: Валідація підпису Slack.
    # slack_signing_secret = "YOUR_SLACK_SIGNING_SECRET" # Отримати з конфігурації
    # if not verify_slack_signature(raw_body, x_slack_request_timestamp, x_slack_signature, slack_signing_secret):
    #     logger.warning("Невалідний підпис вебхука Slack.")
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Невалідний підпис Slack")

    # logger.debug(f"Payload Slack: {payload}")

    # Slack може надсилати `challenge` при налаштуванні URL для Events API.
    if payload.get("type") == "url_verification":
        # logger.info("Обробка запиту url_verification від Slack.")
        return {"challenge": payload.get("challenge")}

    # TODO: Обробка інших типів подій або інтерактивних компонентів.
    # await process_slack_webhook(payload)

    return {"status": "success", "message": "Вебхук Slack прийнято."}

# TODO: Додати ендпоінти для Viber, Microsoft Teams та інших месенджерів, якщо потрібно.
# Кожен месенджер має свої особливості автентифікації та формати даних.

# Підключення цього роутера в backend/app/src/api/external/__init__.py:
# from backend.app.src.api.external.messenger import router as messenger_webhook_router
# external_api_router.include_router(messenger_webhook_router, prefix="/messenger")
