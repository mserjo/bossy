# backend/app/src/api/external/calendar.py
# -*- coding: utf-8 -*-
"""
Обробники вебхуків для інтеграцій з календарними сервісами.

Ці ендпоінти приймають асинхронні сповіщення від зовнішніх календарних платформ
(наприклад, Google Calendar, Outlook Calendar) про зміни в календарях користувачів,
які надали доступ до своїх даних.
"""
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Request, Header, HTTPException, status, Response as FastAPIResponse
from sqlalchemy.ext.asyncio import AsyncSession
# import logging # Замінено на централізований логер

# Повні шляхи імпорту
from backend.app.src.api.dependencies import get_api_db_session  # Залежність для сесії БД
from backend.app.src.services.integrations.google_calendar_service import GoogleCalendarService
from backend.app.src.services.integrations.outlook_calendar_service import OutlookCalendarService
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings  # Для доступу до VALIDATION_TOKENS або Client State Secrets

router = APIRouter()


# TODO: Розглянути механізм зберігання та перевірки токенів каналів (X-Goog-Channel-Token)
#  та клієнтських станів (clientState для Outlook) для валідації вебхуків.
#  Це може зберігатися в моделі UserIntegration або окремій моделі підписок на вебхуки.

@router.post(
    "/google",
    summary="Вебхук для Google Calendar API Push Notifications",  # i18n
    description="""Приймає сповіщення від Google Calendar API (Push Notifications).
    Потребує валідації запиту (наприклад, перевірка `X-Goog-Channel-Token`, `X-Goog-Resource-State`).""",  # i18n
    status_code=status.HTTP_200_OK  # Google очікує 2xx відповідь для підтвердження отримання
)
async def google_calendar_webhook(
        request: Request,
        x_goog_channel_id: Optional[str] = Header(None, alias="X-Goog-Channel-ID"),
        x_goog_resource_id: Optional[str] = Header(None, alias="X-Goog-Resource-ID"),
        x_goog_resource_state: Optional[str] = Header(None, alias="X-Goog-Resource-State"),
        # 'sync', 'exists', 'not_exists'
        x_goog_message_number: Optional[str] = Header(None, alias="X-Goog-Message-Number"),
        x_goog_channel_token: Optional[str] = Header(None, alias="X-Goog-Channel-Token"),  # Для валідації
        # db: AsyncSession = Depends(get_api_db_session), # Розкоментувати, якщо потрібна сесія БД
        # google_calendar_service: GoogleCalendarService = Depends() # Розкоментувати для ін'єкції сервісу
):
    """
    Обробляє вебхуки від Google Calendar.
    - Валідує запит (TODO: реалізувати повну валідацію).
    - Запускає обробку змін в календарі (TODO: викликати відповідний метод сервісу).
    """
    logger.info(
        f"Отримано вебхук від Google Calendar. Заголовки: X-Goog-Channel-ID={x_goog_channel_id}, "
        f"X-Goog-Resource-ID={x_goog_resource_id}, X-Goog-Resource-State={x_goog_resource_state}, "
        f"X-Goog-Message-Number={x_goog_message_number}, X-Goog-Channel-Token (наявність): {'Так' if x_goog_channel_token else 'Ні'}"
    )

    # TODO: Валідація X-Goog-Channel-Token
    #  Отримати очікуваний токен, збережений під час створення каналу (watch) для `x_goog_channel_id`.
    #  Порівняти з `x_goog_channel_token`. Якщо не співпадають, повернути 401/403.
    #  expected_token = await some_service.get_expected_google_channel_token(x_goog_channel_id)
    #  if not x_goog_channel_token or x_goog_channel_token != expected_token:
    #      logger.error(f"Невалідний або відсутній X-Goog-Channel-Token для каналу {x_goog_channel_id}")
    #      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невалідний токен каналу")

    if x_goog_resource_state == "sync":
        logger.info("Це повідомлення про синхронізацію каналу Google Calendar (sync).")
        # Зазвичай нічого не потрібно робити, крім підтвердження отримання (200 OK)
        # i18n
        return {"status": "sync_received", "message": "Вебхук синхронізації Google Calendar оброблено."}

    # Обробка реальних змін (стани 'exists', 'not_exists')
    # TODO: Делегувати обробку `google_calendar_service.handle_webhook_notification(...)`
    #  Цей метод має бути асинхронним і, можливо, ставити завдання у фонову чергу.
    # await google_calendar_service.handle_webhook_notification(
    #     channel_id=x_goog_channel_id,
    #     resource_id=x_goog_resource_id,
    #     resource_state=x_goog_resource_state,
    #     message_number=x_goog_message_number,
    #     headers=dict(request.headers) # Передача всіх заголовків може бути корисною
    # )

    logger.info(
        f"[ЗАГЛУШКА] Вебхук про подію Google Calendar ({x_goog_resource_state}) отримано. Потрібна подальша обробка.")
    # i18n
    return {"status": "google_event_webhook_received", "message": "Вебхук Google Calendar оброблено (заглушка)."}


