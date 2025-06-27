# backend/app/src/api/v1/integrations/trackers.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для налаштування інтеграцій з таск-трекерами API v1.

Цей модуль надає API для користувачів або адміністраторів груп для:
- Підключення/авторизації до таск-трекерів (Jira, Trello тощо).
- Перегляду статусу підключених трекерів.
- Налаштування параметрів інтеграції (наприклад, які проекти/дошки синхронізувати,
  як мапити статуси завдань).
- Відключення інтеграції з трекером.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Path, Body, Response as FastAPIResponse
from typing import List, Optional, Dict, Any

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.integrations.tracker import (
    TrackerIntegrationSchema,
    TrackerConnectionRequestSchema, # Для передачі URL, токенів тощо
    TrackerSyncSettingsSchema,
    TrackerSyncSettingsUpdateSchema
)
from backend.app.src.services.integrations.tracker_service_factory import TrackerServiceFactory
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.models.auth.user import UserModel
# Можливо, group_admin_permission, якщо налаштування інтеграції відбувається в контексті групи
# from backend.app.src.api.v1.groups.groups import group_admin_permission

logger = get_logger(__name__)
router = APIRouter()

# Префікс /trackers вже встановлено в integrations/__init__.py

@router.post(
    "/{provider}/connect",
    response_model=TrackerIntegrationSchema, # Повертає інформацію про створену інтеграцію
    status_code=status.HTTP_201_CREATED,
    tags=["Integrations", "Task Trackers"],
    summary="Підключити таск-трекер"
)
async def connect_task_tracker(
    provider: str = Path(..., description="Провайдер трекера (напр., 'jira', 'trello')"),
    connection_data: TrackerConnectionRequestSchema, # Містить URL, API токен/ключі тощо
    current_user: UserModel = Depends(CurrentActiveUser), # Інтеграції зазвичай персональні або групові
    # group_id: Optional[int] = Query(None, description="ID групи, якщо інтеграція групова"), # Для групових інтеграцій
    db_session: DBSession = Depends()
):
    """
    Налаштовує інтеграцію з вказаним таск-трекером.
    Вимагає URL інстансу та облікові дані (API токен, OAuth тощо).
    """
    logger.info(f"Користувач {current_user.email} підключає таск-трекер: {provider}.")
    # TODO: Якщо інтеграція групова, потрібна перевірка прав group_admin_permission
    # if group_id:
    #     admin_check = await group_admin_permission(group_id, current_user, db_session) # Приклад
    #     # current_user = admin_check["current_user"] # Оновлюємо, якщо залежність повертає його

    try:
        tracker_service = TrackerServiceFactory.get_service(
            provider,
            db_session=db_session,
            user_id=current_user.id,
            # group_id=group_id # Якщо інтеграція на рівні групи
        )
        # Сервіс має валідувати дані підключення та зберегти інтеграцію
        integration_info = await tracker_service.connect(connection_data=connection_data)
        return integration_info
    except ValueError as ve: # Наприклад, непідтримуваний провайдер або невірні дані
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Помилка підключення до трекера {provider} для {current_user.email}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")


@router.get(
    "",
    response_model=List[TrackerIntegrationSchema],
    tags=["Integrations", "Task Trackers"],
    summary="Отримати список підключених таск-трекер інтеграцій"
)
async def list_my_tracker_integrations(
    current_user: UserModel = Depends(CurrentActiveUser),
    # group_id: Optional[int] = Query(None, description="ID групи, якщо інтеграції групові"),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} запитує список своїх таск-трекер інтеграцій.")
    # TODO: Реалізувати отримання списку через TrackerServiceFactory або UserIntegrationService
    # integrations = await TrackerServiceFactory.get_user_tracker_integrations(user_id=current_user.id, group_id=group_id, db_session=db_session)
    # return integrations
    # Заглушка:
    return [
        TrackerIntegrationSchema(id=1, user_id=current_user.id, provider_name="jira", account_identifier="mycompany.atlassian.net", is_active=True, group_id=None),
    ]

@router.get(
    "/{integration_id}/settings",
    response_model=TrackerSyncSettingsSchema,
    tags=["Integrations", "Task Trackers"],
    summary="Отримати налаштування синхронізації для таск-трекера"
)
async def get_tracker_integration_settings(
    integration_id: int,
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} запитує налаштування для трекер-інтеграції ID {integration_id}.")
    # TODO: Сервіс має знайти інтеграцію, перевірити власника/доступ, повернути налаштування
    # tracker_service = TrackerServiceFactory.get_service_by_integration_id(integration_id, db_session, user_id=current_user.id)
    # settings = await tracker_service.get_sync_settings()
    # if not settings:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Налаштування не знайдено.")
    # return settings
    return TrackerSyncSettingsSchema(
        integration_id=integration_id,
        projects_to_sync=["PROJ1", "PROJ2"],
        sync_task_statuses={"Open": "created", "In Progress": "in_progress"},
        default_task_type_id_on_import=1
    )

@router.put(
    "/{integration_id}/settings",
    response_model=TrackerSyncSettingsSchema,
    tags=["Integrations", "Task Trackers"],
    summary="Оновити налаштування синхронізації для таск-трекера"
)
async def update_my_tracker_integration_settings(
    integration_id: int,
    settings_in: TrackerSyncSettingsUpdateSchema,
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} оновлює налаштування для трекер-інтеграції ID {integration_id}.")
    # TODO: Сервіс має знайти інтеграцію, перевірити власника/доступ, оновити налаштування.
    # tracker_service = TrackerServiceFactory.get_service_by_integration_id(integration_id, db_session, user_id=current_user.id)
    # updated_settings = await tracker_service.update_sync_settings(settings_in)
    # if not updated_settings:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Не вдалося оновити налаштування.")
    # return updated_settings
    updated_data = settings_in.model_dump(exclude_unset=True)
    return TrackerSyncSettingsSchema(integration_id=integration_id, **updated_data)


@router.delete(
    "/{integration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Integrations", "Task Trackers"],
    summary="Відключити таск-трекер інтеграцію"
)
async def disconnect_my_tracker_integration(
    integration_id: int,
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} відключає трекер-інтеграцію ID {integration_id}.")
    # TODO: Сервіс має знайти інтеграцію, перевірити власника/доступ, видалити дані інтеграції.
    # tracker_service = TrackerServiceFactory.get_service_by_integration_id(integration_id, db_session, user_id=current_user.id)
    # success = await tracker_service.disconnect()
    # if not success:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Інтеграцію не знайдено або не вдалося відключити.")
    return FastAPIResponse(status_code=status.HTTP_204_NO_CONTENT)

# Роутер буде підключений в backend/app/src/api/v1/integrations/__init__.py
# з префіксом /trackers
