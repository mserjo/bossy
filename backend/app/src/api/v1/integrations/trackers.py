# backend/app/src/api/v1/integrations/trackers.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для налаштування інтеграцій з таск-трекерами API v1.

Цей модуль надає API для користувачів або адміністраторів груп для:
- Підключення/авторизації до таск-трекерів (Jira, Trello тощо).
- Перегляду статусу підключених трекерів.
- Отримання списку доступних проектів/дощок, статусів, типів завдань з трекера.
- Налаштування параметрів інтеграції (наприклад, які проекти/дошки синхронізувати,
  як мапити статуси завдань).
- Відключення інтеграції з трекером.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query, Body, Response as FastAPIResponse
from typing import List, Optional, Dict, Any

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.integrations.tracker import (
    TrackerIntegrationSchema,
    TrackerConnectionRequestSchema,
    TrackerSyncSettingsSchema,
    TrackerSyncSettingsUpdateSchema,
    ExternalProjectSchema,      # Нова схема
    ExternalTaskStatusSchema,   # Нова схема
    ExternalTaskTypeSchema      # Нова схема
)
from backend.app.src.services.integrations.tracker_service_factory import TrackerServiceFactory
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.models.auth.user import UserModel

logger = get_logger(__name__)
router = APIRouter()

# Префікс /trackers вже встановлено в integrations/__init__.py

@router.post(
    "/{provider}/connect",
    response_model=TrackerIntegrationSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Integrations", "Task Trackers"],
    summary="Підключити таск-трекер"
)
async def connect_task_tracker(
    connection_data: TrackerConnectionRequestSchema,
    provider: str = Path(..., description="Провайдер трекера (напр., 'jira', 'trello')"),
    current_user: UserModel = Depends(CurrentActiveUser),
    # group_id: Optional[int] = Query(None, description="ID групи, якщо інтеграція групова"),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} підключає таск-трекер: {provider}.")
    # TODO: Обробка group_id, якщо інтеграція на рівні групи + перевірка прав адміна групи
    try:
        tracker_service = TrackerServiceFactory.get_service(provider, db_session=db_session, user_id=current_user.id)
        integration_info = await tracker_service.connect(connection_data=connection_data)
        return integration_info
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Помилка підключення до трекера {provider} для {current_user.email}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Помилка сервера при підключенні до {provider}.")

# TODO: Додати ендпоінт /{provider}/callback, якщо якийсь трекер використовує OAuth2.

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
    # integrations = await TrackerServiceFactory.get_user_tracker_integrations(user_id=current_user.id, group_id=group_id, db_session=db_session)
    # return integrations
    return [
        TrackerIntegrationSchema(id=1, user_id=current_user.id, provider_name="jira", account_identifier="mycompany.atlassian.net", is_active=True, group_id=None, sync_enabled=False),
    ] # Заглушка

@router.get(
    "/{integration_id}/external-projects",
    response_model=List[ExternalProjectSchema],
    tags=["Integrations", "Task Trackers"],
    summary="Отримати список доступних проектів/дощок з трекера"
)
async def get_external_projects(
    integration_id: int = Path(..., description="ID інтеграції трекера"),
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} запитує проекти для інтеграції трекера ID {integration_id}.")
    # tracker_service = TrackerServiceFactory.get_service_by_integration_id(integration_id, db_session, user_id=current_user.id)
    # projects = await tracker_service.list_available_projects()
    # return projects
    return [{"id": "PROJ1", "name": "Project Alpha"}, {"id": "BOARD2", "name": "Kanban Board Beta"}] # Заглушка

@router.get(
    "/{integration_id}/external-statuses",
    response_model=List[ExternalTaskStatusSchema],
    tags=["Integrations", "Task Trackers"],
    summary="Отримати список доступних статусів завдань з трекера"
)
async def get_external_task_statuses(
    integration_id: int = Path(..., description="ID інтеграції трекера"),
    project_id: Optional[str] = Query(None, description="ID проекту/дошки в трекері, для якого потрібні статуси"),
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} запитує статуси для інтеграції трекера ID {integration_id}, проект: {project_id}.")
    # tracker_service = TrackerServiceFactory.get_service_by_integration_id(integration_id, db_session, user_id=current_user.id)
    # statuses = await tracker_service.list_available_statuses(project_id=project_id)
    # return statuses
    return [{"id": "10000", "name": "To Do"}, {"id": "10001", "name": "In Progress"}, {"id": "10002", "name": "Done"}] # Заглушка

@router.get(
    "/{integration_id}/external-task-types",
    response_model=List[ExternalTaskTypeSchema],
    tags=["Integrations", "Task Trackers"],
    summary="Отримати список доступних типів завдань з трекера"
)
async def get_external_task_types(
    integration_id: int = Path(..., description="ID інтеграції трекера"),
    project_id: Optional[str] = Query(None, description="ID проекту/дошки в трекері, для якого потрібні типи завдань"),
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    logger.info(f"Користувач {current_user.email} запитує типи завдань для інтеграції трекера ID {integration_id}, проект: {project_id}.")
    # tracker_service = TrackerServiceFactory.get_service_by_integration_id(integration_id, db_session, user_id=current_user.id)
    # task_types = await tracker_service.list_available_task_types(project_id=project_id)
    # return task_types
    return [{"id": "10100", "name": "Task"}, {"id": "10101", "name": "Bug"}, {"id": "10102", "name": "Story"}] # Заглушка


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
    # tracker_service = TrackerServiceFactory.get_service_by_integration_id(integration_id, db_session, user_id=current_user.id)
    # settings = await tracker_service.get_sync_settings()
    # if not settings:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Налаштування не знайдено.")
    # return settings
    return TrackerSyncSettingsSchema(
        integration_id=integration_id,
        sync_enabled=True,
        projects_to_sync=["PROJ1"],
        task_status_mapping={"Open": "created", "In Progress": "in_progress", "Done":"completed"},
        task_type_mapping={"Task": 1, "Bug": 2}, # Припускаючи, що 1, 2 - ID наших TaskType
        default_assignee_id_in_bossy=current_user.id,
        sync_direction="bidirectional"
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
    # tracker_service = TrackerServiceFactory.get_service_by_integration_id(integration_id, db_session, user_id=current_user.id)
    # updated_settings = await tracker_service.update_sync_settings(settings_in)
    # if not updated_settings:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Не вдалося оновити налаштування.")
    # return updated_settings
    updated_data = settings_in.model_dump(exclude_unset=True)
    # Заглушка: повертаємо оновлені дані як частину повної схеми
    current_settings_stub = TrackerSyncSettingsSchema(
        integration_id=integration_id, sync_enabled=True, projects_to_sync=[],
        task_status_mapping={}, task_type_mapping={}, sync_direction="disabled"
    )
    # Оновлюємо поля з settings_in
    final_settings_data = current_settings_stub.model_dump()
    final_settings_data.update(updated_data)
    return TrackerSyncSettingsSchema(**final_settings_data)


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
    # tracker_service = TrackerServiceFactory.get_service_by_integration_id(integration_id, db_session, user_id=current_user.id)
    # success = await tracker_service.disconnect()
    # if not success:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Інтеграцію не знайдено або не вдалося відключити.")
    return FastAPIResponse(status_code=status.HTTP_204_NO_CONTENT)