@router.post(
    "/outlook",
    summary="Вебхук для Outlook Calendar API (Microsoft Graph)",  # i18n
    description="""Приймає сповіщення від Outlook Calendar API через Microsoft Graph Webhooks.
    Обробляє запит валідації (`validationToken`) та сповіщення про зміни.
    Потребує валідації `clientState` в сповіщеннях, якщо використовується.""",  # i18n
    # Статус код відповіді залежить від типу запиту (200 для validationToken, 202 для сповіщень)
)
async def outlook_calendar_webhook(
        request: Request,
        # db: AsyncSession = Depends(get_api_db_session), # Розкоментувати, якщо потрібна сесія БД
        # outlook_calendar_service: OutlookCalendarService = Depends() # Розкоментувати для ін'єкції сервісу
):
    """
    Обробляє вебхуки від Outlook Calendar (Microsoft Graph).
    - Обробляє запит валідації підписки (якщо є `validationToken`).
    - Обробляє сповіщення про зміни (TODO: викликати відповідний метод сервісу).
    """
    try:
        payload = await request.json()
        logger.info(f"Отримано вебхук від Outlook Calendar. Тіло: {payload}")
    except Exception as e:
        # Якщо тіло не JSON, але є validationToken в query params (деякі старі API Microsoft так робили)
        validation_token_query = request.query_params.get("validationToken")
        if validation_token_query:
            logger.info(f"Отримано validationToken з query параметра для Outlook: {validation_token_query}")
            # i18n
            return FastAPIResponse(content=validation_token_query, media_type="text/plain",
                                   status_code=status.HTTP_200_OK)

        logger.error(f"Помилка розбору JSON з Outlook вебхука або відсутній validationToken в query: {e}",
                     exc_info=True)
        # i18n
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Не вдалося розпарсити JSON тіло запиту або відсутній validationToken.")

    # Обробка запиту валідації підписки (надсилається Microsoft Graph при створенні підписки)
    if "validationToken" in payload:
        validation_token = payload.get("validationToken")
        logger.info(f"Отримано validationToken для Outlook: {validation_token}")
        # Згідно документації Microsoft, потрібно повернути validationToken як text/plain зі статусом 200 OK
        return FastAPIResponse(content=validation_token, media_type="text/plain", status_code=status.HTTP_200_OK)

    # Обробка сповіщень про зміни
    # TODO: Делегувати обробку `outlook_calendar_service.handle_webhook_notification(...)`
    #  Цей метод має бути асинхронним і, можливо, ставити завдання у фонову чергу.
    # if "value" in payload and isinstance(payload["value"], list):
    #     for notification_item in payload["value"]:
    #         client_state_from_notification = notification_item.get("clientState")
    #         # TODO: Валідація client_state, якщо він використовувався при створенні підписки.
    #         #  expected_client_state = await some_service.get_client_state_for_subscription(notification_item.get("subscriptionId"))
    #         #  if client_state_from_notification != expected_client_state:
    #         #      logger.error("Невідповідність clientState у вебхуку Outlook. Можлива підробка.")
    #         #      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невалідний clientState.")
    #
    #         await outlook_calendar_service.handle_webhook_notification(notification_data=notification_item)

    logger.info(
        "[ЗАГЛУШКА] Вебхук про подію Outlook Calendar отримано. Потрібна подальша обробка. Надсилання 202 Accepted.")
    # Microsoft Graph API очікує відповідь 202 Accepted протягом короткого часу (наприклад, 3-5 секунд) для сповіщень.
    return FastAPIResponse(status_code=status.HTTP_202_ACCEPTED)


logger.info("Роутер для вебхуків календарних сервісів (`/external/calendar`) визначено.")
