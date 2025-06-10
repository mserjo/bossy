# backend/app/src/api/v1/integrations/calendars.py
from typing import List, Optional, Generic, TypeVar # Додано Generic, TypeVar для PaginatedResponse
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from pydantic import BaseModel # Додано BaseModel для PaginatedResponse, якщо визначається локально
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_user # May need get_current_active_superuser for some views
from app.src.models.auth import User as UserModel
# from app.src.models.integrations import UserCalendarConfig as UserCalendarConfigModel # Потрібні моделі
# from app.src.models.integrations import GroupCalendarConfig as GroupCalendarConfigModel
from app.src.schemas.integrations.calendar import ( # Схеми для інтеграцій з календарями
    UserCalendarConfigCreate,
    UserCalendarConfigResponse,
    GroupCalendarConfigCreate,
    GroupCalendarConfigResponse,
    # CalendarProviderResponse # Можливо, для списку доступних провайдерів
)
# Припускаємо, що ці схеми імпортуються, якщо ні - можна визначити як у users.py або groups.py
from app.src.schemas.pagination import PaginatedResponse, PageParams # Якщо потрібна пагінація для списків конфігурацій
from app.src.services.integrations.calendar import CalendarIntegrationService # Сервіс для інтеграцій

router = APIRouter()

# --- User-specific Calendar Integrations ---
@router.post(
    "/user/config", # Шлях відносно /integrations/calendars/user/config
    response_model=UserCalendarConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Налаштування користувацької інтеграції з календарем",
    description="Дозволяє користувачу налаштувати або оновити свою персональну інтеграцію з календарем (наприклад, Google Calendar, Outlook Calendar)."
)
async def configure_user_calendar_integration(
    config_in: UserCalendarConfigCreate, # Включає provider_id, можливо, токени доступу або інші налаштування
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    calendar_service: CalendarIntegrationService = Depends()
):
    '''
    Налаштовує або оновлює персональну інтеграцію календаря для поточного користувача.
    Сервіс може обробляти OAuth redirect, зберігання токенів тощо.
    '''
    if not hasattr(calendar_service, 'db_session') or calendar_service.db_session is None:
        calendar_service.db_session = db

    user_config = await calendar_service.configure_user_calendar(
        user_id=current_user.id,
        config_create_schema=config_in
    )
    # Сервіс має кидати HTTPException у разі помилок
    return UserCalendarConfigResponse.model_validate(user_config)

@router.get(
    "/user/config",
    response_model=List[UserCalendarConfigResponse], # Користувач може мати декілька конфігурацій (для різних провайдерів)
    summary="Перегляд користувацьких інтеграцій з календарями",
    description="Повертає список поточних налаштувань інтеграції з календарями для аутентифікованого користувача."
)
async def get_user_calendar_integrations(
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    calendar_service: CalendarIntegrationService = Depends()
):
    '''
    Отримує список налаштувань інтеграції з календарями для поточного користувача.
    '''
    if not hasattr(calendar_service, 'db_session') or calendar_service.db_session is None:
        calendar_service.db_session = db

    configs = await calendar_service.get_user_calendar_configs(user_id=current_user.id)
    return [UserCalendarConfigResponse.model_validate(conf) for conf in configs]

@router.delete(
    "/user/config/{config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення користувацької інтеграції з календарем",
    description="Дозволяє користувачу видалити своє налаштування інтеграції з календарем."
)
async def delete_user_calendar_integration(
    config_id: int = Path(..., description="ID налаштування інтеграції, яке видаляється"),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    calendar_service: CalendarIntegrationService = Depends()
):
    '''
    Видаляє налаштування інтеграції календаря для поточного користувача.
    Сервіс має перевірити, що конфігурація належить користувачу.
    '''
    if not hasattr(calendar_service, 'db_session') or calendar_service.db_session is None:
        calendar_service.db_session = db

    success = await calendar_service.delete_user_calendar_config(
        config_id=config_id,
        user_id=current_user.id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Налаштування інтеграції з ID {config_id} не знайдено або не належить вам."
        )
    # HTTP 204 No Content


