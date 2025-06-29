# backend/app/src/api/v1/integrations/calendars.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для налаштування інтеграцій з календарними сервісами API v1.

Цей модуль надає API для користувачів для:
- Підключення/авторизації своїх календарів (Google Calendar, Outlook Calendar тощо).
- Обробки OAuth2 callback.
- Перегляду статусу підключених календарів.
- Отримання списку доступних календарів з підключеного сервісу.
- Налаштування параметрів синхронізації (наприклад, які календарі синхронізувати).
- Відключення інтеграції з календарем.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Response as FastAPIResponse
from typing import List, Optional, Dict, Any

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.integrations.calendar import (
    CalendarIntegrationSchema,
    CalendarConnectionUrlSchema,
    ExternalCalendarSchema, # Для списку доступних календарів
    CalendarSyncSettingsSchema, # Для налаштувань синхронізації
    CalendarSyncSettingsUpdateSchema
)
from backend.app.src.services.integrations.calendar_service_factory import CalendarServiceFactory
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.models.auth.user import UserModel

logger = get_logger(__name__)
router = APIRouter()

# Префікс /calendars вже встановлено в integrations/__init__.py

@router.post(
    "/{provider}/connect",
    response_model=CalendarConnectionUrlSchema,
    tags=["Integrations", "Calendars"],
    summary="Ініціювати підключення до календарного сервісу"
)
async def connect_calendar_service(
    provider: str = Path(..., description="Провайдер календаря (напр., 'google', 'outlook')"),
    redirect_uri: Optional[str] = Query(None, description="URI для редиректу після OAuth на стороні клієнта (передається в state)"),
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} ініціює підключення до календаря: {provider}.")
    try:
        calendar_service = CalendarServiceFactory.get_service(provider, db_session=db_session, user_id=current_user.id)
        # redirect_uri передається, щоб сервіс міг включити його в state для повернення клієнту
        auth_url = await calendar_service.initiate_connection(frontend_redirect_uri=redirect_uri)
        if not auth_url:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не вдалося згенерувати URL для авторизації.")
        return CalendarConnectionUrlSchema(auth_url=auth_url)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Помилка ініціації підключення до календаря {provider} для {current_user.email}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера при ініціації підключення.")

@router.get(
    "/{provider}/callback",
    response_model=CalendarIntegrationSchema,
    tags=["Integrations", "Calendars"],
    summary="Обробка OAuth2 callback від календарного сервісу"
)
async def calendar_service_oauth_callback(
    provider: str = Path(..., description="Провайдер календаря"),
    code: Optional[str] = Query(None, description="Авторизаційний код"),
    state: Optional[str] = Query(None, description="CSRF токен стану, що може містити user_id та redirect_uri"),
    error: Optional[str] = Query(None, description="Помилка від OAuth провайдера"),
    db_session: DBSession = Depends()
    # Поточний користувач тут не може бути отриманий через Depends(CurrentActiveUser)
    # так як це прямий редирект від OAuth провайдера без Authorization хедера.
    # Ідентифікація користувача має відбуватися через параметр `state`.
):
    logger.info(f"Обробка OAuth2 callback від {provider}. Code: {'yes' if code else 'no'}, Error: {error}, State: {state}")

    if error:
        logger.error(f"Помилка OAuth від {provider}: {error}")
        # TODO: Повернути користувача на frontend з повідомленням про помилку, можливо через redirect_uri зі state
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Помилка авторизації з {provider}: {error}")
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Авторизаційний код не надано.")
    if not state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Параметр state відсутній або недійсний.")

    try:
        # Сервіс має валідувати state, витягнути user_id та оригінальний redirect_uri (якщо є)
        # Потім використовувати user_id для CalendarServiceFactory
        # Це ПРИБЛИЗНА логіка, конкретна реалізація залежить від CalendarServiceFactory.get_service_for_callback
        calendar_service, user_id = await CalendarServiceFactory.get_service_for_callback(provider, state, db_session)
        if not calendar_service or not user_id:
             raise ValueError("Не вдалося визначити користувача або сервіс для обробки callback.")

        integration_info = await calendar_service.handle_oauth_callback(code=code, state=state)
        # TODO: Після успішної обробки callback, можливо, потрібно редиректнути користувача
        # на frontend_redirect_uri, який був збережений/переданий у state.
        # frontend_redirect_uri = get_frontend_redirect_uri_from_state(state)
        # if frontend_redirect_uri:
        #     return RedirectResponse(url=f"{frontend_redirect_uri}?status=success&provider={provider}")
        return integration_info
    except ValueError as ve:
        logger.warning(f"Помилка значення при обробці callback від {provider}: {str(ve)}")
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
    # TODO: Реалізувати сервісний метод для отримання інтеграцій користувача
    # integrations = await SomeIntegrationManagementService(db_session).get_user_calendar_integrations(user_id=current_user.id)
    # return integrations
    return [
        CalendarIntegrationSchema(id=1, user_id=current_user.id, provider_name="google", account_email="user@gmail.com", is_active=True, last_synced_at=None, sync_enabled=False),
    ] # Заглушка

