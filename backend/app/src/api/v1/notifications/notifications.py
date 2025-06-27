# backend/app/src/api/v1/notifications/notifications.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління сповіщеннями користувача та його налаштуваннями API v1.

Цей модуль надає API для користувачів для:
- Отримання списку своїх сповіщень (непрочитані, всі, з пагінацією).
- Позначення одного або декількох сповіщень як прочитаних.
- Отримання своїх персональних налаштувань сповіщень.
- Оновлення своїх персональних налаштувань сповіщень.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body, Response
from typing import List, Optional, Dict, Any

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.notifications.notification import (
    NotificationSchema,
    NotificationSettingsSchema,
    NotificationSettingsUpdateSchema,
    MarkNotificationsAsReadSchema
)
from backend.app.src.services.notifications.notification_service import NotificationService
# Припускаємо, що є окремий сервіс для налаштувань сповіщень користувача
# from backend.app.src.services.notifications.user_notification_settings_service import UserNotificationSettingsService
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.models.auth.user import UserModel
from backend.app.src.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE

logger = get_logger(__name__)
router = APIRouter()

# Тимчасова заглушка для UserNotificationSettingsService
class UserNotificationSettingsService:
    def __init__(self, db_session: DBSession):
        self.db_session = db_session
        self._settings_db: Dict[int, NotificationSettingsSchema] = {} # user_id -> settings

    async def get_user_notification_settings(self, user_id: int) -> NotificationSettingsSchema:
        logger.info(f"Отримання налаштувань сповіщень для user_id {user_id} (заглушка).")
        if user_id not in self._settings_db:
            # Повертаємо дефолтні налаштування
            default_settings = NotificationSettingsSchema(
                user_id=user_id,
                email_notifications_enabled=True,
                in_app_notifications_enabled=True,
                task_completed_notify=True,
                new_task_in_group_notify=False,
                # ... інші дефолтні налаштування
            )
            self._settings_db[user_id] = default_settings
            return default_settings
        return self._settings_db[user_id]

    async def update_user_notification_settings(
        self, user_id: int, settings_in: NotificationSettingsUpdateSchema
    ) -> NotificationSettingsSchema:
        logger.info(f"Оновлення налаштувань сповіщень для user_id {user_id} (заглушка).")
        current_settings = await self.get_user_notification_settings(user_id)
        update_data = settings_in.model_dump(exclude_unset=True)
        updated_settings = current_settings.model_copy(update=update_data)
        self._settings_db[user_id] = updated_settings
        return updated_settings

# Ендпоінти будуть мати префікс /notifications (глобально для користувача)

@router.get(
    "/me", # Тобто /notifications/me
    response_model=List[NotificationSchema], # Або схема з пагінацією
    tags=["Notifications"],
    summary="Отримати список моїх сповіщень"
)
async def get_my_notifications(
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends(),
    page: int = Query(DEFAULT_PAGE, ge=1, description="Номер сторінки"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100, description="Розмір сторінки"),
    unread_only: bool = Query(False, description="Показати лише непрочитані сповіщення")
):
    """
    Повертає список сповіщень для поточного користувача з пагінацією.
    Можна фільтрувати за непрочитаними.
    """
    logger.info(
        f"Користувач {current_user.email} запитує свої сповіщення "
        f"(сторінка: {page}, розмір: {page_size}, непрочитані: {unread_only})."
    )
    service = NotificationService(db_session)
    notifications_data = await service.get_notifications_for_user(
        user_id=current_user.id,
        skip=(page-1)*page_size,
        limit=page_size,
        unread_only=unread_only
    )
    if isinstance(notifications_data, dict):
        notifications = notifications_data.get("notifications", [])
        # total = notifications_data.get("total", 0) # Для заголовків пагінації
    else:
        notifications = notifications_data

    return notifications

@router.post(
    "/me/mark-as-read", # Тобто /notifications/me/mark-as-read
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Notifications"],
    summary="Позначити сповіщення як прочитані"
)
async def mark_my_notifications_as_read(
    mark_in: MarkNotificationsAsReadSchema, # Схема з notification_ids або mark_all=True
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    """
    Позначає вказані сповіщення (за їх ID) або всі непрочитані сповіщення
    поточного користувача як прочитані.
    """
    logger.info(
        f"Користувач {current_user.email} позначає сповіщення як прочитані. "
        f"IDs: {mark_in.notification_ids}, Mark all: {mark_in.mark_all}."
    )
    service = NotificationService(db_session)

    if mark_in.mark_all:
        await service.mark_all_user_notifications_as_read(user_id=current_user.id)
        logger.info(f"Всі сповіщення для користувача {current_user.email} позначено як прочитані.")
    elif mark_in.notification_ids:
        await service.mark_notifications_as_read_by_ids(
            user_id=current_user.id, # Для перевірки, що сповіщення належать користувачу
            notification_ids=mark_in.notification_ids
        )
        logger.info(f"Сповіщення {mark_in.notification_ids} для {current_user.email} позначено як прочитані.")
    else:
        # Нічого не передано для позначення
        logger.info(f"Немає сповіщень для позначення як прочитаних для {current_user.email}.")
        pass # Або повернути помилку 400, якщо це вважається невалідним запитом

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/me/settings", # Тобто /notifications/me/settings
    response_model=NotificationSettingsSchema,
    tags=["Notifications", "Notification Settings"],
    summary="Отримати мої налаштування сповіщень"
)
async def get_my_notification_settings(
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    """
    Повертає поточні персональні налаштування сповіщень для користувача.
    """
    logger.info(f"Користувач {current_user.email} запитує свої налаштування сповіщень.")
    settings_service = UserNotificationSettingsService(db_session) # Використовуємо тимчасову заглушку
    settings = await settings_service.get_user_notification_settings(user_id=current_user.id)
    return settings

@router.put(
    "/me/settings",
    response_model=NotificationSettingsSchema,
    tags=["Notifications", "Notification Settings"],
    summary="Оновити мої налаштування сповіщень"
)
async def update_my_notification_settings(
    settings_in: NotificationSettingsUpdateSchema,
    current_user: UserModel = Depends(CurrentActiveUser),
    db_session: DBSession = Depends()
):
    """
    Оновлює персональні налаштування сповіщень для поточного користувача.
    """
    logger.info(f"Користувач {current_user.email} оновлює свої налаштування сповіщень.")
    settings_service = UserNotificationSettingsService(db_session) # Використовуємо тимчасову заглушку
    updated_settings = await settings_service.update_user_notification_settings(
        user_id=current_user.id,
        settings_in=settings_in
    )
    logger.info(f"Налаштування сповіщень для {current_user.email} оновлено.")
    return updated_settings

# Роутер буде підключений в backend/app/src/api/v1/notifications/__init__.py