# --- Group-specific Calendar Integrations (Conceptual) ---
# Розробка цих ендпоінтів потребує чіткого розуміння, як інтеграції календарів працюють для груп.
# Наприклад, чи це спільний календар групи, чи налаштування для сповіщень про події групи в календарі адміна.
# Нижче наведено приклади, які можуть потребувати адаптації.

@router.post(
    "/group/{group_id}/config", # Шлях відносно /integrations/calendars/group/{group_id}/config
    response_model=GroupCalendarConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Налаштування інтеграції календаря для групи (Адмін групи/Суперюзер)",
    description="Дозволяє адміністратору групи налаштувати інтеграцію з календарем для групи."
)
async def configure_group_calendar_integration(
    group_id: int = Path(..., description="ID групи"),
    config_in: GroupCalendarConfigCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Має бути адміном групи або суперюзером
    calendar_service: CalendarIntegrationService = Depends()
):
    if not hasattr(calendar_service, 'db_session') or calendar_service.db_session is None:
        calendar_service.db_session = db

    # Сервіс має перевірити права current_user на керування налаштуваннями групи group_id
    group_config = await calendar_service.configure_group_calendar(
        group_id=group_id,
        config_create_schema=config_in,
        requesting_user=current_user
    )
    return GroupCalendarConfigResponse.model_validate(group_config)

@router.get(
    "/group/{group_id}/config",
    response_model=List[GroupCalendarConfigResponse],
    summary="Перегляд інтеграцій календаря для групи (Адмін групи/Суперюзер/Член групи)",
    description="Повертає список налаштувань інтеграції з календарями для вказаної групи."
)
async def get_group_calendar_integrations(
    group_id: int = Path(..., description="ID групи"),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Член групи, адмін або суперюзер
    calendar_service: CalendarIntegrationService = Depends()
):
    if not hasattr(calendar_service, 'db_session') or calendar_service.db_session is None:
        calendar_service.db_session = db

    # Сервіс перевіряє права доступу до перегляду
    configs = await calendar_service.get_group_calendar_configs(
        group_id=group_id,
        requesting_user=current_user
    )
    return [GroupCalendarConfigResponse.model_validate(conf) for conf in configs]

@router.delete(
    "/group/{group_id}/config/{config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення інтеграції календаря для групи (Адмін групи/Суперюзер)",
    description="Дозволяє адміністратору групи видалити налаштування інтеграції з календарем для групи."
)
async def delete_group_calendar_integration(
    group_id: int = Path(..., description="ID групи"),
    config_id: int = Path(..., description="ID налаштування інтеграції, яке видаляється"),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Адмін групи або суперюзер
    calendar_service: CalendarIntegrationService = Depends()
):
    if not hasattr(calendar_service, 'db_session') or calendar_service.db_session is None:
        calendar_service.db_session = db

    success = await calendar_service.delete_group_calendar_config(
        config_id=config_id,
        group_id=group_id, # Для додаткової перевірки
        requesting_user=current_user
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Налаштування інтеграції з ID {config_id} для групи ID {group_id} не знайдено або у вас немає прав."
        )
    # HTTP 204 No Content

# Міркування:
# 1.  Схеми: `UserCalendarConfigCreate/Response`, `GroupCalendarConfigCreate/Response` з `app.src.schemas.integrations.calendar`.
# 2.  Сервіс `CalendarIntegrationService`: Керує логікою налаштування, зберігання (наприклад, OAuth токенів),
#     та видалення конфігурацій. Обробляє взаємодію з API календарів.
# 3.  Права доступу: Користувачі керують своїми персональними налаштуваннями.
#     Адміністратори груп / Суперюзери керують налаштуваннями для груп або глобальними.
# 4.  OAuth: Для багатьох календарних сервісів (Google, Outlook) потрібен OAuth2.
#     API може ініціювати потік OAuth, а окремий ендпоінт (`/callback`) оброблятиме відповідь від провайдера.
#     Ці ендпоінти (`/oauth/start`, `/oauth/callback`) можуть бути частиною цього роутера або окремого. Поки не включені.
# 5.  URL-и: Цей роутер буде підключений до `integrations_router` з префіксом `/calendars`.
#     Шляхи будуть `/api/v1/integrations/calendars/user/config`, `/api/v1/integrations/calendars/group/{group_id}/config`.
# 6.  Коментарі: Українською мовою.
