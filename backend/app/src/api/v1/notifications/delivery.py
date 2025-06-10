# backend/app/src/api/v1/notifications/delivery.py
from typing import List, Optional, Generic, TypeVar # Додано Generic, TypeVar для PaginatedResponse
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from pydantic import BaseModel # Додано BaseModel для PaginatedResponse, якщо визначається локально
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_superuser # Адміністративні дії
from app.src.models.auth import User as UserModel
# from app.src.models.notifications import NotificationDeliveryAttempt as NotificationDeliveryAttemptModel # Потрібна модель
from app.src.schemas.notifications.delivery import ( # Схеми для статусу доставки
    NotificationDeliveryAttemptResponse
)
# Припускаємо, що ці схеми імпортуються, якщо ні - можна визначити як у users.py або groups.py
from app.src.schemas.pagination import PaginatedResponse, PageParams
from app.src.services.notifications.delivery import NotificationDeliveryService # Сервіс для статусу доставки

router = APIRouter()

@router.get(
    "/notification/{notification_id}", # Шлях відносно /notifications/delivery/notification/{notification_id}
    response_model=PaginatedResponse[NotificationDeliveryAttemptResponse],
    summary="Отримання статусів доставки для сповіщення (Адмін/Суперюзер)",
    description="Повертає список спроб та статусів доставки для конкретного сповіщення, з пагінацією."
)
async def list_delivery_attempts_for_notification(
    notification_id: int = Path(..., description="ID сповіщення, для якого запитуються статуси доставки"),
    page_params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    current_admin_user: UserModel = Depends(get_current_active_superuser),
    delivery_service: NotificationDeliveryService = Depends()
):
    '''
    Отримує історію спроб доставки для вказаного сповіщення.
    '''
    if not hasattr(delivery_service, 'db_session') or delivery_service.db_session is None:
        delivery_service.db_session = db

    total_attempts, attempts = await delivery_service.get_delivery_attempts_for_notification(
        notification_id=notification_id,
        # requesting_user=current_admin_user, # Для можливої перевірки прав у сервісі
        skip=page_params.skip,
        limit=page_params.limit
    )
    if not attempts and total_attempts == 0: # Якщо взагалі нічого не знайдено (можливо, і сповіщення немає)
        # Можна перевірити існування самого notification_id окремо, якщо потрібно розрізняти
        # "немає сповіщення" від "немає спроб доставки для існуючого сповіщення"
        pass # Сервіс може повернути порожній список, що є нормальним

    return PaginatedResponse[NotificationDeliveryAttemptResponse]( # Явно вказуємо тип Generic
        total=total_attempts,
        page=page_params.page,
        size=page_params.size,
        results=[NotificationDeliveryAttemptResponse.model_validate(att) for att in attempts]
    )

@router.get(
    "/{delivery_attempt_id}", # Шлях відносно /notifications/delivery/{delivery_attempt_id}
    response_model=NotificationDeliveryAttemptResponse,
    summary="Отримання деталей конкретної спроби доставки (Адмін/Суперюзер)",
    description="Повертає детальну інформацію про конкретну спробу доставки сповіщення."
)
async def get_delivery_attempt_details(
    delivery_attempt_id: int = Path(..., description="ID спроби доставки"),
    db: AsyncSession = Depends(get_db_session),
    current_admin_user: UserModel = Depends(get_current_active_superuser),
    delivery_service: NotificationDeliveryService = Depends()
):
    '''
    Отримує деталі конкретної спроби доставки.
    '''
    if not hasattr(delivery_service, 'db_session') or delivery_service.db_session is None:
        delivery_service.db_session = db

    attempt = await delivery_service.get_delivery_attempt_by_id(
        attempt_id=delivery_attempt_id
        # requesting_user=current_admin_user # Якщо потрібна перевірка прав
        )
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Спроба доставки з ID {delivery_attempt_id} не знайдена."
        )
    return NotificationDeliveryAttemptResponse.model_validate(attempt)

# Міркування:
# 1.  Призначення: Ці ендпоінти переважно для діагностики та моніторингу системи сповіщень адміністраторами.
# 2.  Схеми: `NotificationDeliveryAttemptResponse` з `app.src.schemas.notifications.delivery`.
# 3.  Сервіс `NotificationDeliveryService`: Відповідає за отримання інформації про спроби доставки.
#     Фактичне створення записів про спроби доставки відбувається в інших сервісах,
#     які відповідають за відправку сповіщень (наприклад, EmailNotificationService, SMSNotificationService).
# 4.  Права доступу: Тільки адміністратори/суперюзери.
# 5.  Пагінація: Для списку спроб доставки для конкретного сповіщення.
# 6.  URL-и: Цей роутер буде підключений до `notifications_router` з префіксом `/delivery`.
#     Шляхи будуть `/api/v1/notifications/delivery/notification/{notification_id}` та `/api/v1/notifications/delivery/{delivery_attempt_id}`.
# 7.  Коментарі: Українською мовою.
