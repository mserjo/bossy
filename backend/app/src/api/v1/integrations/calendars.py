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

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Response as FastAPIResponse
from typing import List, Optional, Dict, Any

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.integrations.calendar import (
    CalendarIntegrationSchema,
    CalendarConnectionUrlSchema, # Для відповіді з auth_url
    # CalendarSyncSettingsSchema, # Якщо є налаштування синхронізації
    # CalendarSyncSettingsUpdateSchema
)
from backend.app.src.services.integrations.calendar_service_factory import CalendarServiceFactory # Фабрика для різних провайдерів
# Або конкретні сервіси, якщо фабрика не використовується:
# from backend.app.src.services.integrations.google_calendar_service import GoogleCalendarService
# from backend.app.src.services.integrations.outlook_calendar_service import OutlookCalendarIntegrationService
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.models.auth.user import UserModel

logger = get_logger(__name__)
router = APIRouter()

# Префікс /calendars вже встановлено в integrations/__init__.py

@router.post(
    "/{provider}/connect",
    response_model=CalendarConnectionUrlSchema, # Повертає URL для OAuth авторизації
    tags=["Integrations", "Calendars"],
    summary="Ініціювати підключення до календарного сервісу"
)
async def connect_calendar_service(
    provider: str = Path(..., description="Провайдер календаря (напр., 'google', 'outlook')"),
    redirect_uri: Optional[str] = Query(None, description="URI для редиректу після OAuth (якщо потрібен для генерації URL)"),
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    """
    Ініціює процес OAuth2 для підключення до вказаного календарного сервісу.
    Повертає URL, на який користувач має бути перенаправлений для авторизації.
    """
    logger.info(f"Користувач {current_user.email} ініціює підключення до календаря: {provider}.")
    try:
        calendar_service = CalendarServiceFactory.get_service(provider, db_session=db_session, user_id=current_user.id)
        auth_url = await calendar_service.initiate_connection(redirect_uri_frontend=redirect_uri)
        if not auth_url:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не вдалося згенерувати URL для авторизації.")
        return CalendarConnectionUrlSchema(auth_url=auth_url)
    except ValueError as ve: # Наприклад, якщо провайдер не підтримується
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Помилка ініціації підключення до календаря {provider} для {current_user.email}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")


@router.get(
    "/{provider}/callback",
    response_model=CalendarIntegrationSchema, # Повертає інформацію про успішну інтеграцію
    tags=["Integrations", "Calendars"],
    summary="Обробка OAuth2 callback від календарного сервісу"
)
async def calendar_service_oauth_callback(
    provider: str = Path(..., description="Провайдер календаря"),
    code: Optional[str] = Query(None, description="Авторизаційний код"), # Обов'язковий для багатьох OAuth потоків
    state: Optional[str] = Query(None, description="CSRF токен стану (якщо використовується)"),
    error: Optional[str] = Query(None, description="Помилка від OAuth провайдера"),
    # Поточного користувача потрібно ідентифікувати, часто через 'state' або сесію
    # Для простоти, припустимо, що сервіс може ідентифікувати користувача за 'state' або іншим чином
    # Або передаємо user_id в state і витягуємо його тут.
    # current_user: UserModel = Depends(CurrentActiveUser), # Це не спрацює, якщо це редирект без токена
    db_session: DBSession = Depends()
):
    """
    Обробляє відповідь від OAuth провайдера після авторизації користувачем.
    Отримує токени та зберігає їх, активуючи інтеграцію.
    """
    logger.info(f"Обробка OAuth2 callback від {provider}. Code: {'yes' if code else 'no'}, Error: {error}, State: {state}")

    if error:
        logger.error(f"Помилка OAuth від {provider}: {error}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Помилка авторизації з {provider}: {error}")
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Авторизаційний код не надано.")

    # TODO: Ідентифікація користувача. Часто `state` містить user_id або токен сесії.
    # user_id_from_state = get_user_id_from_state(state) # Потрібна реалізація
    # if not user_id_from_state:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Недійсний або відсутній параметр state.")

    # Тимчасова заглушка для user_id, якщо його немає в state
    temp_user_id_for_callback = 1 # ЗАГЛУШКА - ПОТРІБНО ЗАМІНИТИ НА РЕАЛЬНУ ІДЕНТИФІКАЦІЮ

    try:
        calendar_service = CalendarServiceFactory.get_service(provider, db_session=db_session, user_id=temp_user_id_for_callback)
        integration_info = await calendar_service.handle_oauth_callback(code=code, state=state)
        return integration_info
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Помилка обробки callback від {provider}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при обробці авторизації.")


@router.get(
    "",
    response_model=List[CalendarIntegrationSchema],
    tags=["Integrations", "Calendars"],
    summary="Отримати список підключених календарних інтеграцій"
)
async def list_my_calendar_integrations(
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} запитує список своїх календарних інтеграцій.")
    # Сервіс має повертати список інтеграцій для поточного користувача
    # Припускаємо, що CalendarServiceFactory може надати загальний сервіс для цього,
    # або потрібен окремий UserIntegrationService.
    # Для прикладу, використаємо фабрику для отримання списку.

    # TODO: Реалізувати метод get_user_integrations в CalendarServiceFactory або окремому сервісі
    # integrations = await CalendarServiceFactory.get_user_calendar_integrations(user_id=current_user.id, db_session=db_session)
    # return integrations

    # Заглушка
    return [
        CalendarIntegrationSchema(id=1, user_id=current_user.id, provider_name="google", account_email="user@gmail.com", is_active=True, last_synced_at=None),
    ]


@router.delete(
    "/{integration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Integrations", "Calendars"],
    summary="Відключити календарну інтеграцію"
)
async def disconnect_my_calendar_integration(
    integration_id: int, # ID запису інтеграції в нашій БД
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} відключає календарну інтеграцію ID {integration_id}.")
    # TODO: Реалізувати логіку відключення через сервіс. Сервіс має знайти інтеграцію за ID,
    # перевірити, що вона належить current_user, видалити токени та запис.
    # calendar_service = CalendarServiceFactory.get_service_by_integration_id(integration_id, db_session, current_user.id)
    # success = await calendar_service.disconnect()
    # if not success:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Інтеграцію не знайдено або не вдалося відключити.")
    return FastAPIResponse(status_code=status.HTTP_204_NO_CONTENT)

# Роутер буде підключений в backend/app/src/api/v1/integrations/__init__.py
# з префіксом /calendars
