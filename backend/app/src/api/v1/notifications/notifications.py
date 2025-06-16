# backend/app/src/api/v1/notifications/notifications.py
# -*- coding: utf-8 -*-
"""
API маршрути для управління сповіщеннями користувачів.

Цей модуль визначає ендпоінти для перегляду сповіщень,
позначення їх як прочитаних/непрочитаних, видалення,
а також (концептуально) для створення сповіщень системою або адміністраторами.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
# ПРИМІТКА: У цьому файлі використовується підхід передачі `db_session` в екземпляр
# сервісу (`notification_service.db_session = db_session`) всередині кожного ендпоінта.
# Це відрізняється від підходу в інших частинах API, де сесія зазвичай ін'єктується
# в конструктор сервісу через залежність. Варто розглянути уніфікацію цього механізму
# для консистентності та уникнення потенційних проблем з управлінням сесіями.
from typing import List, Optional
import uuid  # Для використання UUID як ID сповіщень, якщо це стандарт

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body

# --- Імпорт компонентів додатку ---
from backend.app.src.core.database import get_db_session  # Залежність для сесії БД
from backend.app.src.api.dependencies import get_current_active_user, \
    get_current_active_superuser  # Залежності для користувачів
from backend.app.src.models.auth import User as UserModel  # Модель користувача SQLAlchemy
from backend.app.src.schemas.notifications.notification_schemas import (
    NotificationResponseSchema,
    NotificationCreateSchema,  # Схема для створення сповіщення (якщо буде такий ендпоінт)
    NotificationStatusUpdateRequestSchema  # Схема для оновлення статусу (прочитано/непрочитано)
)
from backend.app.src.schemas.pagination_schemas import PaginatedResponseSchema, \
    PageParamsSchema  # Стандартні схеми пагінації
from backend.app.src.schemas.message_schemas import MessageResponseSchema  # Для простих відповідей
from backend.app.src.services.notification.notification_service import NotificationService  # Сервіс для сповіщень
from backend.app.src.config.logging import logger  # Централізований логер


# Базова функція-заглушка для інтернаціоналізації рядків
def _(text: str) -> str:
    return text


router = APIRouter()


# TODO: Розглянути можливість використання UUID для notification_id замість int, якщо це загальний стандарт проекту.
# TODO: Переглянути механізм ініціалізації db_session в сервісах.
#       Поточний підхід (service.db_session = db) працює, але краще, якщо сесія передається
#       в конструктор сервісу або в кожен метод, де вона потрібна, через Depends.

@router.get(
    "/my",
    response_model=PaginatedResponseSchema[NotificationResponseSchema],
    summary="Отримання списку моїх сповіщень",  # i18n
    description="Повертає список сповіщень для поточного аутентифікованого користувача з пагінацією. "  # i18n
                "Дозволяє фільтрувати за статусом прочитання."  # i18n
)
async def list_my_notifications(
        page_params: PageParamsSchema = Depends(),
        status_filter: Optional[str] = Query(None, enum=["read", "unread"], description=_(
            "Фільтр за статусом: 'read' (прочитані) або 'unread' (непрочитані).")),  # i18n
        db_session: AsyncSession = Depends(get_db_session),  # SQLAlchemy AsyncSession
        current_user: UserModel = Depends(get_current_active_user),
        notification_service: NotificationService = Depends()
):
    """
    Отримує список сповіщень для поточного користувача.
    Підтримує пагінацію та фільтрацію за статусом (прочитані/непрочитані).
    """
    logger.info(
        _("Користувач '{user_email}' запитує список своїх сповіщень. Фільтр статусу: {status_filter}, сторінка: {page}, розмір: {size}.").format(
            # i18n
            user_email=current_user.email, status_filter=status_filter, page=page_params.page, size=page_params.size
        ))
    notification_service.db_session = db_session  # TODO: Переглянути ініціалізацію сесії в сервісі

    # Перетворення рядкового фільтра на булевий unread_only або інший параметр для сервісу
    unread_only: Optional[bool] = None
    if status_filter == "unread":
        unread_only = True
    elif status_filter == "read":
        unread_only = False  # Або сервіс може приймати status="read"

    # Припускаємо, що сервіс повертає кортеж (загальна_кількість, список_об'єктів)
    total_notifications, notifications = await notification_service.get_user_notifications(
        user_id=current_user.id,
        unread_only=unread_only,  # Або передавати status_filter напряму, якщо сервіс це підтримує
        skip=page_params.skip,
        limit=page_params.limit
    )

    return PaginatedResponseSchema[NotificationResponseSchema](
        total=total_notifications,
        page=page_params.page,
        size=page_params.size,
        results=[NotificationResponseSchema.model_validate(n) for n in notifications]
    )


@router.patch(
    "/{notification_id}/status",
    response_model=NotificationResponseSchema,
    summary="Оновити статус сповіщення (прочитано/непрочитано)",  # i18n
    description="Дозволяє поточному користувачу позначити своє сповіщення як прочитане або непрочитане."  # i18n
)
async def update_notification_status(
        notification_id: uuid.UUID = Path(..., description=_("ID сповіщення для оновлення статусу.")),  # i18n
        status_update: NotificationStatusUpdateRequestSchema = Body(...),
        db_session: AsyncSession = Depends(get_db_session),
        current_user: UserModel = Depends(get_current_active_user),
        notification_service: NotificationService = Depends()
):
    """
    Оновлює статус прочитання для вказаного сповіщення, що належить поточному користувачу.
    """
    logger.info(
        _("Користувач '{user_email}' оновлює статус сповіщення ID '{notification_id}' на is_read={is_read}.").format(
            # i18n
            user_email=current_user.email, notification_id=notification_id, is_read=status_update.is_read
        ))
    notification_service.db_session = db_session  # TODO: Переглянути

    updated_notification = await notification_service.update_notification_read_status(
        notification_id=notification_id,
        user_id=current_user.id,
        is_read=status_update.is_read
    )
    if not updated_notification:
        # i18n: Error detail - Notification not found or access denied
        detail_msg = _("Сповіщення з ID '{notification_id}' не знайдено або доступ до нього обмежено.").format(
            notification_id=notification_id)
        logger.warning(f"{detail_msg} (користувач: {current_user.email})")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail_msg)
    return NotificationResponseSchema.model_validate(updated_notification)


@router.post(
    "/my/mark-all-as-read",
    response_model=MessageResponseSchema,
    summary="Позначити всі мої непрочитані сповіщення як прочитані",  # i18n
    description="Позначає всі непрочитані сповіщення поточного користувача як прочитані."  # i18n
)
async def mark_all_my_notifications_as_read(
        db_session: AsyncSession = Depends(get_db_session),
        current_user: UserModel = Depends(get_current_active_user),
        notification_service: NotificationService = Depends()
):
    """
    Позначає всі непрочитані сповіщення поточного користувача як прочитані.
    Повертає кількість оновлених сповіщень.
    """
    logger.info(_("Користувач '{user_email}' запитує позначення всіх своїх сповіщень як прочитаних.").format(
        user_email=current_user.email))  # i18n
    notification_service.db_session = db_session  # TODO: Переглянути

    count = await notification_service.mark_all_notifications_as_read_for_user(user_id=current_user.id)
    # i18n: Success message - Number of notifications marked as read
    return MessageResponseSchema(
        message=_("{count} сповіщень було успішно позначено як прочитані.").format(count=count))


@router.get(
    "/{notification_id}",
    response_model=NotificationResponseSchema,
    summary="Отримати деталі конкретного сповіщення",  # i18n
    description="Повертає детальну інформацію про вказане сповіщення, якщо воно належить поточному користувачу."  # i18n
)
async def get_notification_details(
        notification_id: uuid.UUID = Path(..., description=_("ID сповіщення для перегляду.")),  # i18n
        db_session: AsyncSession = Depends(get_db_session),
        current_user: UserModel = Depends(get_current_active_user),
        notification_service: NotificationService = Depends()
):
    """
    Отримує детальну інформацію про сповіщення за його ID.
    Сервіс має перевірити, що сповіщення належить поточному користувачеві.
    """
    logger.info(_("Користувач '{user_email}' запитує деталі сповіщення ID '{notification_id}'.").format(
        user_email=current_user.email, notification_id=notification_id))  # i18n
    notification_service.db_session = db_session  # TODO: Переглянути

    notification = await notification_service.get_notification_by_id_for_user(
        notification_id=notification_id,
        user_id=current_user.id
    )
    if not notification:
        # i18n: Error detail - Notification not found or access denied
        detail_msg = _("Сповіщення з ID '{notification_id}' не знайдено або доступ до нього обмежено.").format(
            notification_id=notification_id)
        logger.warning(f"{detail_msg} (користувач: {current_user.email})")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail_msg)
    return NotificationResponseSchema.model_validate(notification)


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити моє сповіщення",  # i18n
    description="Дозволяє поточному користувачу видалити своє сповіщення."  # i18n
)
async def delete_my_notification(
        notification_id: uuid.UUID = Path(..., description=_("ID сповіщення, яке видаляється.")),  # i18n
        db_session: AsyncSession = Depends(get_db_session),
        current_user: UserModel = Depends(get_current_active_user),
        notification_service: NotificationService = Depends()
):
    """
    Видаляє сповіщення, що належить поточному користувачу.
    Сервіс має перевірити належність перед видаленням.
    """
    logger.info(_("Користувач '{user_email}' запитує видалення сповіщення ID '{notification_id}'.").format(
        user_email=current_user.email, notification_id=notification_id))  # i18n
    notification_service.db_session = db_session  # TODO: Переглянути

    success = await notification_service.delete_notification_for_user(
        notification_id=notification_id,
        user_id=current_user.id
    )
    if not success:  # Сервіс повертає True при успішному видаленні, False якщо не знайдено/не належить
        # i18n: Error detail - Failed to delete notification
        detail_msg = _(
            "Не вдалося видалити сповіщення з ID '{notification_id}'. Можливо, воно не існує або не належить вам.").format(
            notification_id=notification_id)
        logger.warning(f"{detail_msg} (користувач: {current_user.email})")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail_msg)

    # Успішне видалення, повертаємо 204 No Content (тіло відповіді буде порожнім)
    logger.info(_("Сповіщення ID '{notification_id}' успішно видалено для користувача '{user_email}'.").format(
        notification_id=notification_id, user_email=current_user.email))  # i18n
    return None


# --- Ендпоінти для створення сповіщень (зазвичай для адміністраторів або системи) ---
# TODO: Реалізувати логіку створення сповіщень в NotificationService.
# TODO: Визначити точні права доступу: хто може створювати сповіщення (суперадміни, адміни груп, система).

@router.post(
    "/admin/create-direct",
    response_model=NotificationResponseSchema,
    summary="[Admin] Створити пряме сповіщення для користувача",  # i18n
    description="Дозволяє адміністратору створити пряме сповіщення для конкретного користувача. "  # i18n
                "Потребує прав адміністратора/суперкористувача.",  # i18n
    dependencies=[Depends(get_current_active_superuser)],  # Приклад захисту
    tags=["Admin Notifications"]  # Окремий тег для адмінських ендпоінтів
)
# ПРИМІТКА: Цей ендпоінт для створення прямих сповіщень адміністратором
# наразі є заглушкою і залежить від реалізації відповідного методу
# в `NotificationService`, як зазначено в TODO.
async def admin_create_direct_notification(
        notification_data: NotificationCreateSchema,  # Тіло запиту зі схемою створення
        db_session: AsyncSession = Depends(get_db_session),
        current_admin: UserModel = Depends(get_current_active_superuser),  # Для логування та перевірки прав
        notification_service: NotificationService = Depends()
):
    """
    Створює пряме сповіщення для вказаного користувача.
    Доступно тільки адміністраторам/суперкористувачам.
    """
    logger.info(
        _("Адміністратор '{admin_email}' створює пряме сповіщення для користувача ID '{user_id}'. Дані: {data}").format(
            # i18n
            admin_email=current_admin.email, user_id=notification_data.user_id, data=notification_data.model_dump_json()
        ))
    notification_service.db_session = db_session  # TODO: Переглянути

    # TODO: У NotificationService має бути метод типу `create_direct_notification`
    #       який приймає NotificationCreateSchema та, можливо, ID користувача, що створює (admin_id).
    #       Також, він має обробляти прапор `trigger_delivery`.
    # new_notification = await notification_service.create_direct_notification(
    #     create_schema=notification_data,
    #     created_by_user_id=current_admin.id # Опціонально, для аудиту
    # )
    # if not new_notification:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Не вдалося створити сповіщення.")
    # return NotificationResponseSchema.model_validate(new_notification)

    # Поки що заглушка, оскільки сервіс може не мати цього методу
    logger.warning("Функціонал admin_create_direct_notification ще не реалізовано повністю в сервісі. TODO.")  # i18n
    # i18n: Error detail - Feature not implemented
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED,
                        detail=_("Створення прямих сповіщень адміністратором ще не реалізовано."))


# TODO: Додати ендпоінт для створення сповіщень з шаблону (admin_create_from_template),
#       якщо така функціональність передбачена. Він буде схожий на admin_create_direct_notification,
#       але прийматиме ID шаблону та змінні для нього.

logger.info(_("Маршрутизатор для сповіщень API v1 (`notifications.router`) визначено."))  # i18n
