# backend/app/src/services/notifications/delivery.py
# import logging # Замінено на централізований логер
from typing import List, Optional, Dict, Any, Type
from uuid import UUID
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

# Повні шляхи імпорту
from backend.app.src.services.base import BaseService
from backend.app.src.models.notifications.notification import Notification # Модель SQLAlchemy Notification
from backend.app.src.models.notifications.delivery import NotificationDeliveryAttempt # Модель SQLAlchemy DeliveryAttempt
from backend.app.src.models.auth.user import User # Для уподобань користувача та контактних даних

from backend.app.src.services.notifications.delivery_channels import ( # Повний шлях
    ChannelSender, # Базовий клас для каналів
    EmailNotificationService,
    # SmsNotificationService, # Розкоментувати, якщо/коли реалізовано
    # PushNotificationService, # Розкоментувати, якщо/коли реалізовано
    # MessengerNotificationService, # Загальний або специфічні (Telegram, Slack...)
)
# TODO: Додати імпорти для SMS, Push, та месенджер-сервісів, коли вони будуть реалізовані в delivery_channels.py
from backend.app.src.services.integrations.telegram_service import TelegramIntegrationService # Приклад для месенджера
from backend.app.src.services.integrations.slack_service import SlackIntegrationService # Приклад для месенджера


from backend.app.src.schemas.notifications.delivery import NotificationDeliveryAttemptResponse # Схема Pydantic
from backend.app.src.config.logging import logger # Централізований логер
from backend.app.src.config import settings # Для доступу до конфігурацій (наприклад, DEBUG)

