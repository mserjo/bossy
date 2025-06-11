# backend/app/src/api/external/messenger.py
# -*- coding: utf-8 -*-
"""
Обробники вебхуків для інтеграцій з месенджерами.

Ці ендпоінти призначені для прийому вхідних повідомлень, подій та колбеків
від різних платформ месенджерів, з якими інтегрується система.
Кожен ендпоінт має реалізовувати специфічні для платформи механізми валідації
запитів для забезпечення безпеки.
"""
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Request, Header, HTTPException, status, Response as FastAPIResponse
from sqlalchemy.ext.asyncio import AsyncSession
import hashlib # Для перевірки підписів, наприклад, Slack, Viber
import hmac # Для перевірки підписів
import time # Для перевірки timestamp в Slack запитах

# Повні шляхи імпорту
from backend.app.src.api.dependencies import get_api_db_session # Залежність для сесії БД
from backend.app.src.config import settings as global_settings # Для секретів (Slack signing secret, Viber auth token тощо)
from backend.app.src.config.logging import logger # Централізований логер

# TODO: Імпортувати та ін'єктувати відповідні сервіси інтеграцій, коли вони будуть реалізовані
# from backend.app.src.services.integrations import (
#     TelegramIntegrationService,
#     ViberIntegrationService,
#     SlackIntegrationService,
#     TeamsIntegrationService
# )

router = APIRouter()

@router.post(
    "/telegram",
    summary="Вебхук для Telegram Bot API", # i18n
    description="""Приймає оновлення від Telegram Bot API.
Безпека зазвичай забезпечується через секретний токен, доданий до URL вебхука
при його реєстрації в Telegram (наприклад, `https://your.domain/api/external/messenger/telegram/<SECRET_TOKEN>`).
Цей ендпоінт має перевіряти цей токен, якщо він використовується.
Або можна обмежувати доступ за IP-адресами серверів Telegram.""", # i18n
    status_code=status.HTTP_200_OK # Telegram очікує 200 OK
)
async def telegram_webhook(
    request: Request,
    # telegram_service: TelegramIntegrationService = Depends(), # Розкоментувати для ін'єкції сервісу
    # db: AsyncSession = Depends(get_api_db_session) # Якщо сервіс потребує сесію БД
    # secret_token: Optional[str] = Path(None) # Якщо секретний токен є частиною шляху
):
    """
    Обробляє оновлення (повідомлення, команди) від Telegram Bot API.
    """
    # TODO: Валідація запиту Telegram (наприклад, перевірка secret_token з Path, або IP-адреси)
    # if secret_token != global_settings.TELEGRAM_WEBHOOK_SECRET:
    #     logger.warning(f"Невалідний секретний токен для Telegram вебхука: {secret_token}")
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недійсний токен вебхука")

    payload = await request.json()
    logger.info(f"Отримано вебхук від Telegram: {payload}")

    # TODO: Делегувати обробку оновлення `telegram_service.handle_telegram_update(payload)`
    # Цей метод має бути асинхронним і може ставити завдання у фонову чергу.
    # await telegram_service.handle_telegram_update(payload)

    # Telegram Bot API зазвичай очікує швидку відповідь 200 OK.
    # Тривалі операції слід виносити у фонові задачі.
    # i18n
    return {"status": "telegram_webhook_received", "message": "Вебхук Telegram отримано та поставлено в обробку (заглушка)."}

