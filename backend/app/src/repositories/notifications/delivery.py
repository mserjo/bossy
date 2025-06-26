# backend/app/src/repositories/notifications/delivery.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `NotificationDeliveryModel`.
Надає методи для управління записами про доставку сповіщень.
"""

from typing import Optional, List
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select, and_ # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.notifications.delivery import NotificationDeliveryModel
from backend.app.src.schemas.notifications.delivery import NotificationDeliveryCreateSchema, NotificationDeliveryUpdateSchema
from backend.app.src.repositories.base import BaseRepository
from backend.app.src.core.dicts import NotificationDeliveryStatusEnum

class NotificationDeliveryRepository(BaseRepository[NotificationDeliveryModel, NotificationDeliveryCreateSchema, NotificationDeliveryUpdateSchema]):
    """
    Репозиторій для роботи з моделлю статусів доставки сповіщень (`NotificationDeliveryModel`).
    """

    async def get_deliveries_for_notification(
        self, db: AsyncSession, *, notification_id: uuid.UUID
    ) -> List[NotificationDeliveryModel]:
        """
        Отримує всі записи про спроби доставки для конкретного сповіщення.
        """
        statement = select(self.model).where(self.model.notification_id == notification_id)
        statement = statement.order_by(self.model.created_at.asc()) # type: ignore # В хронологічному порядку
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def get_pending_retries(
        self, db: AsyncSession, *, limit: int = 100
    ) -> List[NotificationDeliveryModel]:
        """
        Отримує записи про доставку, які очікують повторної спроби.
        """
        statement = select(self.model).where(
            self.model.status_code == NotificationDeliveryStatusEnum.RETRYING, # Використовуємо Enum
            self.model.next_retry_at <= datetime.utcnow() # Час для повтору настав
        ).order_by(self.model.next_retry_at.asc()).limit(limit) # type: ignore
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def get_by_provider_message_id(
        self, db: AsyncSession, *, channel_code: str, provider_message_id: str
    ) -> Optional[NotificationDeliveryModel]:
        """
        Отримує запис доставки за ідентифікатором повідомлення від провайдера.
        Корисно для обробки вебхуків від сервісів доставки.
        """
        statement = select(self.model).where(
            self.model.channel_code == channel_code, # Використовуємо channel_code з моделі, який є str
            self.model.provider_message_id == provider_message_id
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    # `create` успадкований. `NotificationDeliveryCreateSchema` використовується.
    # `update` успадкований. `NotificationDeliveryUpdateSchema` для оновлення статусу.
    # `delete` успадкований (для видалення старих записів про доставку, якщо потрібно).

notification_delivery_repository = NotificationDeliveryRepository(NotificationDeliveryModel)

# TODO: Переконатися, що `NotificationDeliveryCreateSchema` та `NotificationDeliveryUpdateSchema`
#       коректно визначені та використовують `NotificationChannelEnum` та `NotificationDeliveryStatusEnum`.
#       (Схеми вже оновлені для використання Enum'ів).
#
# TODO: Розглянути методи для пакетного оновлення статусів, якщо це буде потрібно
#       (наприклад, при отриманні вебхуків від провайдера про масову доставку).
#
# Все виглядає добре. Надано методи для отримання записів доставки.
# `get_pending_retries` важливий для системи повторних спроб.
# `get_by_provider_message_id` для обробки вебхуків.
