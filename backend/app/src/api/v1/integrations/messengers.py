# backend/app/src/api/v1/integrations/messengers.py
from typing import List, Optional, Generic, TypeVar # Додано Generic, TypeVar для PaginatedResponse
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from pydantic import BaseModel # Додано BaseModel для PaginatedResponse, якщо визначається локально
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_user
from app.src.models.auth import User as UserModel
# from app.src.models.integrations import UserMessengerConfig as UserMessengerConfigModel # Потрібні моделі
# from app.src.models.integrations import GroupMessengerConfig as GroupMessengerConfigModel
from app.src.schemas.integrations.messenger import ( # Схеми для інтеграцій з месенджерами
    UserMessengerConfigCreate,
    UserMessengerConfigResponse,
    GroupMessengerConfigCreate,
    GroupMessengerConfigResponse,
    # MessengerProviderResponse # Можливо, для списку доступних провайдерів
)
# Припускаємо, що ці схеми імпортуються, якщо ні - можна визначити як у users.py або groups.py
from app.src.schemas.pagination import PaginatedResponse, PageParams # Якщо потрібна пагінація
from app.src.services.integrations.messenger import MessengerIntegrationService # Сервіс для інтеграцій

router = APIRouter()

# --- User-specific Messenger Integrations ---
@router.post(
    "/user/config", # Шлях відносно /integrations/messengers/user/config
    response_model=UserMessengerConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Налаштування користувацької інтеграції з месенджером",
    description="Дозволяє користувачу налаштувати або оновити свою персональну інтеграцію з месенджером для отримання сповіщень (наприклад, Telegram, Viber)."
)
async def configure_user_messenger_integration(
    config_in: UserMessengerConfigCreate, # Включає provider_id, chat_id/contact_info, налаштування сповіщень
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    messenger_service: MessengerIntegrationService = Depends()
):
    '''
    Налаштовує або оновлює персональну інтеграцію з месенджером для поточного користувача.
    Сервіс може обробляти верифікацію (наприклад, код для Telegram бота).
    '''
    if not hasattr(messenger_service, 'db_session') or messenger_service.db_session is None:
        messenger_service.db_session = db

    user_config = await messenger_service.configure_user_messenger(
        user_id=current_user.id,
        config_create_schema=config_in
    )
    # Сервіс має кидати HTTPException у разі помилок
    return UserMessengerConfigResponse.model_validate(user_config)

@router.get(
    "/user/config",
    response_model=List[UserMessengerConfigResponse], # Користувач може мати декілька конфігурацій
    summary="Перегляд користувацьких інтеграцій з месенджерами",
    description="Повертає список поточних налаштувань інтеграції з месенджерами для аутентифікованого користувача."
)
async def get_user_messenger_integrations(
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    messenger_service: MessengerIntegrationService = Depends()
):
    '''
    Отримує список налаштувань інтеграції з месенджерами для поточного користувача.
    '''
    if not hasattr(messenger_service, 'db_session') or messenger_service.db_session is None:
        messenger_service.db_session = db

    configs = await messenger_service.get_user_messenger_configs(user_id=current_user.id)
    return [UserMessengerConfigResponse.model_validate(conf) for conf in configs]

@router.delete(
    "/user/config/{config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення користувацької інтеграції з месенджером",
    description="Дозволяє користувачу видалити своє налаштування інтеграції з месенджером."
)
async def delete_user_messenger_integration(
    config_id: int = Path(..., description="ID налаштування інтеграції, яке видаляється"),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    messenger_service: MessengerIntegrationService = Depends()
):
    '''
    Видаляє налаштування інтеграції месенджера для поточного користувача.
    Сервіс має перевірити, що конфігурація належить користувачу.
    '''
    if not hasattr(messenger_service, 'db_session') or messenger_service.db_session is None:
        messenger_service.db_session = db

    success = await messenger_service.delete_user_messenger_config(
        config_id=config_id,
        user_id=current_user.id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Налаштування інтеграції з ID {config_id} не знайдено або не належить вам."
        )
    # HTTP 204 No Content


# --- Group-specific Messenger Integrations (Conceptual) ---
@router.post(
    "/group/{group_id}/config", # Шлях відносно /integrations/messengers/group/{group_id}/config
    response_model=GroupMessengerConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Налаштування інтеграції месенджера для групи (Адмін групи/Суперюзер)",
    description="Дозволяє адміністратору групи налаштувати інтеграцію з месенджером для групових сповіщень або бота."
)
async def configure_group_messenger_integration(
    group_id: int = Path(..., description="ID групи"),
    config_in: GroupMessengerConfigCreate, # Включає provider_id, webhook_url/bot_token, channel_id
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Має бути адміном групи або суперюзером
    messenger_service: MessengerIntegrationService = Depends()
):
    if not hasattr(messenger_service, 'db_session') or messenger_service.db_session is None:
        messenger_service.db_session = db

    # Сервіс має перевірити права current_user на керування налаштуваннями групи group_id
    group_config = await messenger_service.configure_group_messenger(
        group_id=group_id,
        config_create_schema=config_in,
        requesting_user=current_user
    )
    return GroupMessengerConfigResponse.model_validate(group_config)

@router.get(
    "/group/{group_id}/config",
    response_model=List[GroupMessengerConfigResponse],
    summary="Перегляд інтеграцій месенджера для групи (Адмін групи/Суперюзер/Член групи)",
    description="Повертає список налаштувань інтеграції з месенджерами для вказаної групи."
)
async def get_group_messenger_integrations(
    group_id: int = Path(..., description="ID групи"),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Член групи, адмін або суперюзер
    messenger_service: MessengerIntegrationService = Depends()
):
    if not hasattr(messenger_service, 'db_session') or messenger_service.db_session is None:
        messenger_service.db_session = db

    # Сервіс перевіряє права доступу до перегляду
    configs = await messenger_service.get_group_messenger_configs(
        group_id=group_id,
        requesting_user=current_user
    )
    return [GroupMessengerConfigResponse.model_validate(conf) for conf in configs]

@router.delete(
    "/group/{group_id}/config/{config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення інтеграції месенджера для групи (Адмін групи/Суперюзер)",
    description="Дозволяє адміністратору групи видалити налаштування інтеграції з месенджером для групи."
)
async def delete_group_messenger_integration(
    group_id: int = Path(..., description="ID групи"),
    config_id: int = Path(..., description="ID налаштування інтеграції, яке видаляється"),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Адмін групи або суперюзер
    messenger_service: MessengerIntegrationService = Depends()
):
    if not hasattr(messenger_service, 'db_session') or messenger_service.db_session is None:
        messenger_service.db_session = db

    success = await messenger_service.delete_group_messenger_config(
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
# 1.  Схеми: `UserMessengerConfigCreate/Response`, `GroupMessengerConfigCreate/Response` з `app.src.schemas.integrations.messenger`.
# 2.  Сервіс `MessengerIntegrationService`: Керує логікою налаштування, зберігання конфігурацій (наприклад, ID чатів, токенів ботів, вебхуків).
# 3.  Права доступу: Користувачі керують своїми персональними налаштуваннями сповіщень.
#     Адміністратори груп / Суперюзери керують налаштуваннями для групових сповіщень/ботів.
# 4.  Специфіка месенджерів: Кожен месенджер (Telegram, Viber, Slack, Teams) має свої особливості інтеграції.
#     Сервіс має абстрагувати ці відмінності. API може бути більш загальним.
# 5.  URL-и: Цей роутер буде підключений до `integrations_router` з префіксом `/messengers`.
# 6.  Коментарі: Українською мовою.
