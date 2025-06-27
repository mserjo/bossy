# backend/app/src/services/notifications/notification_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `NotificationService` для управління сповіщеннями.
"""
from typing import List, Optional, Dict, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.notifications.notification import NotificationModel
from backend.app.src.models.auth.user import UserModel
from backend.app.src.schemas.notifications.notification import NotificationCreateSchema, NotificationUpdateSchema, NotificationSchema
from backend.app.src.repositories.notifications.notification import NotificationRepository, notification_repository
from backend.app.src.repositories.auth.user import user_repository # Для перевірки отримувача
from backend.app.src.repositories.groups.group import group_repository # Для перевірки групи (якщо є)
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.dicts import NotificationTypeEnum # Для валідації типу

class NotificationService(BaseService[NotificationRepository]):
    """
    Сервіс для управління сповіщеннями.
    """

    async def get_notification_by_id(self, db: AsyncSession, notification_id: uuid.UUID, recipient_user_id: Optional[uuid.UUID] = None) -> NotificationModel:
        """
        Отримує сповіщення за ID.
        Якщо вказано `recipient_user_id`, перевіряє, чи сповіщення належить цьому користувачеві.
        """
        notification = await self.repository.get(db, id=notification_id) # Репозиторій може завантажувати зв'язки
        if not notification:
            raise NotFoundException(f"Сповіщення з ID {notification_id} не знайдено.")
        if recipient_user_id and notification.recipient_user_id != recipient_user_id:
            raise ForbiddenException("Ви не маєте доступу до цього сповіщення.")
        return notification

    async def create_notification(
        self, db: AsyncSession, *, obj_in: NotificationCreateSchema
        # current_user: Optional[UserModel] = None # Хто ініціював створення (може бути система)
    ) -> NotificationModel:
        """
        Створює нове сповіщення. Зазвичай викликається іншими сервісами або системними подіями.
        """
        # Перевірка існування отримувача
        recipient = await user_repository.get(db, id=obj_in.recipient_user_id)
        if not recipient:
            # Якщо отримувача немає, логуємо і не створюємо сповіщення, або кидаємо помилку
            self.logger.error(f"Спроба створити сповіщення для неіснуючого користувача ID: {obj_in.recipient_user_id}")
            raise BadRequestException(f"Отримувач сповіщення з ID {obj_in.recipient_user_id} не знайдений.")

        # Перевірка існування групи, якщо вказана
        if obj_in.group_id:
            group = await group_repository.get(db, id=obj_in.group_id)
            if not group:
                raise BadRequestException(f"Група з ID {obj_in.group_id} для сповіщення не знайдена.")

        # Валідація notification_type_code
        try:
            NotificationTypeEnum(obj_in.notification_type_code)
        except ValueError:
            raise BadRequestException(f"Невідомий тип сповіщення: {obj_in.notification_type_code}.")

        # TODO: Перевірка, чи є `source_entity_id` валідним ID для `source_entity_type`.

        # `created_by_user_id` для сповіщення (якщо модель його має)
        # може бути системним користувачем або тим, хто ініціював дію.
        # Поки що модель NotificationModel не має created_by_user_id (успадковує від BaseModel).

        return await self.repository.create(db, obj_in=obj_in)

    async def mark_notification_as_read(
        self, db: AsyncSession, *, notification_id: uuid.UUID, current_user: UserModel
    ) -> NotificationModel:
        """Позначає сповіщення як прочитане для поточного користувача."""
        # `get_notification_by_id` вже перевірить належність сповіщення користувачеві
        notification = await self.get_notification_by_id(db, notification_id=notification_id, recipient_user_id=current_user.id)

        updated_notification = await self.repository.mark_as_read(db, notification_id=notification.id, recipient_user_id=current_user.id)
        if not updated_notification: # Малоймовірно, якщо get_notification_by_id спрацював
            raise BadRequestException("Не вдалося позначити сповіщення як прочитане (можливо, вже прочитано або не належить вам).")
        return updated_notification

    async def mark_multiple_notifications_as_read(
        self, db: AsyncSession, *, notification_ids: List[uuid.UUID], current_user: UserModel
    ) -> int:
        """Позначає декілька сповіщень як прочитані для поточного користувача."""
        if not notification_ids:
            return 0
        updated_count = await self.repository.mark_multiple_as_read(db, notification_ids=notification_ids, recipient_user_id=current_user.id)
        return updated_count

    async def mark_all_notifications_as_read_for_user(
        self, db: AsyncSession, *, current_user: UserModel
    ) -> int:
        """Позначає всі непрочитані сповіщення користувача як прочитані."""
        # Отримуємо ID всіх непрочитаних сповіщень
        unread_notifications = await self.repository.get_notifications_for_user(
            db, recipient_user_id=current_user.id, is_read=False, limit=1000 # Обмеження для безпеки
        )
        unread_ids = [n.id for n in unread_notifications]
        if not unread_ids:
            return 0
        return await self.mark_multiple_notifications_as_read(db, notification_ids=unread_ids, current_user=current_user)


    async def get_unread_notifications_count(self, db: AsyncSession, *, current_user: UserModel) -> int:
        """Отримує кількість непрочитаних сповіщень для поточного користувача."""
        return await self.repository.count_unread_notifications_for_user(db, recipient_user_id=current_user.id)

    # TODO: Додати метод для видалення сповіщень (або м'якого видалення, якщо модель підтримує).
    # async def delete_notification(self, db: AsyncSession, *, notification_id: uuid.UUID, current_user: UserModel): ...

    # TODO: Інтеграція з NotificationTemplateService та NotificationDeliveryService
    #       для композиції та відправки сповіщень через різні канали.
    #       Цей сервіс (NotificationService) в основному відповідає за CRUD операції
    #       з самими записами сповіщень в БД.

notification_service = NotificationService(notification_repository)

# Коментарі:
# - Сервіс надає методи для створення, отримання та оновлення статусу прочитання сповіщень.
# - Перевірки існування сутностей (отримувач, група) перед створенням.
# - Валідація типу сповіщення.
# - Перевірка прав при отриманні/оновленні сповіщення (чи належить воно користувачеві).
# - Методи для масової позначки про прочитання.
# - TODO вказують на необхідність інтеграції з іншими сервісами для повної функціональності
#   системи сповіщень (композиція з шаблонів, відправка через канали).
#
# Все виглядає як хороший початок.
