# backend/app/src/api/v1/notifications/delivery.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для перегляду статусів доставки сповіщень API v1 (адміністративні).

Цей модуль надає API для адміністраторів системи для:
- Перегляду логів/статусів доставки конкретних сповіщень.
- Можливо, для повторної спроби надсилання сповіщень, що не були доставлені.
- Фільтрації логів доставки за різними критеріями (користувач, тип, статус).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import List, Optional

from backend.app.src.config.logging import get_logger
from backend.app.src.schemas.notifications.delivery import NotificationDeliveryAttemptSchema
from backend.app.src.services.notifications.notification_delivery_service import NotificationDeliveryService
from backend.app.src.api.dependencies import DBSession, CurrentSuperuser
from backend.app.src.models.auth.user import UserModel
from backend.app.src.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE


logger = get_logger(__name__)
router = APIRouter()

# Префікс /delivery-status вже встановлено в notifications/__init__.py

@router.get(
    "",
    response_model=List[NotificationDeliveryAttemptSchema], # Або схема з пагінацією
    tags=["Notifications", "Notification Delivery (Admin)"],
    summary="Отримати лог статусів доставки сповіщень (суперкористувач)"
)
async def list_all_notification_delivery_statuses(
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser),
    page: int = Query(DEFAULT_PAGE, ge=1, description="Номер сторінки"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100, description="Розмір сторінки"),
    user_id_filter: Optional[int] = Query(None, description="Фільтр за ID користувача"),
    notification_id_filter: Optional[int] = Query(None, description="Фільтр за ID сповіщення"),
    channel_filter: Optional[str] = Query(None, description="Фільтр за каналом доставки (напр., 'email', 'sms')"),
    status_filter: Optional[str] = Query(None, description="Фільтр за статусом доставки (напр., 'sent', 'failed', 'pending')")
):
    logger.info(f"Суперкористувач {current_user.email} запитує лог статусів доставки сповіщень.")
    service = NotificationDeliveryService(db_session)

    attempts_data = await service.get_all_delivery_attempts(
        skip=(page - 1) * page_size,
        limit=page_size,
        user_id=user_id_filter,
        notification_id=notification_id_filter,
        channel=channel_filter,
        status=status_filter
    )
    # Припускаємо, сервіс повертає {"attempts": [], "total": 0}
    # TODO: Додати обробку пагінації та заголовків у відповідь
    if isinstance(attempts_data, dict):
        return attempts_data.get("attempts", [])
    return attempts_data # Якщо повертає просто список


@router.get(
    "/{attempt_id}",
    response_model=NotificationDeliveryAttemptSchema,
    tags=["Notifications", "Notification Delivery (Admin)"],
    summary="Отримати деталі конкретної спроби доставки (суперкористувач)"
)
async def get_delivery_attempt_details_endpoint(
    attempt_id: int = Path(..., description="ID спроби доставки"), # Змінено на int
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    logger.info(f"Суперкористувач {current_user.email} запитує деталі спроби доставки ID: {attempt_id}.")
    service = NotificationDeliveryService(db_session)
    attempt = await service.get_delivery_attempt_by_id(attempt_id=attempt_id)
    if not attempt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Спроба доставки не знайдена.")
    return attempt

@router.post(
    "/{attempt_id}/retry",
    response_model=NotificationDeliveryAttemptSchema, # Повертає оновлений або новий запис спроби
    tags=["Notifications", "Notification Delivery (Admin)"],
    summary="Повторити спробу надсилання сповіщення (суперкористувач)"
)
async def retry_failed_notification_delivery(
    attempt_id: int = Path(..., description="ID невдалої спроби доставки"),
    db_session: DBSession = Depends(),
    current_user: UserModel = Depends(CurrentSuperuser)
):
    logger.info(f"Суперкористувач {current_user.email} запитує повторне надсилання для спроби доставки ID: {attempt_id}.")
    service = NotificationDeliveryService(db_session)
    try:
        # Сервіс має знайти оригінальне сповіщення та спробувати надіслати його знову,
        # створивши новий запис NotificationDeliveryAttempt або оновивши існуючий.
        retried_attempt = await service.retry_delivery_attempt(attempt_id=attempt_id, actor_id=current_user.id)
        if not retried_attempt: # Якщо оригінальна спроба не знайдена або не може бути повторена
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Невдалося знайти або повторити спробу доставки.")
        return retried_attempt
    except HTTPException as e:
        raise e
    except ValueError as ve: # Наприклад, якщо сповіщення вже було успішно доставлене
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e_gen:
        logger.error(f"Помилка повторного надсилання сповіщення для спроби ID {attempt_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")


# Роутер буде підключений в backend/app/src/api/v1/notifications/__init__.py
# з префіксом /delivery-status
