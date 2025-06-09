# backend/app/src/api/v1/notifications/notifications.py
from typing import List, Optional, Generic, TypeVar # Додано Generic, TypeVar для PaginatedResponse
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from pydantic import BaseModel # Додано BaseModel для PaginatedResponse, якщо визначається локально
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_user
from app.src.models.auth import User as UserModel
# from app.src.models.notifications import Notification as NotificationModel # Потрібна модель сповіщення
from app.src.schemas.notifications.notification import ( # Схеми для сповіщень
    NotificationResponse,
    # NotificationUpdate # Може не знадобитися, якщо дії прості
)
from app.src.schemas.message import MessageResponse # Для простих відповідей типу "OK"
# Припускаємо, що ці схеми імпортуються, якщо ні - можна визначити як у users.py або groups.py
from app.src.schemas.pagination import PaginatedResponse, PageParams
from app.src.services.notifications.notification import InternalNotificationService # Сервіс для сповіщень

router = APIRouter()

@router.get(
    "/", # Шлях відносно /notifications/
    response_model=PaginatedResponse[NotificationResponse],
    summary="Отримання списку сповіщень поточного користувача",
    description="Повертає список сповіщень для поточного аутентифікованого користувача з пагінацією. Може фільтруватися за статусом (прочитані/непрочитані)."
)
async def list_my_notifications(
    page_params: PageParams = Depends(),
    unread_only: Optional[bool] = Query(None, description="Показати тільки непрочитані сповіщення"),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    notification_service: InternalNotificationService = Depends()
):
    '''
    Отримує список сповіщень для поточного користувача.
    '''
    if not hasattr(notification_service, 'db_session') or notification_service.db_session is None:
        notification_service.db_session = db

    total_notifications, notifications = await notification_service.get_user_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        skip=page_params.skip,
        limit=page_params.limit
    )
    return PaginatedResponse[NotificationResponse]( # Явно вказуємо тип Generic
        total=total_notifications,
        page=page_params.page,
        size=page_params.size,
        results=[NotificationResponse.model_validate(n) for n in notifications]
    )

@router.post(
    "/{notification_id}/mark-as-read",
    response_model=NotificationResponse, # Повертаємо оновлене сповіщення
    summary="Позначення сповіщення як прочитаного",
    description="Позначає вказане сповіщення як прочитане для поточного користувача."
)
async def mark_notification_as_read(
    notification_id: int = Path(..., description="ID сповіщення, яке позначається як прочитане"),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    notification_service: InternalNotificationService = Depends()
):
    '''
    Позначає сповіщення як прочитане.
    Сервіс має перевірити, чи належить сповіщення поточному користувачу.
    '''
    if not hasattr(notification_service, 'db_session') or notification_service.db_session is None:
        notification_service.db_session = db

    updated_notification = await notification_service.mark_notification_as_read(
        notification_id=notification_id,
        user_id=current_user.id
    )
    if not updated_notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Сповіщення з ID {notification_id} не знайдено або не належить вам."
        )
    return NotificationResponse.model_validate(updated_notification)

@router.post(
    "/mark-all-as-read",
    response_model=MessageResponse, # Або кількість оновлених сповіщень
    summary="Позначення всіх непрочитаних сповіщень як прочитаних",
    description="Позначає всі непрочитані сповіщення поточного користувача як прочитані."
)
async def mark_all_my_notifications_as_read(
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    notification_service: InternalNotificationService = Depends()
):
    '''
    Позначає всі непрочитані сповіщення користувача як прочитані.
    '''
    if not hasattr(notification_service, 'db_session') or notification_service.db_session is None:
        notification_service.db_session = db

    count = await notification_service.mark_all_notifications_as_read_for_user(user_id=current_user.id)
    return MessageResponse(message=f"Успішно позначено {count} сповіщень як прочитані.")


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
    summary="Отримання деталей конкретного сповіщення",
    description="Повертає детальну інформацію про вказане сповіщення, якщо воно належить поточному користувачу."
)
async def get_notification_details(
    notification_id: int = Path(..., description="ID сповіщення"),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    notification_service: InternalNotificationService = Depends()
):
    '''
    Отримує деталі сповіщення.
    Сервіс перевіряє належність сповіщення користувачу.
    '''
    if not hasattr(notification_service, 'db_session') or notification_service.db_session is None:
        notification_service.db_session = db

    notification = await notification_service.get_notification_by_id_for_user(
        notification_id=notification_id,
        user_id=current_user.id
    )
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Сповіщення з ID {notification_id} не знайдено або не належить вам."
        )
    return NotificationResponse.model_validate(notification)


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення сповіщення",
    description="Дозволяє користувачу видалити своє сповіщення."
)
async def delete_my_notification(
    notification_id: int = Path(..., description="ID сповіщення, яке видаляється"),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    notification_service: InternalNotificationService = Depends()
):
    '''
    Видаляє сповіщення користувача.
    Сервіс перевіряє належність сповіщення користувачу.
    '''
    if not hasattr(notification_service, 'db_session') or notification_service.db_session is None:
        notification_service.db_session = db

    success = await notification_service.delete_notification_for_user(
        notification_id=notification_id,
        user_id=current_user.id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Не вдалося видалити сповіщення з ID {notification_id}. Можливо, воно не існує або не належить вам."
        )
    # HTTP 204 No Content

# Міркування:
# 1.  Схеми: `NotificationResponse`, `MessageResponse`, `PaginatedResponse`, `PageParams`.
#     `NotificationUpdate` може не знадобитися, якщо дії (mark-as-read) не потребують тіла запиту.
# 2.  Сервіс `InternalNotificationService`: Керує логікою отримання, оновлення (статус прочитано) та видалення сповіщень.
#     Забезпечує, що користувачі взаємодіють тільки зі своїми сповіщеннями.
# 3.  Права доступу: Всі операції виконуються в контексті поточного аутентифікованого користувача.
# 4.  Пагінація: Для списку сповіщень. Фільтр `unread_only`.
# 5.  URL-и: Цей роутер буде основним для префіксу `/notifications`.
#     Шляхи будуть `/api/v1/notifications/`, `/api/v1/notifications/{notification_id}/mark-as-read` тощо.
# 6.  Коментарі: Українською мовою.
