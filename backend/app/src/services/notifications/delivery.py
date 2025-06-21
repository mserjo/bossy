# backend/app/src/services/notifications/delivery.py
from typing import List, Optional, Dict, Any # Type видалено
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select # sqlalchemy.future тепер select
from sqlalchemy.orm import selectinload

from backend.app.src.services.base import BaseService
from backend.app.src.models.notifications.notification import Notification
from backend.app.src.models.notifications.delivery import NotificationDeliveryAttempt
from backend.app.src.repositories.notifications.delivery_attempt_repository import NotificationDeliveryAttemptRepository # Імпорт репозиторію
from backend.app.src.models.auth.user import User

from backend.app.src.services.notifications.delivery_channels import (
    ChannelSender,
    EmailNotificationService,
)
from backend.app.src.services.integrations.telegram_service import TelegramIntegrationService
from backend.app.src.services.integrations.slack_service import SlackIntegrationService

from backend.app.src.schemas.notifications.delivery import (
    NotificationDeliveryAttemptResponse,
    NotificationDeliveryAttemptCreateSchema
)
from backend.app.src.core.dicts import NotificationChannelType, DeliveryStatusType, NotificationType # Імпорт Enum
from backend.app.src.config import settings
from backend.app.src.config.logging import get_logger
from backend.app.src.core.i18n import _
logger = get_logger(__name__)


