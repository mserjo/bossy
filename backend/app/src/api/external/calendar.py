# backend/app/src/api/external/calendar.py
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Request, Header, HTTPException, status, Response as FastAPIResponse
from sqlalchemy.ext.asyncio import AsyncSession
import logging

# from app.src.core.dependencies import get_db_session
# from app.src.services.integrations.calendar import CalendarIntegrationService
# # Або специфічні сервіси:
# from app.src.services.integrations.google import GoogleCalendarService
# from app.src.services.integrations.outlook import OutlookCalendarService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post(
    "/google", # Шлях відносно /external/calendar/google
    summary="Вебхук для Google Calendar API",
    description="""Приймає сповіщення від Google Calendar API (Push Notifications).
    Потребує валідації запиту (наприклад, перевірка `X-Goog-Channel-Token`, `X-Goog-Resource-State`).""",
    status_code=status.HTTP_200_OK # Google очікує 2xx відповідь
)
async def google_calendar_webhook(
    request: Request,
    x_goog_channel_id: Optional[str] = Header(None, alias="X-Goog-Channel-ID"),
    x_goog_resource_id: Optional[str] = Header(None, alias="X-Goog-Resource-ID"),
    x_goog_resource_state: Optional[str] = Header(None, alias="X-Goog-Resource-State"), # 'sync', 'exists', 'not_exists'
    x_goog_message_number: Optional[str] = Header(None, alias="X-Goog-Message-Number")
    # google_calendar_service: GoogleCalendarService = Depends(),
    # db: AsyncSession = Depends(get_db_session)
):
    '''
    Обробляє вебхуки від Google Calendar.
    - Валідує запит.
    - Запускає обробку змін в календарі (наприклад, синхронізацію подій).
    '''
    logger.info(f"Отримано вебхук від Google Calendar:")
    logger.info(f"Headers: X-Goog-Channel-ID={x_goog_channel_id}, X-Goog-Resource-ID={x_goog_resource_id}, X-Goog-Resource-State={x_goog_resource_state}, X-Goog-Message-Number={x_goog_message_number}")

    # Важливо: Перевірити токен каналу (X-Goog-Channel-Token), якщо він використовувався при підписці,
    # або інші механізми валідації, надані Google.

    if x_goog_resource_state == "sync":
        logger.info("Це повідомлення про синхронізацію каналу Google Calendar.")
        # Зазвичай нічого не потрібно робити, крім підтвердження отримання
        return {"status": "sync received", "message": "Google Calendar sync webhook processed."}

    # Обробка реальних змін (exists, not_exists)
    # await google_calendar_service.handle_webhook_notification(
    #     channel_id=x_goog_channel_id,
    #     resource_id=x_goog_resource_id,
    #     resource_state=x_goog_resource_state,
    #     headers=dict(request.headers)
    # )

    # Google очікує швидку відповідь 2xx. Тривалі операції - у фонові задачі.
    logger.info("Google Calendar event webhook received, placeholder processing.")
    return {"status": "google calendar event webhook received"}


@router.post(
    "/outlook", # Шлях відносно /external/calendar/outlook
    summary="Вебхук для Outlook Calendar API",
    description="""Приймає сповіщення від Outlook Calendar API (Microsoft Graph Webhooks).
    Потребує валідації запиту (наприклад, параметр `validationToken` при підписці, перевірка `clientState`)."""
    # Статус код буде залежати від типу запиту (200 для validationToken, 202 для сповіщень)
)
async def outlook_calendar_webhook(
    request: Request
    # outlook_calendar_service: OutlookCalendarService = Depends(),
    # db: AsyncSession = Depends(get_db_session)
):
    '''
    Обробляє вебхуки від Outlook Calendar.
    - Обробляє запит валідації підписки (якщо є `validationToken`).
    - Обробляє сповіщення про зміни.
    '''
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Помилка розбору JSON з Outlook вебхука: {e}")
        # Microsoft Graph може надсилати порожнє тіло або не JSON, залежно від ситуації
        # Якщо тіло не JSON, а очікується validationToken, це проблема.
        # Якщо це сповіщення, воно має бути JSON.
        # Повертаємо помилку, якщо не можемо обробити запит.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Не вдалося розпарсити JSON тіло запиту.")

    logger.info(f"Отримано вебхук від Outlook Calendar: {payload}")

    # Обробка запиту валідації підписки (одноразово при створенні підписки)
    if "validationToken" in payload:
        validation_token = payload.get("validationToken")
        logger.info(f"Outlook validation token received: {validation_token}")
        # Згідно документації Microsoft, потрібно повернути validationToken як text/plain зі статусом 200 OK
        return FastAPIResponse(content=validation_token, media_type="text/plain", status_code=status.HTTP_200_OK)

    # Обробка сповіщень про зміни
    # if "value" in payload and isinstance(payload["value"], list):
    #     for notification in payload["value"]:
    #         client_state = notification.get("clientState") # Перевірити, чи співпадає з тим, що було надіслано при підписці
    #         subscription_id = notification.get("subscriptionId")
    #         resource_data = notification.get("resourceData") # Містить ID ресурсу
    #         change_type = notification.get("changeType") # 'created', 'updated', 'deleted'

    #         logger.info(f"Outlook notification: clientState={client_state}, subscriptionId={subscription_id}, changeType={change_type}, resourceId={resource_data.get('id') if resource_data else None}")

    #         # await outlook_calendar_service.handle_webhook_notification(notification_data=notification)

    # Microsoft Graph API очікує відповідь 202 Accepted протягом 3 секунд для сповіщень.
    logger.info("Outlook Calendar event webhook received, placeholder processing. Sending 202 Accepted.")
    return FastAPIResponse(status_code=status.HTTP_202_ACCEPTED)


# Міркування:
# 1.  Специфіка провайдерів: Кожен календарний сервіс (Google, Outlook) має свій формат вебхуків,
#     механізми валідації та очікувані відповіді.
# 2.  Валідація запиту: Критично важлива для безпеки.
#     - Google: `X-Goog-Channel-Token`, `X-Goog-Resource-State`.
#     - Outlook: `validationToken` при підписці, `clientState` в сповіщеннях.
# 3.  Обробка: `CalendarIntegrationService` або специфічні сервіси (`GoogleCalendarService`, `OutlookCalendarService`)
#     мають реалізовувати логіку обробки сповіщень (наприклад, отримання змін, оновлення локальних даних).
# 4.  Асинхронність: Обробка вебхуків має бути швидкою. Тривалі операції слід виносити у фонові задачі.
# 5.  Коментарі: Українською мовою.
# 6.  URL-и: Цей роутер буде підключений до `external_api_router` з префіксом `/calendar`.
#     Шляхи будуть `/external/calendar/google`, `/external/calendar/outlook`.
# 7.  Відповіді: Важливо повертати саме ті статуси та формати, які очікує провайдер вебхука.
#     Для Outlook validationToken - це 200 OK з text/plain. Для сповіщень - 202 Accepted.
#     Для Google - 2xx.
