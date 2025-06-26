# backend/app/src/repositories/notifications/notification.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `NotificationModel`.
Надає методи для управління сповіщеннями користувачів.
"""

from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime
from sqlalchemy import select, and_, update # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload # type: ignore

from backend.app.src.models.notifications.notification import NotificationModel
from backend.app.src.schemas.notifications.notification import NotificationCreateSchema, NotificationUpdateSchema
from backend.app.src.repositories.base import BaseRepository

class NotificationRepository(BaseRepository[NotificationModel, NotificationCreateSchema, NotificationUpdateSchema]):
    """
    Репозиторій для роботи з моделлю сповіщень (`NotificationModel`).
    """

    async def get_notifications_for_user(
        self, db: AsyncSession, *,
        recipient_user_id: uuid.UUID,
        is_read: Optional[bool] = None,
        notification_type_code: Optional[str] = None,
        skip: int = 0, limit: int = 20 # За замовчуванням менший ліміт для сповіщень
    ) -> List[NotificationModel]:
        """
        Отримує список сповіщень для вказаного користувача з можливістю фільтрації.
        """
        statement = select(self.model).where(self.model.recipient_user_id == recipient_user_id)

        if is_read is not None:
            statement = statement.where(self.model.is_read == is_read)

        if notification_type_code:
            statement = statement.where(self.model.notification_type_code == notification_type_code)

        statement = statement.order_by(self.model.created_at.desc()).offset(skip).limit(limit) # type: ignore
        # Можна додати selectinload для group, якщо потрібно
        # .options(selectinload(self.model.group))

        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def mark_as_read(self, db: AsyncSession, *, notification_id: uuid.UUID, recipient_user_id: uuid.UUID) -> Optional[NotificationModel]:
        """
        Позначає сповіщення як прочитане.
        Перевіряє, що сповіщення належить вказаному отримувачу.
        """
        notification = await self.get(db, notification_id)
        if notification and notification.recipient_user_id == recipient_user_id and not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow() # Або func.now()
            db.add(notification)
            await db.commit()
            await db.refresh(notification)
            return notification
        return None # Або кидати виняток, якщо сповіщення не знайдено або не належить користувачу

    async def mark_multiple_as_read(self, db: AsyncSession, *, notification_ids: List[uuid.UUID], recipient_user_id: uuid.UUID) -> int:
        """
        Позначає декілька сповіщень як прочитані для вказаного користувача.
        Повертає кількість оновлених записів.
        """
        statement = (
            update(self.model)
            .where(
                self.model.id.in_(notification_ids), # type: ignore
                self.model.recipient_user_id == recipient_user_id,
                self.model.is_read == False
            )
            .values(is_read=True, read_at=datetime.utcnow()) # Або func.now()
            .execution_options(synchronize_session="fetch") # Важливо для оновлення сесії
        )
        result = await db.execute(statement)
        await db.commit()
        return result.rowcount # type: ignore

    async def count_unread_notifications_for_user(self, db: AsyncSession, *, recipient_user_id: uuid.UUID) -> int:
        """
        Підраховує кількість непрочитаних сповіщень для користувача.
        """
        statement = select(func.count(self.model.id)).where( # type: ignore
            self.model.recipient_user_id == recipient_user_id,
            self.model.is_read == False
        )
        result = await db.execute(statement)
        return result.scalar_one() or 0

    # `create` успадкований. `NotificationCreateSchema` використовується.
    # `update` успадкований, але для зміни статусу is_read краще використовувати `mark_as_read`.
    # `delete` успадкований. "М'яке" видалення не передбачено в BaseModel.

notification_repository = NotificationRepository(NotificationModel)

# TODO: Переконатися, що `NotificationCreateSchema` та `NotificationUpdateSchema` коректно визначені.
#       `NotificationCreateSchema` має містити всі необхідні поля для створення сповіщення
#       (recipient_user_id, body, notification_type_code; title, group_id, source_entity опціонально).
#       `NotificationUpdateSchema` в основному для `is_read`.
#
# TODO: Розглянути методи для видалення старих сповіщень (наприклад, старше N днів).
#
# Все виглядає добре. Надано методи для отримання, позначки про прочитання та підрахунку сповіщень.
# Використання `func.count` для підрахунку.
# `mark_multiple_as_read` для оптимізації масових операцій.