@router.post(
    "/viber",
    summary="Вебхук для Viber Bot API", # i18n
    description="""Приймає колбеки від Viber Bot API.
Потребує валідації запиту за допомогою заголовка `X-Viber-Content-Signature` та автентифікаційного токена Viber бота.""", # i18n
)
async def viber_webhook(
    request: Request,
    x_viber_content_signature: Optional[str] = Header(None, alias="X-Viber-Content-Signature")
    # viber_service: ViberIntegrationService = Depends(), # Розкоментувати
    # db: AsyncSession = Depends(get_api_db_session) # Якщо потрібно
):
    """
    Обробляє колбеки від Viber Bot API.
    - Валідує підпис `X-Viber-Content-Signature`.
    - Обробляє різні типи подій (повідомлення, підписка, відписка).
    """
    raw_body = await request.body()
    logger.info(f"Отримано вебхук від Viber. Signature: {x_viber_content_signature}")

    # TODO: Критично! Реалізувати валідацію підпису Viber.
    # if not global_settings.VIBER_AUTH_TOKEN:
    #     logger.error("VIBER_AUTH_TOKEN не налаштований. Неможливо валідувати підпис Viber.")
    #     # i18n
    #     raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Сервіс Viber тимчасово недоступний через помилку конфігурації.")
    #
    # expected_signature = hmac.new(global_settings.VIBER_AUTH_TOKEN.encode(), raw_body, hashlib.sha256).hexdigest()
    # if not x_viber_content_signature or not hmac.compare_digest(expected_signature, x_viber_content_signature):
    #     logger.warning(f"Невалідний підпис Viber. Очікуваний: {expected_signature}, Отриманий: {x_viber_content_signature}")
    #     # i18n
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Невалідний підпис запиту.")
    # logger.info("Підпис Viber валідний (або перевірку не виконано - ЗАГЛУШКА).")

    try:
        payload = await request.json() # Розбір JSON після валідації підпису
        logger.info(f"Viber payload: {payload}")
    except Exception as e:
        logger.error(f"Помилка розбору JSON з Viber вебхука: {e}", exc_info=True)
        # i18n
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Не вдалося розпарсити JSON тіло запиту.")

    # TODO: Делегувати обробку `viber_service.handle_viber_callback(payload)`
    # await viber_service.handle_viber_callback(payload)

    # Viber очікує відповідь 200 OK.
    # i18n
    return {"status": "viber_webhook_received", "message": "Вебхук Viber отримано (заглушка, потрібна валідація підпису!)."}


@router.post(
    "/slack",
    summary="Вебхук для Slack (Events API, Interactive Components)", # i18n
    description="""Приймає події від Slack Events API або запити від Interactive Components.
Потребує валідації запиту за допомогою `X-Slack-Signature` та `X-Slack-Request-Timestamp`
із використанням Slack Signing Secret.""", # i18n
)
async def slack_webhook(
    request: Request,
    x_slack_signature: Optional[str] = Header(None, alias="X-Slack-Signature"),
    x_slack_request_timestamp: Optional[str] = Header(None, alias="X-Slack-Request-Timestamp")
    # slack_service: SlackIntegrationService = Depends(), # Розкоментувати
    # db: AsyncSession = Depends(get_api_db_session) # Якщо потрібно
):
    """
    Обробляє вебхуки від Slack.
    - Валідація підпису (Signing Secret v2).
    - Обробка URL верифікації для Events API.
    - Обробка подій та інтерактивних компонентів.
    """
    raw_body = await request.body()
    logger.info(f"Отримано вебхук від Slack. Signature: {x_slack_signature}, Timestamp: {x_slack_request_timestamp}")

    # TODO: Критично! Реалізувати валідацію підпису Slack.
    # if not global_settings.SLACK_SIGNING_SECRET or not x_slack_signature or not x_slack_request_timestamp:
    #     logger.warning("Відсутні необхідні дані для валідації Slack запиту (токен або заголовки).")
    #     # i18n
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Відсутні заголовки для валідації Slack.")
    #
    # if abs(time.time() - int(x_slack_request_timestamp)) > 60 * 5: # Перевірка, що запит не старший 5 хвилин
    #     logger.warning("Запит Slack застарілий (перевірка timestamp).")
    #     # i18n
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Застарілий запит Slack.")
    #
    # basestring = f"v0:{x_slack_request_timestamp}:{raw_body.decode('utf-8')}".encode('utf-8')
    # expected_signature = 'v0=' + hmac.new(global_settings.SLACK_SIGNING_SECRET.encode('utf-8'), basestring, hashlib.sha256).hexdigest()
    #
    # if not hmac.compare_digest(expected_signature, x_slack_signature):
    #     logger.warning(f"Невалідний підпис Slack. Очікуваний: {expected_signature}, Отриманий: {x_slack_signature}")
    #     # i18n
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Невалідний підпис запиту Slack.")
    # logger.info("Підпис Slack валідний (або перевірку не виконано - ЗАГЛУШКА).")

    payload_data: Dict[str, Any] = {}
    content_type = request.headers.get("content-type", "").lower()

    if "application/json" in content_type:
        try: payload_data = await request.json()
        except Exception as e:
            logger.error(f"Помилка розбору JSON з Slack вебхука: {e}", exc_info=True)
            # i18n
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Не вдалося розпарсити JSON тіло запиту Slack.")
    elif "application/x-www-form-urlencoded" in content_type:
        try:
            form_data = await request.form()
            payload_from_form = form_data.get('payload') # Для interactive components
            if payload_from_form and isinstance(payload_from_form, str):
                payload_data = json.loads(payload_from_form)
            else: # Для slash commands, form_data є словником ключів/значень
                payload_data = dict(form_data)
        except Exception as e:
            logger.error(f"Помилка розбору Form-data з Slack вебхука: {e}", exc_info=True)
            # i18n
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Не вдалося розпарсити Form-data тіло запиту Slack.")
    else: # Непідтримуваний тип контенту
        logger.warning(f"Непідтримуваний Content-Type від Slack: {content_type}. Тіло: {raw_body.decode(errors='ignore')[:200]}")
        # i18n
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f"Непідтримуваний Content-Type: {content_type}")

    logger.info(f"Slack payload ({content_type}): {payload_data}")

    # Обробка URL верифікації для Events API
    if payload_data.get("type") == "url_verification":
        challenge = payload_data.get("challenge")
        logger.info(f"Обробка Slack URL verification challenge: {challenge}")
        return {"challenge": challenge} # FastAPI автоматично поверне JSON

    # TODO: Делегувати обробку `slack_service.handle_slack_event(payload_data)`
    # await slack_service.handle_slack_event(payload_data)

    # Slack очікує швидку відповідь 200 OK.
    # i18n
    return {"status": "slack_webhook_received", "message": "Вебхук Slack отримано (заглушка, потрібна валідація підпису!)."}


