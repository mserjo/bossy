# backend/app/src/api/v1/notifications/delivery.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для перегляду інформації про спроби доставки сповіщень.

Ці ендпоінти зазвичай призначені для адміністраторів або суперкористувачів
з метою моніторингу та діагностики системи сповіщень.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from typing import List # Optional видалено, оскільки не використовується в активному коді
from uuid import UUID  # ID тепер UUID
from fastapi import APIRouter, Depends, HTTPException, status, Path  # Query не використовується прямо тут
from sqlalchemy.ext.asyncio import AsyncSession  # Не використовується прямо, якщо сесія в сервісі

from backend.app.src.api.dependencies import get_api_db_session, get_current_active_superuser, paginator
from backend.app.src.models.auth.user import User as UserModel  # Для типізації current_admin_user
from backend.app.src.schemas.notifications.delivery import NotificationDeliveryAttemptResponse
from backend.app.src.core.pagination import PagedResponse, PageParams
from backend.app.src.services.notifications.delivery import NotificationDeliveryService
from backend.app.src.config import settings as global_settings
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

router = APIRouter(
    # Префікс /delivery-attempts буде додано в __init__.py батьківського роутера notifications
    # Теги також успадковуються/додаються звідти
    dependencies=[Depends(get_current_active_superuser)]  # Всі ендпоінти тут вимагають прав суперкористувача
)


# Залежність для отримання NotificationDeliveryService
async def get_notification_delivery_service(
        session: AsyncSession = Depends(get_api_db_session)) -> NotificationDeliveryService:
    """Залежність FastAPI для отримання екземпляра NotificationDeliveryService."""
    return NotificationDeliveryService(db_session=session)


@router.get(
    "/notification/{notification_id}",
    response_model=PagedResponse[NotificationDeliveryAttemptResponse],
    summary="Отримання спроб доставки для сповіщення (Адмін/Суперюзер)",  # i18n
    description="Повертає список спроб та статусів доставки для конкретного сповіщення, з пагінацією."  # i18n
)
async def list_delivery_attempts_for_notification_endpoint(  # Перейменовано
        notification_id: UUID = Path(..., description="ID сповіщення, для якого запитуються статуси доставки"),  # i18n
        page_params: PageParams = Depends(paginator),
        # current_admin_user: UserModel = Depends(get_current_active_superuser), # Вже в router.dependencies
        delivery_service: NotificationDeliveryService = Depends(get_notification_delivery_service)
) -> PagedResponse[NotificationDeliveryAttemptResponse]:
    """
    Отримує історію спроб доставки для вказаного сповіщення.
    Доступно тільки суперкористувачам (або адміністраторам з відповідними правами).
    """
    logger.debug(f"Запит спроб доставки для сповіщення ID: {notification_id}, сторінка: {page_params.page}.")

    # TODO: NotificationDeliveryService.list_delivery_attempts_for_notification_paginated має повертати (items, total_count)
    attempts_orm, total_attempts = await delivery_service.list_delivery_attempts_for_notification_paginated(
        notification_id=notification_id,
        skip=page_params.skip,
        limit=page_params.limit
    )

    return PagedResponse[NotificationDeliveryAttemptResponse](
        total=total_attempts,
        page=page_params.page,
        size=page_params.size,
        results=[NotificationDeliveryAttemptResponse.model_validate(att) for att in attempts_orm]  # Pydantic v2
    )


@router.get(
    "/{delivery_attempt_id}",
    response_model=NotificationDeliveryAttemptResponse,
    summary="Отримання деталей конкретної спроби доставки (Адмін/Суперюзер)",  # i18n
    description="Повертає детальну інформацію про конкретну спробу доставки сповіщення."  # i18n
)
# ПРИМІТКА: Важливо, щоб сервісний метод `get_delivery_attempt_by_id`
# (або спеціалізований `get_delivery_attempt_by_id_admin`) належним чином
# обробляв права доступу, оскільки цей ендпоінт призначений для адміністраторів.
async def get_delivery_attempt_details_endpoint(  # Перейменовано
        delivery_attempt_id: UUID = Path(..., description="ID спроби доставки"),  # i18n
        # current_admin_user: UserModel = Depends(get_current_active_superuser), # Вже в router.dependencies
        delivery_service: NotificationDeliveryService = Depends(get_notification_delivery_service)
) -> NotificationDeliveryAttemptResponse:
    """
    Отримує деталі конкретної спроби доставки.
    Доступно тільки суперкористувачам (або адміністраторам з відповідними правами).
    """
    logger.debug(f"Запит деталей спроби доставки ID: {delivery_attempt_id}.")
    # TODO: NotificationDeliveryService.get_delivery_attempt_by_id_admin має перевіряти права або цей ендпоінт має бути захищений
    attempt = await delivery_service.get_delivery_attempt_by_id(  # Припускаємо, що цей метод існує
        attempt_id=delivery_attempt_id
        # requesting_user_id=current_admin_user.id # Якщо сервіс потребує для аудиту/прав
    )
    if not attempt:
        logger.warning(f"Спроба доставки з ID '{delivery_attempt_id}' не знайдена.")
        # i18n
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Спроба доставки з ID {delivery_attempt_id} не знайдена.")
    return attempt  # Сервіс вже повертає Pydantic модель


# TODO: Розглянути ендпоінт для ініціювання повторної спроби доставки (POST /{delivery_attempt_id}/retry),
#  якщо це потрібно для адміністрування. Він би викликав
#  `delivery_service.retry_specific_failed_attempt(attempt_id)`.

logger.info(f"Роутер для спроб доставки сповіщень (`{router.prefix}`) визначено.")
