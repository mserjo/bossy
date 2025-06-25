# backend/app/src/schemas/notifications/delivery.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `NotificationDeliveryModel`.
Схеми використовуються для відображення інформації про статус доставки сповіщень
через різні канали. Записи зазвичай створюються та оновлюються системою.
"""

from pydantic import Field
from typing import Optional, List, Any, ForwardRef, Dict # Додано Dict
import uuid
from datetime import datetime

from backend.app.src.schemas.base import BaseSchema, AuditDatesSchema
# Потрібно буде імпортувати схему NotificationSchema для зв'язку
# from backend.app.src.schemas.notifications.notification import NotificationSchema

NotificationSchema = ForwardRef('backend.app.src.schemas.notifications.notification.NotificationSchema')

# --- Схема для відображення інформації про спробу доставки сповіщення (для читання) ---
class NotificationDeliverySchema(AuditDatesSchema): # Успадковує id, created_at, updated_at
    """
    Схема для представлення запису про спробу доставки сповіщення.
    """
    notification_id: uuid.UUID = Field(..., description="ID сповіщення, яке доставляється")
    channel_code: str = Field(..., max_length=50, description="Код каналу доставки (наприклад, 'EMAIL', 'SMS', 'PUSH')")
    recipient_address: str = Field(..., max_length=512, description="Адреса отримувача для цього каналу (email, телефон, device_token)")

    status_code: str = Field(..., max_length=50, description="Статус доставки (наприклад, 'PENDING', 'SENT', 'FAILED')")
    status_message: Optional[str] = Field(None, description="Деталі статусу або повідомлення про помилку")

    sent_at: Optional[datetime] = Field(None, description="Час, коли сповіщення було надіслано через цей канал")
    delivered_at: Optional[datetime] = Field(None, description="Час, коли сповіщення було доставлено")

    provider_message_id: Optional[str] = Field(None, max_length=255, description="ID повідомлення від зовнішнього провайдера")
    provider_response: Optional[Dict[str, Any]] = Field(None, description="Повна відповідь від провайдера (JSON)")

    attempt_count: int = Field(..., ge=0, description="Кількість спроб доставки")
    next_retry_at: Optional[datetime] = Field(None, description="Час наступної спроби (якщо планується)")

    # --- Розгорнуті зв'язки (приклад) ---
    # notification: Optional[NotificationSchema] = None # Зазвичай не розгортаємо, бо в контексті сповіщення


# --- Схема для створення запису про спробу доставки (зазвичай внутрішнє використання) ---
class NotificationDeliveryCreateSchema(BaseSchema):
    """
    Схема для створення запису про спробу доставки сповіщення.
    Використовується внутрішньою логікою системи сповіщень.
    """
    notification_id: uuid.UUID = Field(..., description="ID сповіщення")
    channel_code: str = Field(..., max_length=50, description="Код каналу доставки")
    recipient_address: str = Field(..., max_length=512, description="Адреса отримувача для каналу")

    status_code: str = Field(default="PENDING", max_length=50, description="Початковий статус доставки")
    # status_message: Optional[str] # Встановлюється при зміні статусу

    # sent_at, delivered_at, provider_message_id, provider_response - встановлюються пізніше
    attempt_count: int = Field(default=0, ge=0)
    # next_retry_at - встановлюється логікою повторних спроб

    # `id`, `created_at`, `updated_at` встановлюються автоматично.

# --- Схема для оновлення статусу доставки (зазвичай внутрішнє використання) ---
class NotificationDeliveryUpdateSchema(BaseSchema):
    """
    Схема для оновлення статусу доставки сповіщення.
    Використовується внутрішньою логікою системи при отриманні відповіді від провайдера
    або при плануванні повторних спроб.
    """
    status_code: str = Field(..., max_length=50, description="Новий статус доставки")
    status_message: Optional[str] = Field(None, description="Деталі статусу або повідомлення про помилку")

    sent_at: Optional[datetime] = Field(None, description="Час відправки (якщо оновлюється)")
    delivered_at: Optional[datetime] = Field(None, description="Час доставки (якщо оновлюється)")

    provider_message_id: Optional[str] = Field(None, max_length=255, description="ID повідомлення від провайдера")
    provider_response: Optional[Dict[str, Any]] = Field(None, description="Відповідь від провайдера")

    attempt_count: Optional[int] = Field(None, ge=0, description="Оновлена кількість спроб")
    next_retry_at: Optional[datetime] = Field(None, description="Новий час наступної спроби (або NULL, якщо не потрібно)")


# NotificationDeliverySchema.model_rebuild() # Для ForwardRef

# TODO: Переконатися, що схеми відповідають моделі `NotificationDeliveryModel`.
# `NotificationDeliveryModel` успадковує від `BaseModel`.
# `NotificationDeliverySchema` успадковує від `AuditDatesSchema` і відображає поля доставки.
#
# Поля: `notification_id`, `channel_code`, `recipient_address`, `status_code`, `status_message`,
# `sent_at`, `delivered_at`, `provider_message_id`, `provider_response`, `attempt_count`, `next_retry_at`.
#
# `NotificationDeliveryCreateSchema` для створення запису про спробу доставки.
# `NotificationDeliveryUpdateSchema` для оновлення статусу.
#
# Розгорнутий зв'язок `notification` в `NotificationDeliverySchema` закоментований.
#
# Все виглядає узгоджено.
# `AuditDatesSchema` надає `id, created_at, updated_at`.
# `created_at` - час створення запису про спробу доставки.
# `updated_at` - час останнього оновлення статусу.
#
# Важливо, щоб `channel_code` та `status_code` були стандартизованими (Enum або довідник).
# `recipient_address` залежить від каналу.
# `provider_response` (JSONB/Dict) для зберігання необробленої відповіді від сервісу доставки.
#
# Все виглядає добре.
