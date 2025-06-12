# backend/app/src/api/v1/integrations/calendars.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління інтеграціями з календарними сервісами.

Включає підключення облікових записів користувачів до зовнішніх календарних платформ
(наприклад, Google Calendar, Outlook Calendar) через OAuth2, відключення,
а також управління конфігураціями інтеграцій на рівні користувача та групи.
"""
from typing import List, Optional, Dict, Any  # Generic, TypeVar, BaseModel не потрібні
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, \
    Request as FastAPIRequest  # Query, Path, FastAPIRequest
from fastapi.responses import RedirectResponse  # Для OAuth2 потоку

from sqlalchemy.ext.asyncio import AsyncSession

# Повні шляхи імпорту
from backend.app.src.api.dependencies import get_api_db_session, get_current_active_user, get_current_active_superuser
from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.integrations.calendar import (
    # UserCalendarConfigCreate, # Може не знадобитися, якщо конфігурація через OAuth
    UserCalendarConnectionResponse,  # Схема для відображення статусу підключення
    GroupCalendarConfigCreate,  # Якщо є налаштування на рівні групи
    GroupCalendarConfigResponse,
    CalendarProviderResponse  # Для списку доступних провайдерів
)
from backend.app.src.services.integrations.google_calendar_service import GoogleCalendarService
from backend.app.src.services.integrations.outlook_calendar_service import OutlookCalendarService
# TODO: Додати сервіс для UserIntegrationCredential для зберігання токенів
# from backend.app.src.services.integrations.user_integration_credential_service import UserIntegrationCredentialService
from backend.app.src.services.dictionaries.calendars import CalendarProviderService  # Для отримання списку провайдерів
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings as global_settings

router = APIRouter()


# --- Залежності для сервісів ---
async def get_google_calendar_service(session: AsyncSession = Depends(get_api_db_session)) -> GoogleCalendarService:
    """Залежність для GoogleCalendarService."""
    return GoogleCalendarService(db_session=session)


async def get_outlook_calendar_service(session: AsyncSession = Depends(get_api_db_session)) -> OutlookCalendarService:
    """Залежність для OutlookCalendarService."""
    return OutlookCalendarService(db_session=session)


async def get_calendar_provider_dict_service(
        session: AsyncSession = Depends(get_api_db_session)) -> CalendarProviderService:
    """Залежність для CalendarProviderService (довідник)."""
    return CalendarProviderService(db_session=session)


# --- Ендпоінти для управління підключеннями календарів користувача ---

@router.get(
    "/user/providers",
    response_model=List[CalendarProviderResponse],
    summary="Список доступних провайдерів календарів",  # i18n
    description="Повертає список усіх доступних для інтеграції провайдерів календарів, які налаштовані в системі."
    # i18n
)
async def list_available_calendar_providers(
        provider_service: CalendarProviderService = Depends(get_calendar_provider_dict_service)
) -> List[CalendarProviderResponse]:
    """Отримує список всіх доступних провайдерів календарів з довідника."""
    # TODO: Додати пагінацію, якщо список може бути великим (малоймовірно для провайдерів)
    return await provider_service.get_all(limit=100)  # Припускаємо, що get_all повертає Pydantic схеми


@router.get(
    "/user/connections",
    response_model=List[UserCalendarConnectionResponse],  # Список підключень користувача
    summary="Перегляд активних інтеграцій з календарями користувача",  # i18n
    description="Повертає список поточних активних інтеграцій з календарями для аутентифікованого користувача."  # i18n
)
async def get_user_calendar_connections(
        current_user: UserModel = Depends(get_current_active_user),
        # TODO: Потрібен сервіс для отримання UserIntegration записів (або подібних)
        # user_integration_credential_service: UserIntegrationCredentialService = Depends(...)
) -> List[UserCalendarConnectionResponse]:
    """
    Отримує список активних підключень до календарів для поточного користувача.
    Має звертатися до сервісу, що керує збереженими токенами/даними інтеграцій.
    """
    logger.info(f"Користувач ID '{current_user.id}' запитує свої активні календарні підключення.")
    # TODO: Реалізувати логіку отримання активних підключень з UserIntegrationCredentialService
    #  Для кожного підключення, повернути дані у форматі UserCalendarConnectionResponse.
    #  Приклад:
    #  active_connections = await user_integration_credential_service.get_active_connections_for_user(
    #      user_id=current_user.id, service_type_filter="CALENDAR"
    #  )
    #  return active_connections
    logger.warning("[ЗАГЛУШКА] Повернення мок-даних для активних підключень календарів.")
    return [
        UserCalendarConnectionResponse(provider_name="GOOGLE_CALENDAR",
                                       account_identifier=f"{current_user.email or current_user.username}-google",
                                       connected_at=datetime.now(timezone.utc)),
        # UserCalendarConnectionResponse(provider_name="OUTLOOK_CALENDAR", account_identifier="Інший Обліковий Запис", connected_at=datetime.now(timezone.utc) - timedelta(days=1)),
    ]


@router.get(
    "/{provider_code}/connect",  # Наприклад, /integrations/calendars/GOOGLE_CALENDAR/connect
    summary="Ініціалізація OAuth2 підключення до календаря",  # i18n
    description="Перенаправляє користувача на сторінку авторизації провайдера календаря для надання доступу.",  # i18n
    status_code=status.HTTP_307_TEMPORARY_REDIRECT
)
async def initiate_calendar_connection(
        provider_code: str = Path(...,
                                  description="Код провайдера календаря (наприклад, 'GOOGLE_CALENDAR', 'OUTLOOK_CALENDAR')"),
        # i18n
        request: FastAPIRequest,  # Потрібен для генерації redirect_uri
        current_user: UserModel = Depends(get_current_active_user),
        google_service: GoogleCalendarService = Depends(get_google_calendar_service),
        outlook_service: OutlookCalendarService = Depends(get_outlook_calendar_service)
):
    """
    Ініціює потік OAuth2 для підключення до календаря.
    Генерує URL авторизації та перенаправляє користувача.
    """
    logger.info(f"Користувач ID '{current_user.id}' ініціює підключення до календаря: {provider_code}.")

    # TODO: Зберігати state параметр в сесії користувача або кеші для перевірки в callback.
    # state = str(uuid4())
    # request.session['oauth_state'] = state # Якщо використовується сесія FastAPI/Starlette

    # TODO: redirect_uri має бути динамічним або з конфігурації, і зареєстрованим у провайдера.
    #  Приклад: request.url_for('handle_calendar_callback', provider_code=provider_code)
    # redirect_uri = str(request.url_for('handle_calendar_callback', provider_code=provider_code))
    # Для заглушки, використовуємо фіксований (має бути в settings)
    redirect_uri_placeholder = f"{global_settings.APP_BASE_URL}{global_settings.API_V1_STR}/integrations/calendars/{provider_code}/callback"

    auth_url: Optional[str] = None
    if provider_code.upper() == "GOOGLE_CALENDAR":
        # TODO: GoogleCalendarService має надати метод для генерації auth_url
        # auth_url = await google_service.generate_auth_url(redirect_uri, state=state)
        logger.warning(f"[ЗАГЛУШКА] Генерація auth_url для Google Calendar. Потрібна реалізація.")
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id=YOUR_GOOGLE_CLIENT_ID&redirect_uri={redirect_uri_placeholder}&response_type=code&scope=https://www.googleapis.com/auth/calendar.events+https://www.googleapis.com/auth/calendar.readonly&access_type=offline&prompt=consent"  # i18n
    elif provider_code.upper() == "OUTLOOK_CALENDAR":
        # TODO: OutlookCalendarService має надати метод для генерації auth_url
        # auth_url = await outlook_service.generate_auth_url(redirect_uri, state=state)
        logger.warning(f"[ЗАГЛУШКА] Генерація auth_url для Outlook Calendar. Потрібна реалізація.")
        auth_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=YOUR_MICROSOFT_APP_ID&redirect_uri={redirect_uri_placeholder}&response_type=code&scope=openid+profile+offline_access+Calendars.ReadWrite&response_mode=query"  # i18n
    else:
        # i18n
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Провайдер календаря '{provider_code}' не підтримується.")

    if not auth_url:
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не вдалося згенерувати URL авторизації для {provider_code}.")

    return RedirectResponse(url=auth_url)


@router.get(
    "/{provider_code}/callback",
    summary="Обробка OAuth2 callback від провайдера календаря",  # i18n
    description="Приймає код авторизації від провайдера, обмінює його на токени та зберігає їх.",  # i18n
    response_model=UserCalendarConnectionResponse  # Або просте повідомлення про успіх/помилку
)
async def handle_calendar_callback(
        provider_code: str = Path(..., description="Код провайдера календаря"),  # i18n
        code: Optional[str] = Query(None, description="Код авторизації від провайдера"),  # i18n
        error: Optional[str] = Query(None, description="Повідомлення про помилку від провайдера"),  # i18n
        # state: Optional[str] = Query(None, description="Параметр state для перевірки CSRF"), # i18n
        request: FastAPIRequest,  # Для перевірки state з сесії
        current_user: UserModel = Depends(get_current_active_user),  # Поточний користувач, для якого зберігаємо токени
        google_service: GoogleCalendarService = Depends(get_google_calendar_service),
        outlook_service: OutlookCalendarService = Depends(get_outlook_calendar_service)
) -> UserCalendarConnectionResponse:
    """
    Обробляє OAuth2 callback. Обмінює код на токени, зберігає їх для `current_user`.
    """
    logger.info(
        f"Callback для {provider_code} отримано для користувача ID '{current_user.id}'. Code: {'так' if code else 'ні'}, Error: {error}.")

    # TODO: Перевірити параметр `state` для запобігання CSRF атакам.
    #  `expected_state = request.session.pop('oauth_state', None)`
    #  `if not state or state != expected_state: raise HTTPException(...)`

    if error:
        # i18n
        logger.error(f"Помилка від провайдера {provider_code} в callback: {error}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Помилка авторизації з {provider_code}: {error}")
    if not code:
        # i18n
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Код авторизації не надано провайдером {provider_code}.")

    # TODO: redirect_uri має бути тим самим, що використовувався для генерації auth_url.
    # redirect_uri = str(request.url_for('handle_calendar_callback', provider_code=provider_code))
    redirect_uri_placeholder = f"{global_settings.APP_BASE_URL}{global_settings.API_V1_STR}/integrations/calendars/{provider_code}/callback"

    connection_details: Optional[Dict[str, Any]] = None
    if provider_code.upper() == "GOOGLE_CALENDAR":
        connection_details = await google_service.connect_account(user_id=current_user.id, auth_code=code,
                                                                  redirect_uri=redirect_uri_placeholder)
    elif provider_code.upper() == "OUTLOOK_CALENDAR":
        connection_details = await outlook_service.connect_account(user_id=current_user.id, auth_code=code,
                                                                   redirect_uri=redirect_uri_placeholder)
    else:
        # i18n
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Провайдер календаря '{provider_code}' не підтримується для callback.")

    if not connection_details or connection_details.get("status") != "success":
        # i18n
        err_msg = connection_details.get('message') if connection_details else "Невідома помилка підключення."
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не вдалося підключити обліковий запис {provider_code}: {err_msg}")

    # i18n
    return UserCalendarConnectionResponse(
        provider_name=provider_code.upper(),
        account_identifier=connection_details.get("account_identifier", "N/A"),
        connected_at=datetime.now(timezone.utc),  # Або час з токенів, якщо є
        status_message=connection_details.get("message", "Підключення успішне.")  # i18n
    )


@router.delete(
    "/user/connections/{provider_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення/відключення інтеграції з календарем користувача",  # i18n
    description="Дозволяє користувачу видалити своє підключення до вказаного провайдера календаря."  # i18n
)
async def delete_user_calendar_connection(
        provider_code: str = Path(..., description="Код провайдера календаря для відключення"),  # i18n
        current_user: UserModel = Depends(get_current_active_user),
        google_service: GoogleCalendarService = Depends(get_google_calendar_service),
        outlook_service: OutlookCalendarService = Depends(get_outlook_calendar_service)
):
    """
    Видаляє підключення до календаря для поточного користувача.
    Сервіс має відкликати токени та видалити їх зі сховища.
    """
    logger.info(f"Користувач ID '{current_user.id}' намагається відключити календар: {provider_code}.")

    success = False
    if provider_code.upper() == "GOOGLE_CALENDAR":
        success = await google_service.disconnect_account(user_id=current_user.id)
    elif provider_code.upper() == "OUTLOOK_CALENDAR":
        success = await outlook_service.disconnect_account(user_id=current_user.id)
    else:
        # i18n
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Провайдер календаря '{provider_code}' не підтримується для відключення.")

    if not success:
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Не вдалося відключити обліковий запис {provider_code}.")

    return None  # HTTP 204 No Content


# --- Ендпоінти для конфігурації календарів на рівні групи (заглушки) ---
# TODO: Переглянути та реалізувати логіку для групових налаштувань календарів, якщо це потрібно.
#  Поточні ендпоінти є заглушками і можуть бути неактуальними або потребувати іншого підходу.

@router.post(
    "/group/{group_id}/config",
    response_model=GroupCalendarConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Налаштування інтеграції календаря для групи (Адмін групи/Суперюзер) - ЗАГЛУШКА",  # i18n
    description="Дозволяє адміністратору групи налаштувати інтеграцію з календарем для групи (ЗАГЛУШКА).",  # i18n
    deprecated=True
)
async def configure_group_calendar_integration(
        group_id: UUID = Path(..., description="ID групи"),  # i18n
        config_in: GroupCalendarConfigCreate,
        current_user: UserModel = Depends(get_current_active_superuser),  # Тимчасово, потрібна перевірка адміна групи
        # calendar_service: BaseCalendarIntegrationService = Depends(...) # Потрібен відповідний сервіс
):
    logger.warning(
        f"[ЗАГЛУШКА] Налаштування календаря для групи {group_id} не реалізовано. Дані: {config_in.model_dump_minimal()}")
    # i18n
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED,
                        detail="Функціонал налаштування календаря для групи ще не реалізовано.")


@router.get(
    "/group/{group_id}/config",
    response_model=List[GroupCalendarConfigResponse],
    summary="Перегляд інтеграцій календаря для групи (Адмін/Суперюзер/Член групи) - ЗАГЛУШКА",  # i18n
    description="Повертає список налаштувань інтеграції з календарями для вказаної групи (ЗАГЛУШКА).",  # i18n
    deprecated=True
)
async def get_group_calendar_integrations(
        group_id: UUID = Path(..., description="ID групи"),  # i18n
        current_user: UserModel = Depends(get_current_active_user),
):
    logger.warning(f"[ЗАГЛУШКА] Перегляд налаштувань календаря для групи {group_id} не реалізовано.")
    return []


logger.info(f"Роутер для інтеграцій з календарями (`{router.prefix}`) визначено.")