@router.post(
    "/teams",
    summary="Вебхук для Microsoft Teams (Bot Framework)", # i18n
    description="""Приймає повідомлення та події для бота Microsoft Teams через Bot Framework.
Потребує валідації JWT токена в заголовку `Authorization`.""", # i18n
)
async def teams_webhook(
    request: Request,
    authorization: Optional[str] = Header(None) # Заголовок авторизації
    # teams_service: TeamsIntegrationService = Depends(), # Розкоментувати
    # db: AsyncSession = Depends(get_api_db_session) # Якщо потрібно
):
    """
    Обробляє вебхуки від Microsoft Teams.
    - Валідує JWT токен авторизації (Bot Framework).
    - Обробляє активності (повідомлення тощо).
    """
    payload = await request.json() # Тіло запиту Teams зазвичай JSON
    logger.info(f"Отримано вебхук від Microsoft Teams: {payload}")
    logger.debug(f"Teams Authorization header (наявність): {'Так' if authorization else 'Ні'}")

    # TODO: Критично! Реалізувати валідацію JWT токена Bot Framework.
    #  Це складна логіка, яка зазвичай реалізується за допомогою бібліотеки Microsoft Bot Builder SDK.
    #  Потрібно перевірити `appid` та `serviceUrl` з токена.
    # if not await teams_service.validate_auth_header(authorization_header=authorization, request_body=payload):
    #     logger.warning("Невалідний Authorization токен для Teams вебхука.")
    #     # i18n
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Невалідний Authorization токен.")
    # logger.info("Токен авторизації Teams валідний (або перевірку не виконано - ЗАГЛУШКА).")

    # TODO: Делегувати обробку активності `teams_service.handle_teams_activity(payload)`
    # await teams_service.handle_teams_activity(payload)

    # Teams Bot Framework очікує 200, 201 або 202. Для проактивних повідомлень - відповідь не потрібна.
    # Для отриманих активностей - зазвичай 200 або 202.
    # i18n
    return {"status": "teams_webhook_received", "message": "Вебхук Teams отримано (заглушка, потрібна валідація токена!)."}


logger.info("Роутер для вебхуків месенджерів (`/external/messenger`) визначено.")
