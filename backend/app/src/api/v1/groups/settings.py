# backend/app/src/api/v1/groups/settings.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_user
from app.src.models.auth import User as UserModel
# from app.src.models.groups import GroupSetting as GroupSettingModel # Якщо є окрема модель
from app.src.schemas.groups.settings import ( # Схеми для налаштувань групи
    GroupSettingResponse,
    GroupSettingUpdate
)
from app.src.services.groups.settings import GroupSettingService # Сервіс для налаштувань групи
# from app.src.core.permissions import GroupPermissionsChecker # Для перевірки прав

router = APIRouter()

@router.get(
    "/{group_id}/settings",
    response_model=GroupSettingResponse,
    summary="Отримання налаштувань групи",
    description="Повертає налаштування для вказаної групи. Доступно адміністраторам групи або суперюзерам."
)
async def get_group_settings(
    group_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    settings_service: GroupSettingService = Depends()
):
    '''
    Отримує налаштування групи.
    Необхідна перевірка, чи є поточний користувач адміністратором цієї групи або суперюзером.
    '''
    if not hasattr(settings_service, 'db_session') or settings_service.db_session is None:
        settings_service.db_session = db
    # if not hasattr(settings_service, 'current_user') or settings_service.current_user is None:
    #     settings_service.current_user = current_user # Якщо сервіс потребує

    # Перевірка прав доступу (має бути в сервісі або через GroupPermissionsChecker)
    # await GroupPermissionsChecker(db).check_user_can_manage_group_settings(user=current_user, group_id=group_id)

    group_settings = await settings_service.get_settings_by_group_id(
        group_id=group_id,
        requesting_user=current_user
    )
    if not group_settings:
        # Це може означати, що група не існує, налаштування не створені, або доступ заборонено.
        # Сервіс має обробляти це відповідно.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Налаштування для групи з ID {group_id} не знайдено або доступ заборонено."
        )
    return GroupSettingResponse.model_validate(group_settings)

@router.put(
    "/{group_id}/settings",
    response_model=GroupSettingResponse,
    summary="Оновлення налаштувань групи",
    description="Дозволяє адміністраторам групи або суперюзерам оновити налаштування групи."
)
async def update_group_settings(
    group_id: int,
    settings_in: GroupSettingUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    settings_service: GroupSettingService = Depends()
):
    '''
    Оновлює налаштування групи.
    Необхідна перевірка, чи є поточний користувач адміністратором цієї групи або суперюзером.
    '''
    if not hasattr(settings_service, 'db_session') or settings_service.db_session is None:
        settings_service.db_session = db
    # if not hasattr(settings_service, 'current_user') or settings_service.current_user is None:
    #     settings_service.current_user = current_user

    # Перевірка прав доступу
    # await GroupPermissionsChecker(db).check_user_can_manage_group_settings(user=current_user, group_id=group_id)

    updated_settings = await settings_service.update_settings_by_group_id(
        group_id=group_id,
        settings_update_schema=settings_in,
        requesting_user=current_user
    )
    if not updated_settings:
        # Сервіс має обробляти це відповідно (не знайдено, заборонено, помилка валідації).
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # Або 403, 400
            detail=f"Не вдалося оновити налаштування для групи з ID {group_id}. Групу не знайдено, доступ заборонено або дані невалідні."
        )
    return GroupSettingResponse.model_validate(updated_settings)

# Міркування:
# 1.  Структура URL: Ендпоінти використовують `/{group_id}/settings`. Це означає, що цей роутер (`settings_router`)
#     має бути підключений до `groups_router` (в `groups/__init__.py`) без додаткового префіксу,
#     але `groups_router` буде підключений до `v1_router` з префіксом `/groups`.
#     Таким чином, повний шлях буде `/api/v1/groups/{group_id}/settings`.
# 2.  Схеми: `GroupSettingResponse`, `GroupSettingUpdate` мають бути визначені в `app.src.schemas.groups.settings`.
# 3.  Сервіс `GroupSettingService`: Відповідає за логіку отримання та оновлення налаштувань групи,
#     включаючи перевірку прав (чи є користувач адміном групи або суперюзером).
#     Методи: `get_settings_by_group_id`, `update_settings_by_group_id`.
# 4.  Модель `GroupSettingModel`: Налаштування групи можуть зберігатися в окремій таблиці/моделі,
#     пов'язаній з моделлю `Group`, або як JSONB поле в самій моделі `Group`.
#     `GroupSettingService` абстрагує цю деталь реалізації.
# 5.  Права доступу: Тільки адміністратори відповідної групи або суперюзери системи можуть керувати налаштуваннями.
#     Ця логіка має бути реалізована в `GroupSettingService`.
# 6.  Коментарі: Українською мовою.
# 7.  Залежності: `get_current_active_user` для ідентифікації користувача, що робить запит.
#     `GroupSettingService = Depends()` для ін'єкції сервісу.
