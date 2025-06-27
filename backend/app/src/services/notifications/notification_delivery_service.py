# backend/app/src/services/notifications/notification_delivery_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `NotificationDeliveryService` для управління
статусами доставки сповіщень.
"""
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.notifications.delivery import NotificationDeliveryModel
from backend.app.src.schemas.notifications.delivery import (
    NotificationDeliveryCreateSchema, NotificationDeliveryUpdateSchema, NotificationDeliverySchema
)
from backend.app.src.repositories.notifications.delivery import NotificationDeliveryRepository, notification_delivery_repository
# from backend.app.src.repositories.notifications.notification import notification_repository # Для перевірки існування сповіщення
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, BadRequestException
from backend.app.src.core.dicts import NotificationChannelEnum, NotificationDeliveryStatusEnum

class NotificationDeliveryService(BaseService[NotificationDeliveryRepository]):
    """
    Сервіс для управління статусами доставки сповіщень.
    Зазвичай, записи створюються та оновлюються внутрішніми процесами відправки сповіщень
    та обробки вебхуків від провайдерів доставки.
    """

    async def get_delivery_by_id(self, db: AsyncSession, delivery_id: uuid.UUID) -> NotificationDeliveryModel:
        delivery = await self.repository.get(db, id=delivery_id)
        if not delivery:
            raise NotFoundException(f"Запис доставки з ID {delivery_id} не знайдено.")
        return delivery

    async def create_delivery_record(
        self, db: AsyncSession, *, obj_in: NotificationDeliveryCreateSchema
    ) -> NotificationDeliveryModel:
        """
        Створює новий запис про спробу доставки сповіщення.
        """
        # Перевірка існування сповіщення
        from backend.app.src.repositories.notifications.notification import notification_repository # Відкладений імпорт
        notification = await notification_repository.get(db, id=obj_in.notification_id)
        if not notification:
            raise BadRequestException(f"Сповіщення з ID {obj_in.notification_id} для доставки не знайдено.")

        # Валідація channel_code та status_code вже відбувається через Enum в схемі.
        # `attempt_count` за замовчуванням 0 в схемі.

        # Якщо `status_code` не передано, Pydantic схема встановить PENDING.
        # Якщо `channel_code` не передано, Pydantic схема видасть помилку (бо він обов'язковий).

        return await self.repository.create(db, obj_in=obj_in)

    async def update_delivery_status(
        self, db: AsyncSession, *,
        delivery_id: Optional[uuid.UUID] = None, # Можна оновлювати за ID запису
        provider_message_id: Optional[str] = None, # Або за ID від провайдера
        channel_code_for_provider_lookup: Optional[NotificationChannelEnum] = None, # Потрібен, якщо шукаємо за provider_message_id
        obj_in: NotificationDeliveryUpdateSchema
    ) -> NotificationDeliveryModel:
        """
        Оновлює статус та іншу інформацію для запису доставки.
        Може знаходити запис за `delivery_id` або за `provider_message_id` + `channel_code`.
        """
        db_delivery: Optional[NotificationDeliveryModel] = None
        if delivery_id:
            db_delivery = await self.get_delivery_by_id(db, delivery_id=delivery_id)
        elif provider_message_id and channel_code_for_provider_lookup:
            db_delivery = await self.repository.get_by_provider_message_id(
                db, channel_code=channel_code_for_provider_lookup.value, provider_message_id=provider_message_id
            )
            if not db_delivery:
                # Можливо, це перше оновлення статусу від провайдера, і запис ще не створено
                # або `provider_message_id` ще не було встановлено.
                # В такому випадку, цей метод не підходить, потрібен `create_or_update`.
                # Або ж, якщо очікується, що запис вже існує, то це NotFound.
                raise NotFoundException(f"Запис доставки для провайдера {provider_message_id} (канал {channel_code_for_provider_lookup.value}) не знайдено.")
        else:
            raise BadRequestException("Необхідно вказати delivery_id або provider_message_id з channel_code для оновлення статусу доставки.")

        # Оновлюємо поля. `NotificationDeliveryUpdateSchema` містить лише ті поля, що можна оновлювати.
        # `attempt_count` може бути збільшено тут або в логіці повторних спроб.
        update_data = obj_in.model_dump(exclude_unset=True)

        # Якщо оновлюється статус, і він FAILED або RETRYING, збільшуємо attempt_count
        # Цю логіку краще винести в окремий метод або обробник.
        # Поки що, якщо attempt_count передано в схемі, він буде встановлений.
        # Якщо ні, то він не зміниться (якщо не був None).
        # Якщо потрібно інкрементувати, то:
        # if "status_code" in update_data and update_data["status_code"] in [NotificationDeliveryStatusEnum.FAILED, NotificationDeliveryStatusEnum.RETRYING]:
        #     if db_delivery.attempt_count is None: db_delivery.attempt_count = 0 # На випадок, якщо було NULL
        #     update_data["attempt_count"] = db_delivery.attempt_count + 1
        # else: # Якщо успішно або інший статус, можна скинути attempt_count, якщо він був для retry
        #     if "attempt_count" not in update_data and db_delivery.status_code == NotificationDeliveryStatusEnum.RETRYING:
        #         update_data["attempt_count"] = 0 # Скидаємо лічильник, якщо статус змінився з RETRYING

        return await self.repository.update(db, db_obj=db_delivery, obj_in=update_data) # obj_in тут словник

    async def schedule_retry(
        self, db: AsyncSession, *, delivery_obj: NotificationDeliveryModel, retry_delay_seconds: int
    ) -> NotificationDeliveryModel:
        """Планує повторну спробу доставки."""
        if delivery_obj.status_code != NotificationDeliveryStatusEnum.FAILED:
            # Можна кинути помилку або просто проігнорувати, якщо статус не FAILED
            self.logger.warning(f"Спроба запланувати retry для доставки {delivery_obj.id}, яка не в статусі FAILED (поточний: {delivery_obj.status_code}).")
            return delivery_obj # Не змінюємо

        update_schema = NotificationDeliveryUpdateSchema(
            status_code=NotificationDeliveryStatusEnum.RETRYING,
            next_retry_at=datetime.utcnow() + timedelta(seconds=retry_delay_seconds),
            attempt_count=(delivery_obj.attempt_count or 0) + 1 # Збільшуємо лічильник
        )
        return await self.repository.update(db, db_obj=delivery_obj, obj_in=update_schema)

    # TODO: Додати метод для отримання списку доставок з фільтрами (наприклад, за статусом, каналом).

notification_delivery_service = NotificationDeliveryService(notification_delivery_repository)

# TODO: Узгодити логіку оновлення `attempt_count` в `update_delivery_status`.
#       Краще, щоб це робилося явно, або в `schedule_retry`.
#
# TODO: Реалізувати фонову задачу (Celery), яка буде періодично викликати
#       `NotificationDeliveryRepository.get_pending_retries()` та намагатися
#       повторно відправити сповіщення.
#
# Все виглядає як хороший початок для NotificationDeliveryService.
# Основні методи для створення та оновлення статусів доставки.
# `schedule_retry` для логіки повторних спроб.
# Валідація Enum'ів для `channel_code` та `status_code` відбувається на рівні схем.