@router.get(
    "/{integration_id}/external-calendars",
    response_model=List[ExternalCalendarSchema],
    tags=["Integrations", "Calendars"],
    summary="Отримати список доступних календарів з підключеного сервісу"
)
async def get_available_external_calendars(
    integration_id: int = Path(..., description="ID існуючої інтеграції календаря"),
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} запитує список зовнішніх календарів для інтеграції ID {integration_id}.")
    # TODO: Сервіс має отримати інтеграцію, перевірити її належність користувачу,
    # використати збережені токени для запиту до зовнішнього API календаря.
    # calendar_service = CalendarServiceFactory.get_service_by_integration_id(integration_id, db_session, current_user.id)
    # external_calendars = await calendar_service.list_available_calendars()
    # return external_calendars
    return [{"id": "primary", "name": "Основний календар (user@gmail.com)", "can_edit": True, "is_selected_for_sync": False}] # Заглушка

@router.get(
    "/{integration_id}/settings",
    response_model=CalendarSyncSettingsSchema,
    tags=["Integrations", "Calendars"],
    summary="Отримати поточні налаштування синхронізації для інтеграції"
)
async def get_calendar_sync_settings(
    integration_id: int = Path(..., description="ID інтеграції календаря"),
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} запитує налаштування синхронізації для інтеграції ID {integration_id}.")
    # TODO: Сервіс має отримати та повернути збережені налаштування синхронізації.
    # settings = await SomeIntegrationManagementService(db_session).get_calendar_sync_settings(integration_id, user_id=current_user.id)
    # if not settings:
    #     raise HTTPException(status_code=404, detail="Налаштування не знайдено")
    # return settings
    return CalendarSyncSettingsSchema(integration_id=integration_id, sync_enabled=False, rules=[]) # Заглушка

@router.put(
    "/{integration_id}/settings",
    response_model=CalendarSyncSettingsSchema,
    tags=["Integrations", "Calendars"],
    summary="Оновити налаштування синхронізації для інтеграції"
)
async def update_calendar_sync_settings(
    settings_in: CalendarSyncSettingsUpdateSchema,
    integration_id: int = Path(..., description="ID інтеграції календаря"),
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} оновлює налаштування синхронізації для інтеграції ID {integration_id}.")
    # TODO: Сервіс має оновити налаштування синхронізації.
    # updated_settings = await SomeIntegrationManagementService(db_session).update_calendar_sync_settings(
    # integration_id, settings_in, user_id=current_user.id
    # )
    # return updated_settings
    return CalendarSyncSettingsSchema(integration_id=integration_id, sync_enabled=settings_in.sync_enabled, rules=settings_in.rules or []) # Заглушка


@router.delete(
    "/{integration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Integrations", "Calendars"],
    summary="Відключити календарну інтеграцію"
)
async def disconnect_my_calendar_integration(
    integration_id: int,
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} відключає календарну інтеграцію ID {integration_id}.")
    # TODO: Реалізувати логіку відключення через сервіс.
    # success = await SomeIntegrationManagementService(db_session).disconnect_calendar(integration_id, user_id=current_user.id)
    # if not success:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Інтеграцію не знайдено або не вдалося відключити.")
    return FastAPIResponse(status_code=status.HTTP_204_NO_CONTENT)
