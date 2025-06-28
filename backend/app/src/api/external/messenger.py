# backend/app/src/api/external/messenger.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для прийому вебхуків від месенджерів (API v1).

Цей модуль містить FastAPI роутери для обробки вебхуків, надісланих
різними месенджерами (Telegram, Slack, Viber, Microsoft Teams, WhatsApp тощо).
Вебхуки можуть сповіщати про нові повідомлення, команди від користувачів,
або інші події в месенджерах, що дозволяє реалізувати ботів або інтеграції.

Безпека: Кожен ендпоінт має бути захищений валідацією запиту,
специфічною для провайдера (перевірка секретних токенів, підписів, IP-адрес).
Обробка даних з вебхука має бути швидкою, а тривалі операції
слід виносити у фонові завдання.
"""

from fastapi import APIRouter, Request, HTTPException, status, Header, Body, Response as FastAPIResponse
from typing import Any, Dict, Optional

from backend.app.src.config.logging import get_logger
# TODO: Імпортувати сервіси/функції для обробки вебхуків та постановки завдань в чергу
# from backend.app.src.services.integrations.telegram_service import queue_telegram_update_processing
# from backend.app.src.services.integrations.slack_service import queue_slack_event_processing
# from backend.app.src.core.security import verify_telegram_webhook, verify_slack_signature
# from backend.app.src.core.config import settings # Для секретів

logger = get_logger(__name__)
router = APIRouter()

@router.post("/telegram/{bot_token_path}", tags=["Webhooks", "Messenger"], summary="Обробка вебхуків Telegram")
async def handle_telegram_webhook(
    request: Request,
    bot_token_path: str = Path(..., description="Частина шляху, що містить токен бота або його ідентифікатор"),
    payload: Dict[str, Any] = Body(...)
):
    logger.info(f"Отримано вебхук Telegram для шляху /telegram/{bot_token_path}")
    logger.debug(f"Payload Telegram: {payload}")

    # TODO: Реалізувати надійну валідацію вебхука Telegram:
    # 1. Перевірити `bot_token_path` - чи відповідає він зареєстрованому боту в системі.
    #    Секретний токен самого бота не має бути частиною публічного URL повністю.
    #    Краще використовувати унікальний секретний суфікс у шляху, який знає тільки наш додаток і Telegram.
    #    Наприклад, `settings.TELEGRAM_WEBHOOK_SECRET_PATH_SUFFIX`.
    #    if bot_token_path != settings.TELEGRAM_WEBHOOK_SECRET_PATH_SUFFIX:
    #        logger.warning(f"Невірний секретний шлях для Telegram вебхука: {bot_token_path}")
    #        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ заборонено.")
    # 2. Опціонально: Перевірити IP-адресу запиту (чи належить вона до діапазону IP-адрес Telegram).
    #    client_host = request.client.host
    #    if not await verify_telegram_webhook(request, bot_token_from_db): # Функція перевірки
    #        logger.warning(f"Невалідний вебхук Telegram (помилка валідації IP або токена) для {bot_token_path} від {client_host}.")
    #        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Невалідний запит вебхука.")

    # TODO: Поставити `payload` (Telegram Update object) в чергу для асинхронної обробки.
    # await queue_telegram_update_processing(payload, bot_token_path) # bot_token_path може ідентифікувати конфігурацію бота

    # Telegram очікує відповідь 200 OK протягом короткого часу.
    return {"status": "success", "message": "Вебхук Telegram прийнято до обробки."}


@router.post("/slack", tags=["Webhooks", "Messenger"], summary="Обробка вебхуків Slack")
async def handle_slack_webhook(
    request: Request,
    # Slack використовує підписані секрети для валідації запитів
    # x_slack_request_timestamp: Optional[str] = Header(None, alias="X-Slack-Request-Timestamp"),
    # x_slack_signature: Optional[str] = Header(None, alias="X-Slack-Signature"),
    # Тіло може бути application/json (Events API) або application/x-www-form-urlencoded (Slash Commands, Interactive Components)
    # FastAPI автоматично розбере JSON, для form-data може знадобитися `payload: Dict[str, Any] = Depends(parse_slack_payload)`
):
    logger.info("Отримано вебхук Slack.")

    # Slack вимагає перевірки підпису для всіх запитів, крім url_verification.
    # Для цього потрібне сире тіло запиту.
    # raw_body = await request.body()
    # timestamp_header = request.headers.get("X-Slack-Request-Timestamp")
    # signature_header = request.headers.get("X-Slack-Signature")

    # TODO: Реалізувати надійну валідацію підпису Slack.
    # if not await verify_slack_signature(raw_body, timestamp_header, signature_header, settings.SLACK_SIGNING_SECRET):
    #     logger.warning("Невалідний підпис вебхука Slack.")
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Невалідний підпис Slack.")

    # Обробка JSON payload для Events API
    try:
        payload = await request.json()
        logger.debug(f"Payload Slack (JSON): {payload}")

        if payload.get("type") == "url_verification":
            challenge = payload.get("challenge")
            logger.info(f"Обробка запиту url_verification від Slack, challenge: {challenge}")
            return {"challenge": challenge}

        # TODO: Поставити `payload` (Slack Event) в чергу для асинхронної обробки.
        # await queue_slack_event_processing(payload)
        return {"status": "success", "message": "Вебхук Slack (JSON) прийнято."}

    except Exception as json_err:
        logger.debug(f"Не вдалося розпарсити Slack payload як JSON: {json_err}. Спроба як form data.")
        # Спроба обробити як form data (для Slash Commands, Interactive Components)
        try:
            form_data = await request.form()
            payload_str = form_data.get("payload") # Для інтерактивних компонентів payload вкладений
            if payload_str:
                import json
                payload = json.loads(payload_str)
                logger.debug(f"Payload Slack (Interactive Component): {payload}")
            else: # Для Slash Commands
                payload = dict(form_data)
                logger.debug(f"Payload Slack (Slash Command): {payload}")

            # TODO: Поставити `payload` в чергу для асинхронної обробки.
            # await queue_slack_event_processing(payload)
            # Для Slash Commands та деяких Interactive Components може знадобитися негайна відповідь.
            # Залежить від типу взаємодії. Якщо потрібна негайна відповідь, обробка не може бути повністю асинхронною.
            return FastAPIResponse(content="Обробка команди...", media_type="text/plain") # Приклад відповіді для Slash Command
        except Exception as form_err:
            raw_body_for_log = await request.body() # Читаємо ще раз для логування
            logger.error(f"Помилка обробки вебхука Slack. Не вдалося розпарсити як JSON або form-data. Тіло: {raw_body_for_log.decode(errors='replace')}. Помилка: {form_err}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Невірний формат запиту Slack.")


# TODO: Додати ендпоінти для Viber, Microsoft Teams, WhatsApp.
# - Viber: Потребує перевірки підпису X-Viber-Content-Signature.
# - Microsoft Teams: Боти взаємодіють через Bot Framework, вебхуки для сповіщень (Incoming Webhooks).
# - WhatsApp: Через WhatsApp Business API, вебхуки для повідомлень, статусів.

# Цей роутер буде підключений в backend/app/src/api/external/__init__.py
# з префіксом /messenger. Тоді шляхи будуть /external/messenger/telegram/{token} тощо.
