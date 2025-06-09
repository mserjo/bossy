# backend/app/src/api/external/messenger.py
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Request, Header, HTTPException, status, Response as FastAPIResponse
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import hashlib # Для перевірки підписів, наприклад, Slack
import hmac # Для перевірки підписів, наприклад, Slack

# from app.src.core.dependencies import get_db_session
# from app.src.config.settings import settings_app # Потрібен для секретів (Slack signing secret, etc.)
# from app.src.services.integrations.messenger import MessengerIntegrationService
# # Або специфічні сервіси:
# from app.src.services.integrations.telegram import TelegramIntegrationService
# from app.src.services.integrations.viber import ViberIntegrationService
# from app.src.services.integrations.slack import SlackIntegrationService
# from app.src.services.integrations.teams import TeamsIntegrationService


logger = logging.getLogger(__name__)
router = APIRouter()

@router.post(
    "/telegram", # Шлях відносно /external/messenger/telegram
    summary="Вебхук для Telegram Bot API",
    description="""Приймає оновлення від Telegram Bot API.
    Безпека може забезпечуватися через секретний токен у URL вебхука (встановлюється при реєстрації вебхука)
    або через перевірку IP-адреси Telegram серверів (менш надійно)."""
)
async def telegram_webhook(
    request: Request
    # telegram_service: TelegramIntegrationService = Depends(),
    # db: AsyncSession = Depends(get_db_session)
):
    '''
    Обробляє оновлення (повідомлення, команди) від Telegram Bot API.
    '''
    payload = await request.json()
    logger.info(f"Отримано вебхук від Telegram: {payload}")

    # Тут логіка обробки update від Telegram
    # await telegram_service.handle_update(payload)

    # Telegram Bot API зазвичай очікує швидку відповідь 200 OK.
    # Тривалі операції слід виносити у фонові задачі.
    return {"status": "telegram webhook received"}

@router.post(
    "/viber", # Шлях відносно /external/messenger/viber
    summary="Вебхук для Viber Bot API",
    description="""Приймає колбеки від Viber Bot API.
    Потребує валідації запиту за допомогою `X-Viber-Content-Signature` заголовка."""
)
async def viber_webhook(
    request: Request,
    x_viber_content_signature: Optional[str] = Header(None, alias="X-Viber-Content-Signature")
    # viber_service: ViberIntegrationService = Depends(),
    # settings: AppSettings = Depends(get_settings) # Для VIBER_AUTH_TOKEN
    # db: AsyncSession = Depends(get_db_session)
):
    '''
    Обробляє колбеки від Viber Bot API.
    - Валідує підпис `X-Viber-Content-Signature`.
    - Обробляє різні типи подій (повідомлення, підписка, відписка).
    '''
    raw_body = await request.body()
    logger.info(f"Отримано вебхук від Viber. Signature: {x_viber_content_signature}")
    # logger.debug(f"Viber raw body: {raw_body.decode(errors='ignore')}")

    # Валідація підпису (приклад, потребує VIBER_AUTH_TOKEN з налаштувань)
    # if not settings_app.VIBER_AUTH_TOKEN: # Припускаємо, що VIBER_AUTH_TOKEN є в settings_app
    #     logger.error("VIBER_AUTH_TOKEN не налаштований. Неможливо валідувати підпис Viber.")
    #     raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Серверна помилка конфігурації Viber.")

    # expected_signature = hmac.new(settings_app.VIBER_AUTH_TOKEN.encode(), raw_body, hashlib.sha256).hexdigest()
    # if not hmac.compare_digest(expected_signature, x_viber_content_signature or ""):
    #     logger.warning(f"Невалідний підпис Viber. Очікуваний: {expected_signature}, Отриманий: {x_viber_content_signature}")
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Невалідний підпис запиту.")

    # logger.info("Підпис Viber валідний.")

    try:
        # Розбір JSON після валідації підпису, оскільки підпис базується на raw body
        payload = await request.json()
        logger.info(f"Viber payload: {payload}")
    except Exception as e:
        logger.error(f"Помилка розбору JSON з Viber вебхука: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Не вдалося розпарсити JSON тіло запиту.")

    # await viber_service.handle_callback(payload)

    # Viber очікує відповідь 200 OK.
    return {"status": "viber webhook received"}