class NotificationDeliveryService(BaseService):
    """
    Сервіс, відповідальний за оркестрацію доставки сповіщень
    через різні налаштовані канали (Email, SMS, Push, Месенджери тощо).
    Логує спроби доставки та їх результати в таблицю NotificationDeliveryAttempt.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        self.attempt_repo = NotificationDeliveryAttemptRepository() # Ініціалізація репозиторію
        self.channel_senders: Dict[NotificationChannelType, ChannelSender] = { # Ключ тепер NotificationChannelType
            NotificationChannelType.EMAIL: EmailNotificationService(),
            # TODO: Додати інші канали аналогічно
        }
        logger.info(f"NotificationDeliveryService ініціалізовано з каналами: {[ch.value for ch in self.channel_senders.keys()]}")

    async def queue_notification_for_delivery(self, notification_id: int, user_id: int) -> List[ # Змінено UUID на int
        NotificationDeliveryAttemptResponse]:
        """
        Додає сповіщення в чергу для доставки (фактично, намагається доставити негайно).
        Цей метод зазвичай викликається NotificationService після створення сповіщення.
        """
        logger.info(
            f"Сповіщення ID '{notification_id}' для користувача ID '{user_id}' поставлено в чергу на доставку (негайна спроба).")
        return await self.send_notification_to_user(notification_id, user_id)

    async def send_notification_to_user(
            self,
            notification_id: int, # Змінено UUID на int
            user_id: int, # Змінено UUID на int
    ) -> List[NotificationDeliveryAttemptResponse]:
        """
        Намагається надіслати конкретне сповіщення користувачеві через відповідні канали.
        """
        logger.info(f"Спроба надсилання сповіщення ID '{notification_id}' користувачу ID '{user_id}'.")

        # Завантажуємо сповіщення та пов'язаного користувача
        notification_db = await self.db_session.get(Notification, notification_id, options=[selectinload(Notification.user).options(selectinload(User.user_type))])
        if not notification_db:
            logger.error(f"Сповіщення ID '{notification_id}' не знайдено. Надсилання неможливе.")
            return []

        if notification_db.user_id != user_id:
            logger.error(
                f"Невідповідність: Сповіщення ID '{notification_id}' (для користувача {notification_db.user_id}) не призначене для користувача ID '{user_id}'.")
            return []

        if not notification_db.user:
            logger.error(
                f"Користувача ID '{user_id}' для сповіщення ID '{notification_id}' не знайдено. Надсилання неможливе.")
            return []
        user_db = notification_db.user

        channels_to_try: List[NotificationChannelType] = []
        # Використовуємо NotificationType Enum
        if notification_db.notification_type == NotificationType.EMAIL_ONLY and user_db.email and NotificationChannelType.EMAIL in self.channel_senders:
            channels_to_try.append(NotificationChannelType.EMAIL)
        elif notification_db.notification_type == NotificationType.IN_APP:
            logger.info(f"Сповіщення ID '{notification_id}' є типу IN_APP. Зовнішня доставка не потрібна.")
            # Можна створити запис DeliveryAttempt зі статусом DELIVERED_IN_APP
            # Для цього потрібно визначити такий статус в DeliveryStatusType Enum
            # Або просто повернути порожній список, якщо IN_APP не логується як спроба доставки.
            return []
        else: # ANY_AVAILABLE або інші типи, що потребують перебору каналів
            if user_db.email and NotificationChannelType.EMAIL in self.channel_senders:
                channels_to_try.append(NotificationChannelType.EMAIL)
            # Додати логіку для SMS, PUSH, MESSENGER_X, використовуючи NotificationChannelType Enum

        if not channels_to_try:
            logger.warning(
                f"Не знайдено відповідних каналів або контактної інформації для користувача ID '{user_id}' для сповіщення ID '{notification_id}'.")
            attempt_create_schema = NotificationDeliveryAttemptCreateSchema(
                notification_id=notification_id,
                channel=NotificationChannelType.UNKNOWN,
                status=DeliveryStatusType.FAILED,
                error_message=_("notification.delivery.errors.no_channel_or_contact"),
                attempt_count=1,
            )
            failed_attempt_db = await self.attempt_repo.create(session=self.db_session, obj_in=attempt_create_schema)
            await self.commit()
            return [NotificationDeliveryAttemptResponse.model_validate(failed_attempt_db)]

        attempt_orm_objects: List[NotificationDeliveryAttempt] = []
        created_attempt_ids: List[int] = []

        for channel_enum in channels_to_try:
            sender = self.channel_senders.get(channel_enum)
            if not sender:
                logger.error(f"Не знайдено відправника для каналу '{channel_enum.value}'. Пропуск.")
                continue

            logger.debug(
                f"Спроба доставки сповіщення ID '{notification_id}' користувачу ID '{user_id}' через канал '{channel_enum.value}'.")

            attempt_create_data = NotificationDeliveryAttemptCreateSchema(
                notification_id=notification_id,
                channel=channel_enum, # Використовуємо Enum
                status=DeliveryStatusType.PENDING, # Використовуємо Enum
                attempt_count=1
            )
            attempt_db = await self.attempt_repo.create(session=self.db_session, obj_in=attempt_create_data)
            attempt_orm_objects.append(attempt_db)

        await self.db_session.flush([att for att in attempt_orm_objects if att is not None])
        for att_db in attempt_orm_objects:
            if att_db and att_db.id is not None: # Перевірка, що ID було встановлено
                 created_attempt_ids.append(att_db.id)


        updated_attempts: List[NotificationDeliveryAttempt] = []
        for attempt_id in created_attempt_ids: # Використовуємо ID для отримання свіжих об'єктів
            current_attempt_db = await self.attempt_repo.get(session=self.db_session, id=attempt_id)
            if not current_attempt_db: continue # Малоймовірно

            sender = self.channel_senders[current_attempt_db.channel] # Отримуємо Enum з об'єкта
            try:
                send_result = await sender.send(user_to_notify=user_db, notification_content=notification_db)

                current_attempt_db.status = DeliveryStatusType(str(send_result.get("status", "FAILED")).upper())
                current_attempt_db.external_message_id = send_result.get("message_id")
                current_attempt_db.sent_at = datetime.now(timezone.utc)
                if current_attempt_db.status == DeliveryStatusType.FAILED:
                    error_detail = send_result.get("error")
                    current_attempt_db.error_message = str(error_detail) if error_detail else _("notification.delivery.errors.send_unknown_error")
                logger.info(
                    f"Спроба доставки ID '{current_attempt_db.id}' для сповіщення ID '{notification_id}' через {current_attempt_db.channel.value}: Статус {current_attempt_db.status.value}, ID Повід.: {current_attempt_db.external_message_id}")
            except Exception as e:
                logger.error(
                    f"Виняток під час спроби надсилання ID '{current_attempt_db.id}' для сповіщення '{notification_id}' через {current_attempt_db.channel.value}: {e}",
                    exc_info=True)
                current_attempt_db.status = DeliveryStatusType.FAILED
                current_attempt_db.error_message = _("notification.delivery.errors.send_exception_on_channel", channel_name=current_attempt_db.channel.value ,details=str(e))
                current_attempt_db.sent_at = datetime.now(timezone.utc)

            # Оновлюємо через репозиторій, якщо схема оновлення дозволяє ці поля.
            # Або оновлюємо напряму і робимо add. Поки що напряму.
            self.db_session.add(current_attempt_db)
            updated_attempts.append(current_attempt_db)

        try:
            await self.commit()
            for att_db in updated_attempts: await self.db_session.refresh(att_db)
        except Exception as e:
            await self.rollback()
            logger.error(f"Помилка коміту спроб доставки для сповіщення ID '{notification_id}': {e}",
                         exc_info=settings.DEBUG)
            return []

        logger.info(
            f"Завершено всі спроби доставки для сповіщення ID '{notification_id}' користувачу ID '{user_id}'. {len(updated_attempts)} спроб оброблено.")
        return [NotificationDeliveryAttemptResponse.model_validate(att) for att in updated_attempts]

    async def retry_failed_delivery_attempts(self, max_attempts: int = 3, age_threshold_hours: int = 24) -> int:
        """
        Повторює невдалі спроби доставки, які не перевищили максимальну кількість спроб
        та є достатньо новими.
        """
        logger.info(
            f"Повторна спроба невдалих доставок (макс. спроб={max_attempts}, поріг віку={age_threshold_hours} год).")

        age_threshold_dt = datetime.now(timezone.utc) - timedelta(hours=age_threshold_hours)

        # Використовуємо метод репозиторію для отримання спроб
        failed_attempts_db_list, _ = await self.attempt_repo.list_retryable_attempts(
            session=self.db_session,
            max_attempts=max_attempts,
            age_threshold=age_threshold_dt,
            with_relations=True, # Потрібні зв'язки для notification.user
            limit=settings.RETRY_DELIVERY_BATCH_SIZE # Обмежуємо кількість за один раз
        )

        retried_success_count = 0
        if not failed_attempts_db_list:
            logger.info("Не знайдено невдалих спроб доставки, що відповідають критеріям для повтору.")
            return 0

        for attempt in failed_attempts_db_list:
            if not attempt.notification or not attempt.notification.user:
                logger.warning(f"Пропуск повтору для спроби ID {attempt.id}: відсутні дані сповіщення або користувача.")
                attempt.status = DeliveryStatusType.FAILED_PERMANENTLY
                attempt.error_message = _("notification.delivery.errors.retry_missing_data")
                self.db_session.add(attempt) # Оновлюємо стару спробу
                continue

            logger.info(
                f"Повторна спроба доставки для сповіщення ID '{attempt.notification_id}' (Спроба ID: {attempt.id}) користувачу ID '{attempt.notification.user.id}' через канал '{attempt.channel.value}'. Попередніх спроб: {attempt.attempt_count}.")

            sender = self.channel_senders.get(attempt.channel) # channel тепер Enum
            if not sender:
                logger.error(
                    f"Немає відправника для каналу '{attempt.channel.value}' спроби ID {attempt.id}. Повтор неможливий.")
                attempt.status = DeliveryStatusType.FAILED_PERMANENTLY
                attempt.error_message = _("notification.delivery.errors.retry_sender_not_found", channel=attempt.channel.value)
                self.db_session.add(attempt)
                continue

            # Створюємо НОВИЙ запис спроби для цього повтору
            new_retry_create_schema = NotificationDeliveryAttemptCreateSchema(
                notification_id=attempt.notification_id,
                channel=attempt.channel, # Enum
                status=DeliveryStatusType.PENDING, # Enum
                attempt_count=attempt.attempt_count + 1,
                # previous_attempt_id=attempt.id # Якщо модель підтримує
            )
            new_retry_attempt_db = await self.attempt_repo.create(session=self.db_session, obj_in=new_retry_create_schema)
            await self.db_session.flush([new_retry_attempt_db]) # Отримуємо ID

            try:
                send_result = await sender.send(user_to_notify=attempt.notification.user,
                                                notification_content=attempt.notification)

                new_retry_attempt_db.status = DeliveryStatusType(str(send_result.get("status", "FAILED")).upper())
                new_retry_attempt_db.external_message_id = send_result.get("message_id")
                new_retry_attempt_db.sent_at = datetime.now(timezone.utc)
                if new_retry_attempt_db.status == DeliveryStatusType.FAILED:
                    error_detail = send_result.get("error")
                    new_retry_attempt_db.error_message = str(error_detail) if error_detail else _("notification.delivery.errors.retry_send_unknown_error")
                else:
                    retried_success_count += 1
                logger.info(
                    f"Результат повторної спроби {new_retry_attempt_db.attempt_count} для Сповіщ. ID '{attempt.notification_id}' через {attempt.channel.value}: Статус {new_retry_attempt_db.status.value}")
            except Exception as e:
                logger.error(
                    f"Виняток під час повторного надсилання для Сповіщ. ID '{attempt.notification_id}' через {attempt.channel.value}: {e}",
                    exc_info=True)
                new_retry_attempt_db.status = DeliveryStatusType.FAILED
                new_retry_attempt_db.error_message = _("notification.delivery.errors.retry_exception_on_channel", channel_name=attempt.channel.value, details=str(e))
                new_retry_attempt_db.sent_at = datetime.now(timezone.utc)

            self.db_session.add(new_retry_attempt_db) # Додаємо оновлену нову спробу

            # Оновлюємо стару спробу
            if new_retry_attempt_db.status == DeliveryStatusType.SUCCESS:
                attempt.status = DeliveryStatusType.RETRY_SUCCESS
            elif new_retry_attempt_db.attempt_count >= max_attempts:
                attempt.status = DeliveryStatusType.FAILED_MAX_ATTEMPTS
            else:
                attempt.status = DeliveryStatusType.RETRY_INITIATED
            self.db_session.add(attempt)

        if failed_attempts_db_list:
            await self.commit()
            logger.info(
                f"Оброблено {len(failed_attempts_db_list)} невдалих спроб доставки. Успішних повторів: {retried_success_count}.")

        return retried_success_count

    async def list_delivery_attempts_for_notification(
            self, notification_id: int, skip: int = 0, limit: int = 10 # Змінено UUID на int
    ) -> List[NotificationDeliveryAttemptResponse]:
        """Перелічує всі спроби доставки для конкретного сповіщення."""
        logger.debug(f"Перелік спроб доставки для сповіщення ID: {notification_id}")
        stmt = select(NotificationDeliveryAttempt).options(
            selectinload(NotificationDeliveryAttempt.notification)  # Завантажуємо саме сповіщення
        ).where(NotificationDeliveryAttempt.notification_id == notification_id) \
            .order_by(NotificationDeliveryAttempt.created_at.desc()).offset(skip).limit(limit)

        attempts_db = (await self.db_session.execute(
            stmt)).scalars().all()  # unique() тут не потрібен, бо це не join на той самий рівень

        response_list = [NotificationDeliveryAttemptResponse.model_validate(att) for att in attempts_db]  # Pydantic v2
        logger.info(f"Отримано {len(response_list)} спроб доставки для сповіщення ID '{notification_id}'.")
        return response_list


logger.debug(f"{NotificationDeliveryService.__name__} (сервіс доставки сповіщень) успішно визначено.")