class NotificationDeliveryService(BaseService):
    """
    Сервіс, відповідальний за оркестрацію доставки сповіщень
    через різні налаштовані канали (Email, SMS, Push, Месенджери тощо).
    Логує спроби доставки та їх результати в таблицю NotificationDeliveryAttempt.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        # Словник доступних відправників по каналах.
        # Конкретні сервіси каналів (Email, SMS, Push, месенджери) повинні реалізовувати інтерфейс ChannelSender.
        self.channel_senders: Dict[str, ChannelSender] = {
            "EMAIL": EmailNotificationService(), # Припускаємо, що EmailNotificationService не потребує db_session в конструкторі
            # "SMS": SmsNotificationService(), # Розкоментувати та налаштувати, коли буде реалізовано
            # "PUSH": PushNotificationService(db_session=db_session), # Push може потребувати db_session для токенів
            # "TELEGRAM": MessengerNotificationService(TelegramIntegrationService(db_session=db_session), "TELEGRAM"), # Приклад обгортки
            # "SLACK": MessengerNotificationService(SlackIntegrationService(db_session=db_session), "SLACK"),
        }
        # TODO: Динамічно завантажувати та ініціалізувати channel_senders на основі конфігурації
        #  та доступних інтеграцій (наприклад, перевіряти наявність токенів).
        logger.info(f"NotificationDeliveryService ініціалізовано з каналами: {list(self.channel_senders.keys())}")

    async def queue_notification_for_delivery(self, notification_id: UUID, user_id: UUID) -> List[NotificationDeliveryAttemptResponse]:
        """
        Додає сповіщення в чергу для доставки (фактично, намагається доставити негайно).
        Цей метод зазвичай викликається NotificationService після створення сповіщення.

        :param notification_id: ID сповіщення для доставки.
        :param user_id: ID користувача-одержувача.
        :return: Список Pydantic схем NotificationDeliveryAttemptResponse для кожної спроби.
        """
        # В поточній реалізації цей метод є синонімом send_notification_to_user.
        # В більш складній системі тут могла б бути логіка додавання в реальну чергу (Celery, RabbitMQ).
        logger.info(f"Сповіщення ID '{notification_id}' для користувача ID '{user_id}' поставлено в чергу на доставку (негайна спроба).")
        return await self.send_notification_to_user(notification_id, user_id)


    async def send_notification_to_user(
        self,
        notification_id: UUID,
        user_id: UUID,
    ) -> List[NotificationDeliveryAttemptResponse]:
        """
        Намагається надіслати конкретне сповіщення користувачеві через відповідні канали.

        :param notification_id: ID сповіщення.
        :param user_id: ID користувача-одержувача.
        :return: Список Pydantic схем NotificationDeliveryAttemptResponse.
        """
        logger.info(f"Спроба надсилання сповіщення ID '{notification_id}' користувачу ID '{user_id}'.")

        notification_db = await self.db_session.get(Notification, notification_id, options=[selectinload(Notification.user)])
        if not notification_db:
            logger.error(f"Сповіщення ID '{notification_id}' не знайдено. Надсилання неможливе.")
            return [] # Порожній список, якщо сповіщення не знайдено

        if notification_db.user_id != user_id: # Додаткова перевірка відповідності
            logger.error(f"Невідповідність: Сповіщення ID '{notification_id}' (для користувача {notification_db.user_id}) не призначене для користувача ID '{user_id}'.")
            return []

        if not notification_db.user: # Користувач має бути завантажений через selectinload
            logger.error(f"Користувача ID '{user_id}' для сповіщення ID '{notification_id}' не знайдено (або не завантажено). Надсилання неможливе.")
            return []

        user_db = notification_db.user # Отримуємо об'єкт User з Notification

        # TODO: Визначити канали на основі `notification_db.notification_type` та уподобань користувача.
        #  Наприклад, якщо notification_type = "EMAIL_ONLY", то намагатися тільки через EMAIL.
        #  Уподобання користувача можуть зберігатися в моделі User або UserProfile.
        channels_to_try: List[str] = []
        # Приклад простої логіки вибору каналів (потрібно розширити):
        if notification_db.notification_type == "EMAIL" and user_db.email and "EMAIL" in self.channel_senders:
            channels_to_try.append("EMAIL")
        elif notification_db.notification_type == "IN_APP": # IN_APP зазвичай не потребує зовнішньої доставки
            logger.info(f"Сповіщення ID '{notification_id}' є типу IN_APP. Зовнішня доставка не потрібна.")
            # Можна створити запис DeliveryAttempt зі статусом "DELIVERED_IN_APP" або "NOT_APPLICABLE".
            return []
        # ... додати логіку для SMS, PUSH, MESSENGER_X ...
        else: # Якщо тип не специфікований або "ANY_AVAILABLE", пробуємо доступні канали
            if user_db.email and "EMAIL" in self.channel_senders: channels_to_try.append("EMAIL")
            # if user_db.phone_number and "SMS" in self.channel_senders: channels_to_try.append("SMS")
            # if user_db.has_active_push_subscriptions() and "PUSH" in self.channel_senders: channels_to_try.append("PUSH")


        if not channels_to_try:
            logger.warning(f"Не знайдено відповідних каналів або контактної інформації для користувача ID '{user_id}' для сповіщення ID '{notification_id}'.")
            # Створюємо запис про невдалу спробу, якщо канали не знайдено
            failed_attempt_no_channel = NotificationDeliveryAttempt(
                notification_id=notification_id, channel="NONE", status="FAILED",
                error_message="Не знайдено каналу або контактної інформації", # i18n
                attempt_count=1, created_at=datetime.now(timezone.utc), sent_at=datetime.now(timezone.utc)
            )
            self.db_session.add(failed_attempt_no_channel)
            await self.commit()
            return [NotificationDeliveryAttemptResponse.model_validate(failed_attempt_no_channel)]

        attempt_orm_objects: List[NotificationDeliveryAttempt] = []

        for channel_key in channels_to_try:
            sender = self.channel_senders.get(channel_key)
            if not sender: # Малоймовірно, якщо channels_to_try формується на основі self.channel_senders
                logger.error(f"Не знайдено відправника для каналу '{channel_key}'. Пропуск.")
                continue

            logger.debug(f"Спроба доставки сповіщення ID '{notification_id}' користувачу ID '{user_id}' через канал '{channel_key}'.")

            # Створюємо запис спроби зі статусом PENDING
            attempt_db = NotificationDeliveryAttempt(
                notification_id=notification_id, channel=channel_key, status="PENDING", attempt_count=1
                # created_at встановлюється автоматично
            )
            self.db_session.add(attempt_db)
            attempt_orm_objects.append(attempt_db) # Зберігаємо для подальшого оновлення

        await self.db_session.flush(attempt_orm_objects) # Отримуємо ID для записів спроб

        # Виконуємо надсилання для кожного створеного запису спроби
        for attempt_db in attempt_orm_objects:
            sender = self.channel_senders[attempt_db.channel] # Отримуємо відправника знову
            try:
                # `send` має повернути словник зі статусом та опціонально message_id/error
                send_result = await sender.send(user_to_notify=user_db, notification_content=notification_db)

                attempt_db.status = str(send_result.get("status", "FAILED")).upper()
                attempt_db.external_message_id = send_result.get("message_id")
                attempt_db.sent_at = datetime.now(timezone.utc) # Час завершення спроби
                if attempt_db.status == "FAILED":
                    attempt_db.error_message = str(send_result.get("error", "Невідома помилка надсилання")) # i18n
                logger.info(f"Спроба доставки ID '{attempt_db.id}' для сповіщення ID '{notification_id}' через {attempt_db.channel}: Статус {attempt_db.status}, ID Повід.: {attempt_db.external_message_id}")
            except Exception as e:
                logger.error(f"Виняток під час спроби надсилання ID '{attempt_db.id}' для сповіщення '{notification_id}' через {attempt_db.channel}: {e}", exc_info=True)
                attempt_db.status = "FAILED"
                attempt_db.error_message = str(e)
                attempt_db.sent_at = datetime.now(timezone.utc)
            self.db_session.add(attempt_db) # Додаємо оновлений запис до сесії

        try:
            await self.commit() # Зберігаємо всі оновлені статуси спроб
            # Оновлюємо об'єкти з БД для консистентної відповіді (необов'язково, якщо model_validate працює з поточним станом сесії)
            for att_db in attempt_orm_objects: await self.db_session.refresh(att_db)
        except Exception as e:
            await self.rollback()
            logger.error(f"Помилка коміту спроб доставки для сповіщення ID '{notification_id}': {e}", exc_info=settings.DEBUG)
            return [] # Повертаємо порожній список у разі помилки коміту

        logger.info(f"Завершено всі спроби доставки для сповіщення ID '{notification_id}' користувачу ID '{user_id}'. {len(attempt_orm_objects)} спроб оброблено.")
        return [NotificationDeliveryAttemptResponse.model_validate(att) for att in attempt_orm_objects] # Pydantic v2

    async def retry_failed_delivery_attempts(self, max_attempts: int = 3, age_threshold_hours: int = 24) -> int:
        """
        Повторює невдалі спроби доставки, які не перевищили максимальну кількість спроб
        та є достатньо новими.
        """
        logger.info(f"Повторна спроба невдалих доставок (макс. спроб={max_attempts}, поріг віку={age_threshold_hours} год).")

        threshold_time = datetime.now(timezone.utc) - timedelta(hours=age_threshold_hours)

        # Обираємо невдалі спроби, що відповідають критеріям
        stmt = select(NotificationDeliveryAttempt).options(
            selectinload(NotificationDeliveryAttempt.notification).options(
                selectinload(Notification.user).options(selectinload(User.user_type)) # Потрібен user для send()
            )
        ).where(
            NotificationDeliveryAttempt.status.in_(["FAILED", "RETRY_SCHEDULED"]), # Можливо, є статус для запланованих повторів
            NotificationDeliveryAttempt.attempt_count < max_attempts,
            NotificationDeliveryAttempt.created_at >= threshold_time # Обробляємо тільки відносно нові
        ).order_by(NotificationDeliveryAttempt.created_at) # Обробляємо старіші спочатку

        failed_attempts_db = (await self.db_session.execute(stmt)).scalars().all()

        retried_success_count = 0
        if not failed_attempts_db:
            logger.info("Не знайдено невдалих спроб доставки, що відповідають критеріям для повтору.")
            return 0

        for attempt in failed_attempts_db:
            if not attempt.notification or not attempt.notification.user:
                logger.warning(f"Пропуск повтору для спроби ID {attempt.id}: відсутні дані сповіщення або користувача.")
                attempt.status = "FAILED_PERMANENTLY" # Або інший кінцевий статус
                attempt.error_message = "Відсутні дані для повтору" # i18n
                self.db_session.add(attempt)
                continue

            logger.info(f"Повторна спроба доставки для сповіщення ID '{attempt.notification_id}' (Спроба ID: {attempt.id}) користувачу ID '{attempt.notification.user.id}' через канал '{attempt.channel}'. Попередніх спроб: {attempt.attempt_count}.")

            sender = self.channel_senders.get(attempt.channel)
            if not sender:
                logger.error(f"Немає відправника для каналу '{attempt.channel}' спроби ID {attempt.id}. Повтор неможливий.")
                attempt.status = "FAILED_PERMANENTLY" # Помилка конфігурації
                attempt.error_message = f"Відправник для каналу '{attempt.channel}' не знайдено" # i18n
                self.db_session.add(attempt)
                continue

            # Створюємо НОВИЙ запис спроби для цього повтору
            new_retry_attempt_db = NotificationDeliveryAttempt(
                notification_id=attempt.notification_id,
                channel=attempt.channel,
                status="PENDING", # Нова спроба починається як PENDING
                attempt_count=attempt.attempt_count + 1,
                # previous_attempt_id=attempt.id # Опціонально: посилання на попередню спробу, якщо модель підтримує
            )
            self.db_session.add(new_retry_attempt_db)
            await self.db_session.flush([new_retry_attempt_db]) # Отримуємо ID для new_retry_attempt_db

            try:
                send_result = await sender.send(user_to_notify=attempt.notification.user, notification_content=attempt.notification)
                new_retry_attempt_db.status = str(send_result.get("status", "FAILED")).upper()
                new_retry_attempt_db.external_message_id = send_result.get("message_id")
                new_retry_attempt_db.sent_at = datetime.now(timezone.utc)
                if new_retry_attempt_db.status == "FAILED":
                    new_retry_attempt_db.error_message = str(send_result.get("error", "Помилка повторної відправки")) # i18n
                else: # Успішний повтор
                    retried_success_count +=1
                logger.info(f"Результат повторної спроби {new_retry_attempt_db.attempt_count} для Сповіщ. ID '{attempt.notification_id}' через {attempt.channel}: Статус {new_retry_attempt_db.status}")
            except Exception as e:
                logger.error(f"Виняток під час повторного надсилання для Сповіщ. ID '{attempt.notification_id}' через {attempt.channel}: {e}", exc_info=True)
                new_retry_attempt_db.status = "FAILED"
                new_retry_attempt_db.error_message = str(e)
                new_retry_attempt_db.sent_at = datetime.now(timezone.utc)

            self.db_session.add(new_retry_attempt_db)

            # Оновлюємо стару спробу, щоб не вибирати її знову
            if new_retry_attempt_db.status == "SUCCESS":
                attempt.status = "RETRY_SUCCESS" # Стара спроба успішно повторена
            elif new_retry_attempt_db.attempt_count >= max_attempts:
                attempt.status = "FAILED_MAX_ATTEMPTS" # Досягнуто макс. кількості повторів
            else:
                attempt.status = "RETRY_INITIATED" # Заплановано наступний повтор (або цей був невдалий)
            self.db_session.add(attempt)

        if failed_attempts_db: # Якщо були спроби для обробки
            await self.commit()
            logger.info(f"Оброблено {len(failed_attempts_db)} невдалих спроб доставки. Успішних повторів: {retried_success_count}.")

        return retried_success_count # Повертаємо кількість успішних повторів

    async def list_delivery_attempts_for_notification(
        self, notification_id: UUID, skip: int = 0, limit: int = 10
    ) -> List[NotificationDeliveryAttemptResponse]:
        """Перелічує всі спроби доставки для конкретного сповіщення."""
        logger.debug(f"Перелік спроб доставки для сповіщення ID: {notification_id}")
        stmt = select(NotificationDeliveryAttempt).options(
            selectinload(NotificationDeliveryAttempt.notification) # Завантажуємо саме сповіщення
        ).where(NotificationDeliveryAttempt.notification_id == notification_id) \
         .order_by(NotificationDeliveryAttempt.created_at.desc()).offset(skip).limit(limit)

        attempts_db = (await self.db_session.execute(stmt)).scalars().all() # unique() тут не потрібен, бо це не join на той самий рівень

        response_list = [NotificationDeliveryAttemptResponse.model_validate(att) for att in attempts_db] # Pydantic v2
        logger.info(f"Отримано {len(response_list)} спроб доставки для сповіщення ID '{notification_id}'.")
        return response_list

logger.debug(f"{NotificationDeliveryService.__name__} (сервіс доставки сповіщень) успішно визначено.")