@router.post(
    "/slack", # Шлях відносно /external/messenger/slack
    summary="Вебхук для Slack (Events API, Interactive Components)",
    description="""Приймає події від Slack Events API або запити від Interactive Components.
    Потребує валідації запиту за допомогою `X-Slack-Signature` та `X-Slack-Request-Timestamp`."""
)
async def slack_webhook(
    request: Request,
    x_slack_signature: Optional[str] = Header(None, alias="X-Slack-Signature"),
    x_slack_request_timestamp: Optional[str] = Header(None, alias="X-Slack-Request-Timestamp")
    # slack_service: SlackIntegrationService = Depends(),
    # settings: AppSettings = Depends(get_settings) # Для SLACK_SIGNING_SECRET
    # db: AsyncSession = Depends(get_db_session)
):
    '''
    Обробляє вебхуки від Slack.
    - Валідація підпису (Signing Secret v2).
    - Обробка URL верифікації для Events API.
    - Обробка подій та інтерактивних компонентів.
    '''
    raw_body = await request.body()
    logger.info(f"Отримано вебхук від Slack. Signature: {x_slack_signature}, Timestamp: {x_slack_request_timestamp}")

    # Валідація підпису Slack (приклад, потребує SLACK_SIGNING_SECRET з settings_app)
    # if not settings_app.SLACK_SIGNING_SECRET or not x_slack_signature or not x_slack_request_timestamp:
    #     logger.warning("Відсутні необхідні дані для валідації Slack запиту.")
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Відсутні заголовки для валідації Slack.")

    # import time # Для перевірки timestamp
    # if abs(time.time() - int(x_slack_request_timestamp)) > 60 * 5: # Перевірка, що запит не старший 5 хвилин
    #     logger.warning("Запит Slack застарілий (перевірка timestamp).")
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Застарілий запит Slack.")

    # basestring = f"v0:{x_slack_request_timestamp}:{raw_body.decode('utf-8')}".encode('utf-8')
    # expected_signature = 'v0=' + hmac.new(settings_app.SLACK_SIGNING_SECRET.encode('utf-8'), basestring, hashlib.sha256).hexdigest()

    # if not hmac.compare_digest(expected_signature, x_slack_signature):
    #     logger.warning(f"Невалідний підпис Slack. Очікуваний: {expected_signature}, Отриманий: {x_slack_signature}")
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Невалідний підпис запиту Slack.")

    # logger.info("Підпис Slack валідний.")

    payload_data = {}
    content_type = request.headers.get("content-type", "").lower()

    if "application/json" in content_type:
        try:
            payload_data = await request.json()
            logger.info(f"Slack JSON payload: {payload_data}")
        except Exception as e:
            logger.error(f"Помилка розбору JSON з Slack вебхука: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Не вдалося розпарсити JSON тіло запиту Slack.")
    elif "application/x-www-form-urlencoded" in content_type:
        try:
            form_data = await request.form()
            # Payload для interactive components часто приходить в 'payload' полі форми
            if 'payload' in form_data:
                import json
                payload_data = json.loads(form_data['payload'])
            else:
                payload_data = dict(form_data)
            logger.info(f"Slack Form payload: {payload_data}")
        except Exception as e:
            logger.error(f"Помилка розбору Form-data з Slack вебхука: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Не вдалося розпарсити Form-data тіло запиту Slack.")
    else:
        logger.warning(f"Непідтримуваний Content-Type від Slack: {content_type}")
        # Можна повернути помилку або спробувати прочитати raw_body, якщо це очікується для якихось випадків
        # Для прикладу, повернемо помилку
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f"Непідтримуваний Content-Type: {content_type}")


    # Обробка URL верифікації для Events API (payload буде JSON)
    if payload_data.get("type") == "url_verification":
        challenge = payload_data.get("challenge")
        logger.info(f"Slack URL verification challenge: {challenge}")
        return {"challenge": challenge} # FastAPI автоматично поверне JSON

    # await slack_service.handle_event(payload_data)

    # Slack очікує швидку відповідь 200 OK.
    return {"status": "slack webhook received"}


@router.post(
    "/teams", # Шлях відносно /external/messenger/teams
    summary="Вебхук для Microsoft Teams (Bot Framework)",
    description="""Приймає повідомлення та події для бота Microsoft Teams через Bot Framework.
    Потребує валідації JWT токена в `Authorization` заголовку."""
)
async def teams_webhook(
    request: Request,
    authorization: Optional[str] = Header(None)
    # teams_service: TeamsIntegrationService = Depends(),
    # db: AsyncSession = Depends(get_db_session)
):
    '''
    Обробляє вебхуки від Microsoft Teams.
    - Валідує JWT токен авторизації.
    - Обробляє активності (повідомлення тощо).
    '''
    payload = await request.json()
    logger.info(f"Отримано вебхук від Microsoft Teams: {payload}")
    logger.info(f"Teams Authorization header: {authorization}")

    # Валідація JWT токена (складна логіка, зазвичай через бібліотеку Microsoft Bot Builder)
    # if not await teams_service.validate_auth_header(authorization, payload): # Потрібна реалізація validate_auth_header
    #     logger.warning("Невалідний Authorization токен для Teams.")
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Невалідний Authorization токен.")

    # await teams_service.handle_activity(payload)

    # Teams Bot Framework очікує 200 або 202.
    return {"status": "teams webhook received"}

# Міркування:
# 1.  Специфіка платформ: Кожен месенджер має унікальний API, формат даних та механізми безпеки.
# 2.  Безпека: Валідація запитів є критичною (секретні токени URL, підписи заголовків, JWT).
#     Приклади валідації підписів для Viber та Slack закоментовані, оскільки потребують секретів з налаштувань.
# 3.  Сервіси: Спеціалізовані сервіси (`TelegramIntegrationService` і т.д.) мають інкапсулювати логіку
#     валідації, обробки повідомлень/команд/подій та взаємодії з API відповідної платформи.
# 4.  Асинхронність: Обробка може бути тривалою, тому фонові задачі є рекомендованими.
# 5.  Коментарі: Українською мовою.
# 6.  URL-и: Цей роутер буде підключений до `external_api_router` з префіксом `/messenger`.
# 7.  Обробка Content-Type для Slack: Додано більш гнучку обробку JSON та Form-urlencoded.
