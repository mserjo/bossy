# backend/app/src/api/v1/integrations/calendars.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для налаштування інтеграцій з календарними сервісами API v1.

Цей модуль надає API для користувачів для:
- Підключення/авторизації своїх календарів (Google Calendar, Outlook Calendar тощо).
- Перегляду статусу підключених календарів.
- Налаштування параметрів синхронізації (наприклад, які календарі синхронізувати).
- Відключення інтеграції з календарем.
"""

from fastapi import APIRouter, Depends, status
from typing import List, Dict, Any

from backend.app.src.config.logging import get_logger
# TODO: Імпортувати схеми для налаштувань інтеграції з календарями
# from backend.app.src.schemas.integrations.calendar import CalendarIntegrationSchema, CalendarSyncSettingsSchema
# TODO: Імпортувати сервіс(и) для інтеграції з календарями
# from backend.app.src.services.integrations.google_calendar_service import GoogleCalendarIntegrationService
# from backend.app.src.services.integrations.outlook_calendar_service import OutlookCalendarIntegrationService
# TODO: Імпортувати залежності (DBSession, CurrentActiveUser)

logger = get_logger(__name__)
router = APIRouter()

# Ендпоінти можуть бути префіксовані як /integrations/calendars
# або /users/me/integrations/calendars, якщо налаштування персональні.

@router.post(
    "/google/connect", # Приклад для Google Calendar
    # response_model=CalendarIntegrationSchema,
    status_code=status.HTTP_200_OK, # Або інший, залежно від OAuth потоку
    tags=["Integrations", "Calendars"],
    summary="Ініціювати підключення до Google Calendar (заглушка)"
)
async def connect_google_calendar(
    # current_user: UserModel = Depends(CurrentActiveUser),
    # db_session: DBSession = Depends()
    # Може вимагати redirect_uri або інші параметри для OAuth
):
    """
    Ініціює процес OAuth2 для підключення Google Calendar користувача.
    Зазвичай повертає URL для редиректу на сторінку згоди Google.
    """
    logger.info(f"Користувач (ID TODO) ініціює підключення Google Calendar (заглушка).")
    # TODO: Реалізувати отримання auth_url від GoogleCalendarIntegrationService
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?..." # Приклад
    return {"auth_url": auth_url, "message": "Перейдіть за цим URL для авторизації."}

@router.get(
    "/google/callback", # Приклад callback URL
    # response_model=CalendarIntegrationSchema,
    tags=["Integrations", "Calendars"],
    summary="Обробка OAuth2 callback від Google Calendar (заглушка)"
)
async def google_calendar_oauth_callback(
    # state: str, # Обов'язковий для перевірки
    # code: str,  # Авторизаційний код від Google
    # current_user: UserModel = Depends(CurrentActiveUser), # Можливо, сесія/state для ідентифікації
    # db_session: DBSession = Depends()
):
    """
    Обробляє відповідь від Google після авторизації користувачем.
    Отримує токени та зберігає їх для подальшої синхронізації.
    """
    logger.info(f"Обробка OAuth2 callback від Google Calendar (заглушка).")
    # TODO: Реалізувати обмін коду на токени та збереження через GoogleCalendarIntegrationService
    return {"message": "Google Calendar успішно підключено (заглушка).", "integration_id": "gcal_123"}

@router.get(
    "", # Тобто /integrations/calendars або /users/me/integrations/calendars
    # response_model=List[CalendarIntegrationSchema],
    tags=["Integrations", "Calendars"],
    summary="Отримати список підключених календарних інтеграцій (заглушка)"
)
async def list_calendar_integrations(
    # current_user: UserModel = Depends(CurrentActiveUser),
    # db_session: DBSession = Depends()
):
    logger.info(f"Користувач (ID TODO) запитує список календарних інтеграцій (заглушка).")
    # TODO: Реалізувати отримання списку підключених календарів для користувача
    return [
        {"id": "gcal_123", "provider": "google", "status": "active", "linked_email": "user@gmail.com"},
        {"id": "outlook_456", "provider": "outlook", "status": "needs_reauth", "linked_email": "user@outlook.com"}
    ]

@router.delete(
    "/{integration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Integrations", "Calendars"],
    summary="Відключити календарну інтеграцію (заглушка)"
)
async def disconnect_calendar_integration(
    integration_id: str, # ID конкретної інтеграції
    # current_user: UserModel = Depends(CurrentActiveUser),
    # db_session: DBSession = Depends()
):
    logger.info(f"Користувач (ID TODO) відключає календарну інтеграцію ID {integration_id} (заглушка).")
    # TODO: Реалізувати логіку відключення (видалення токенів, зупинка синхронізації)
    return

# Роутер буде підключений в backend/app/src/api/v1/integrations/__init__.py
