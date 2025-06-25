# backend/app/src/models/notifications/delivery.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `NotificationDeliveryModel` для відстеження
статусу доставки сповіщень (`NotificationModel`) через різні канали
(наприклад, email, SMS, push-сповіщення, месенджери).
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean # type: ignore
from sqlalchemy.dialects.postgresql import UUID, JSONB # type: ignore
from sqlalchemy.orm import relationship # type: ignore
import uuid # Для роботи з UUID
from datetime import datetime # Для роботи з датами та часом

from backend.app.src.models.base import BaseModel # Використовуємо BaseModel

class NotificationDeliveryModel(BaseModel):
    """
    Модель для відстеження статусу доставки сповіщень.
    Кожен запис представляє спробу доставки одного сповіщення через один канал.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор запису доставки (успадковано).
        notification_id (uuid.UUID): Ідентифікатор сповіщення, яке доставляється.
        channel_code (str): Код каналу доставки (наприклад, "EMAIL", "SMS", "FIREBASE_PUSH", "TELEGRAM").
                            TODO: Визначити Enum або довідник для каналів.
        recipient_address (str): Адреса отримувача для цього каналу (наприклад, email-адреса, номер телефону, device_token).

        status_code (str): Статус доставки (наприклад, "PENDING", "SENT", "DELIVERED", "FAILED", "OPENED", "CLICKED").
                           TODO: Визначити Enum або довідник для статусів доставки.
        status_message (Text | None): Деталі статусу або повідомлення про помилку від провайдера.

        sent_at (datetime | None): Час, коли сповіщення було надіслано через цей канал.
        delivered_at (datetime | None): Час, коли сповіщення було доставлено (якщо провайдер надає таку інформацію).
        # opened_at (datetime | None): Час, коли сповіщення було відкрито (для email, push).
        # clicked_at (datetime | None): Час, коли було здійснено клік по посиланню в сповіщенні.

        # Інформація від провайдера доставки
        provider_message_id (str | None): Ідентифікатор повідомлення від зовнішнього провайдера (наприклад, SendGrid Message ID).
        provider_response (JSONB | None): Повна відповідь від провайдера.

        # Лічильники спроб
        attempt_count (int): Кількість спроб доставки.
        next_retry_at (datetime | None): Час наступної спроби (якщо доставка не вдалася і планується повторна спроба).

        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення статусу (успадковано).

    Зв'язки:
        notification (relationship): Зв'язок з NotificationModel.
    """
    __tablename__ = "notification_deliveries"

    notification_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False, index=True)

    # Канал доставки (EMAIL, SMS, PUSH_FIREBASE, PUSH_APNS, TELEGRAM_BOT, SLACK, etc.)
    # TODO: Створити Enum або довідник для NotificationChannel.
    channel_code: Column[str] = Column(String(50), nullable=False, index=True)

    # Адреса/ідентифікатор отримувача для цього каналу.
    # Наприклад, email, номер телефону, FCM token, Telegram chat_id.
    recipient_address: Column[str] = Column(String(512), nullable=False) # 512 для довгих токенів

    # Статус доставки.
    # TODO: Створити Enum або довідник для NotificationDeliveryStatus.
    # Приклади: 'PENDING', 'PROCESSING', 'SENT', 'DELIVERED', 'FAILED', 'RETRYING', 'OPENED', 'CLICKED', 'UNSUBSCRIBED'.
    status_code: Column[str] = Column(String(50), nullable=False, default="PENDING", index=True)
    status_message: Column[str | None] = Column(Text, nullable=True) # Повідомлення про помилку або деталі статусу

    sent_at: Column[DateTime | None] = Column(DateTime(timezone=True), nullable=True)
    delivered_at: Column[DateTime | None] = Column(DateTime(timezone=True), nullable=True)
    # opened_at: Column[DateTime | None] = Column(DateTime(timezone=True), nullable=True)
    # clicked_at: Column[DateTime | None] = Column(DateTime(timezone=True), nullable=True)

    provider_message_id: Column[str | None] = Column(String(255), nullable=True, index=True)
    provider_response: Column[JSONB | None] = Column(JSONB, nullable=True) # Повна відповідь від сервісу доставки

    attempt_count: Column[int] = Column(Integer, default=0, nullable=False)
    next_retry_at: Column[DateTime | None] = Column(DateTime(timezone=True), nullable=True, index=True)


    # --- Зв'язки (Relationships) ---
    notification = relationship("NotificationModel", back_populates="deliveries")


    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі NotificationDeliveryModel.
        """
        return f"<{self.__class__.__name__}(id='{self.id}', notification_id='{self.notification_id}', channel='{self.channel_code}', status='{self.status_code}')>"

# TODO: Перевірити відповідність `technical-task.md`.
# - "Можливість сповіщень через месенджери (Telegram/Viber/Slack/Teams/WhatsApp та інші)"
#   - Ця модель дозволяє відстежувати доставку через різні канали, включаючи месенджери.
#   - Кожен канал матиме свій `channel_code`.
# - "Firebase Cloud Messaging", "Android та Apple Push Notification service"
#   - Це також канали доставки, які будуть тут представлені.

# TODO: Узгодити назву таблиці `notification_deliveries` з `structure-claude-v3.md`. Відповідає.
# Використання `BaseModel` як основи.
# Ключові поля: `notification_id`, `channel_code`, `recipient_address`, `status_code`.
# Додаткові поля для деталей доставки та повторних спроб.
# `ondelete="CASCADE"` для `notification_id`.
# Зв'язок з `NotificationModel` визначено.
# Все виглядає логічно для відстеження процесу доставки.
# `recipient_address` важливий, оскільки для різних каналів у одного користувача можуть бути різні адреси/токени.
# `status_code` має бути стандартизованим (через Enum/довідник).
# `provider_message_id` та `provider_response` корисні для інтеграції з зовнішніми сервісами доставки.
# `attempt_count` та `next_retry_at` для реалізації механізму повторних спроб.
# Поля `opened_at` та `clicked_at` можуть бути додані, якщо є можливість відстежувати такі події
# (наприклад, через пікселі відстеження в email або колбеки від push-сервісів).
# Поки що закоментовані для спрощення.
# `updated_at` буде оновлюватися при зміні статусу доставки.
# `created_at` - час створення запиту на доставку.
# `sent_at` та `delivered_at` - фактичний час відправки та доставки.
