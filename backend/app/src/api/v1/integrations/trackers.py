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

from fastapi import APIRouter, Depends, status
from typing import List, Dict, Any

from backend.app.src.config.logging import get_logger
# TODO: Імпортувати схеми для налаштувань інтеграції з трекерами
# from backend.app.src.schemas.integrations.tracker import TrackerIntegrationSchema, TrackerSyncSettingsSchema
# TODO: Імпортувати сервіс(и) для інтеграції з трекерами
# from backend.app.src.services.integrations.jira_tracker_service import JiraTrackerService
# TODO: Імпортувати залежності (DBSession, CurrentActiveUser, можливо, group_admin_permission)

logger = get_logger(__name__)
router = APIRouter()

# Ендпоінти можуть бути префіксовані як /integrations/trackers
# або /users/me/integrations/trackers (якщо персональні)
# або /groups/{group_id}/integrations/trackers (якщо налаштування на рівні групи)

@router.post(
    "/jira/connect", # Приклад для Jira
    # response_model=TrackerIntegrationSchema,
    status_code=status.HTTP_200_OK,
    tags=["Integrations", "Task Trackers"],
    summary="Підключити Jira (заглушка)"
)
async def connect_jira_tracker(
    # current_user: UserModel = Depends(CurrentActiveUser),
    # db_session: DBSession = Depends(),
    # jira_url: str = Body(...),
    # api_token: str = Body(...) # Або інші методи автентифікації
):
    """
    Налаштовує інтеграцію з Jira.
    Вимагає URL інстансу Jira та облікові дані (API токен або OAuth).
    """
    logger.info(f"Користувач (ID TODO) підключає Jira (заглушка).")
    # TODO: Реалізувати логіку підключення та валідації облікових даних Jira.
    return {"message": "Інтеграція з Jira налаштовується (заглушка).", "integration_id": "jira_conn_789"}

@router.get(
    "",
    # response_model=List[TrackerIntegrationSchema],
    tags=["Integrations", "Task Trackers"],
    summary="Отримати список підключених таск-трекер інтеграцій (заглушка)"
)
async def list_tracker_integrations(
    # current_user: UserModel = Depends(CurrentActiveUser), # Або group_id, якщо налаштування групові
    # db_session: DBSession = Depends()
):
    logger.info(f"Запит списку інтеграцій з таск-трекерами (заглушка).")
    # TODO: Реалізувати отримання списку підключених трекерів
    return [
        {"id": "jira_conn_789", "provider": "jira", "status": "active", "details": "URL: mycompany.atlassian.net"},
        {"id": "trello_conn_123", "provider": "trello", "status": "error", "details": "Invalid API key"}
    ]

@router.put(
    "/{integration_id}/settings",
    # response_model=TrackerSyncSettingsSchema,
    tags=["Integrations", "Task Trackers"],
    summary="Оновити налаштування синхронізації для таск-трекера (заглушка)"
)
async def update_tracker_sync_settings(
    integration_id: str,
    # settings_data: TrackerSyncSettingsUpdateSchema,
    # current_user: UserModel = Depends(CurrentActiveUser), # Або адмін групи
    # db_session: DBSession = Depends()
):
    logger.info(f"Оновлення налаштувань для таск-трекер інтеграції ID {integration_id} (заглушка).")
    # TODO: Реалізувати логіку оновлення налаштувань синхронізації
    return {"integration_id": integration_id, "settings": {"project_key": "PROJ", "sync_statuses": ["Open", "In Progress"]}, "message": "Налаштування оновлено."}

@router.delete(
    "/{integration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Integrations", "Task Trackers"],
    summary="Відключити таск-трекер інтеграцію (заглушка)"
)
async def disconnect_tracker_integration(
    integration_id: str,
    # current_user: UserModel = Depends(CurrentActiveUser), # Або адмін групи
    # db_session: DBSession = Depends()
):
    logger.info(f"Відключення таск-трекер інтеграції ID {integration_id} (заглушка).")
    # TODO: Реалізувати логіку відключення
    return

# Роутер буде підключений в backend/app/src/api/v1/integrations/__init__.py
