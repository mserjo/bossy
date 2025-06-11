# backend/app/src/services/notifications/delivery_channels.py
# import logging # Замінено на централізований логер
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from uuid import uuid4

# Повні шляхи імпорту
from backend.app.src.models.auth.user import User # Для деталей користувача (email, телефон)
from backend.app.src.models.notifications.notification import Notification # Вміст сповіщення
from backend.app.src.config.settings import settings # Для ключів API, налаштувань SMTP тощо
from backend.app.src.config.logging import logger # Централізований логер

# TODO: Додати імпорти для конкретних SDK/бібліотек каналів, коли буде реалізовано
# Наприклад:
# import aiosmtplib # для Email
# from twilio.rest import Client as TwilioClient # для SMS (потребує асинхронного аналога або запуску в executor)
# from firebase_admin.messaging import Message as FirebaseMessage, send # для FCM Push
# from backend.app.src.services.integrations.telegram_service import TelegramIntegrationService
# from backend.app.src.services.integrations.slack_service import SlackIntegrationService
# from backend.app.src.services.integrations.messenger_base import MessageSendCommand, MessengerMessage


class ChannelSender(ABC):
    """
    Абстрактний базовий клас для відправників сповіщень по каналах.
    Визначає інтерфейс для надсилання сповіщення через конкретний канал.
    """
    channel_type: str # Має бути визначено в підкласах (наприклад, "EMAIL", "SMS")

    @abstractmethod
    async def send(
        self,
        user_to_notify: User,
        notification_content: Notification,
    ) -> Dict[str, Any]:
        """
        Надсилає сповіщення.

        :param user_to_notify: Об'єкт користувача-одержувача.
        :param notification_content: Об'єкт сповіщення, що містить заголовок, повідомлення тощо.
        :return: Словник, що містить:
            - "status": "success" або "failed" (успішно/невдача) # i18n
            - "message_id": Опціональний зовнішній ID повідомлення від провайдера.
            - "error": Опціональне повідомлення про помилку, якщо невдача.
            - "channel_type": Тип використаного каналу (має відповідати self.channel_type).
        :raises NotImplementedError: Якщо метод не реалізовано.
        """
        # i18n
        raise NotImplementedError(f"Метод 'send' не реалізовано для каналу '{getattr(self, 'channel_type', 'НевідомийКанал')}'")


class EmailNotificationService(ChannelSender):
    """
    Обробляє надсилання сповіщень електронною поштою.
    Фактична логіка надсилання email є заглушкою.
    """
    channel_type = "EMAIL"

    def __init__(self):
        # TODO: Ініціалізувати SMTP клієнт або клієнт стороннього сервісу (SendGrid, Mailgun)
        # self.smtp_server = getattr(settings, 'SMTP_SERVER', None)
        # self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        # self.smtp_user = getattr(settings, 'SMTP_USER', None)
        # self.smtp_password = getattr(settings, 'SMTP_PASSWORD', None)
        # self.smtp_sender_email = getattr(settings, 'SMTP_SENDER_EMAIL', 'noreply@example.com')
        logger.info(f"{self.channel_type} сервіс ініціалізовано (заглушка).")

    async def send(
        self, user_to_notify: User, notification_content: Notification,
    ) -> Dict[str, Any]:
        recipient_email = getattr(user_to_notify, 'email', None)
        if not recipient_email:
            msg = f"У користувача ID '{user_to_notify.id}' відсутня адреса ел. пошти. Неможливо надіслати email ID '{notification_content.id}'." # i18n
            logger.warning(msg)
            return {"status": "failed", "error": msg, "channel_type": self.channel_type}

        subject = notification_content.title or "Сповіщення системи" # i18n
        body = notification_content.message

        # TODO: Реалізувати фактичне надсилання email за допомогою aiosmtplib або SDK.
        # Наприклад:
        # try:
        #     message = EmailMessage()
        #     message["From"] = self.smtp_sender_email
        #     message["To"] = recipient_email
        #     message["Subject"] = subject
        #     message.set_content(body) # Для простого тексту
        #     # Для HTML: message.add_alternative(html_body, subtype='html')
        #
        #     async with SMTPClient(hostname=self.smtp_server, port=self.smtp_port) as client:
        #         await client.login(self.smtp_user, self.smtp_password)
        #         await client.send_message(message)
        #     message_id = message.get("Message-ID", f"mock_email_id_{uuid4()}")
        #     logger.info(f"Email успішно надіслано до {recipient_email} для сповіщення ID '{notification_content.id}'.")
        #     return {"status": "success", "message_id": message_id, "channel_type": self.channel_type}
        # except Exception as e:
        #     logger.error(f"Помилка надсилання EMAIL для сповіщення ID '{notification_content.id}': {e}", exc_info=True)
        #     return {"status": "failed", "error": str(e), "channel_type": self.channel_type}

        message_id = f"placeholder_email_msg_id_{notification_content.id}_{uuid4()}"
        logger.info(f"[ЗАГЛУШКА] Надсилання EMAIL сповіщення ID '{notification_content.id}':")
        logger.info(f"  Кому: {recipient_email} (Користувач: {getattr(user_to_notify, 'username', user_to_notify.id)})")
        logger.info(f"  Тема: {subject}")
        logger.info(f"  Тіло: {body[:100]}...")
        logger.info(f"  Email надіслано (симуляція). ID Повідомлення: {message_id}")
        # i18n
        return {"status": "success", "message_id": message_id, "error": None, "channel_type": self.channel_type}


class SmsNotificationService(ChannelSender):
    """
    Обробляє надсилання сповіщень через SMS.
    Фактична логіка надсилання SMS є заглушкою.
    """
    channel_type = "SMS"

    def __init__(self):
        # TODO: Ініціалізувати клієнт SMS-шлюзу (Twilio, Vonage, etc.)
        # self.sms_gateway_sid = getattr(settings, 'SMS_GATEWAY_SID', None)
        # self.sms_gateway_token = getattr(settings, 'SMS_GATEWAY_AUTH_TOKEN', None)
        # self.sms_sender_phone = getattr(settings, 'SMS_SENDER_PHONE', None)
        logger.info(f"{self.channel_type} сервіс ініціалізовано (заглушка).")

    async def send(
        self, user_to_notify: User, notification_content: Notification,
    ) -> Dict[str, Any]:
        phone_number = getattr(user_to_notify, 'phone_number', None)
        if not phone_number:
            msg = f"У користувача ID '{user_to_notify.id}' відсутній номер телефону. Неможливо надіслати SMS ID '{notification_content.id}'." # i18n
            logger.warning(msg)
            return {"status": "failed", "error": msg, "channel_type": self.channel_type}

        sms_text = f"{notification_content.title}: {notification_content.message}"
        # TODO: Перевірити максимальну довжину SMS та правила конкатенації для конкретного шлюзу.
        max_sms_length = 160 # Стандартна довжина одного SMS
        if len(sms_text) > max_sms_length:
            sms_text = sms_text[:max_sms_length-3] + "..."
            logger.warning(f"Текст SMS для сповіщення ID '{notification_content.id}' було скорочено до {max_sms_length} символів.")

        # TODO: Реалізувати фактичне надсилання SMS через API шлюзу.
        # try:
        #     # client = TwilioClient(self.sms_gateway_sid, self.sms_gateway_token)
        #     # message = client.messages.create(to=phone_number, from_=self.sms_sender_phone, body=sms_text)
        #     # message_id = message.sid
        #     message_id = f"placeholder_sms_msg_id_{notification_content.id}_{uuid4()}" # Заглушка
        #     logger.info(f"SMS успішно надіслано на {phone_number} для сповіщення ID '{notification_content.id}'.")
        #     return {"status": "success", "message_id": message_id, "channel_type": self.channel_type}
        # except Exception as e:
        #     logger.error(f"Помилка надсилання SMS для сповіщення ID '{notification_content.id}': {e}", exc_info=True)
        #     return {"status": "failed", "error": str(e), "channel_type": self.channel_type}

        message_id = f"placeholder_sms_msg_id_{notification_content.id}_{uuid4()}"
        logger.info(f"[ЗАГЛУШКА] Надсилання SMS сповіщення ID '{notification_content.id}':")
        logger.info(f"  Кому: {phone_number} (Користувач: {getattr(user_to_notify, 'username', user_to_notify.id)})")
        logger.info(f"  Текст: {sms_text}")
        logger.info(f"  SMS надіслано (симуляція). ID Повідомлення: {message_id}")
        # i18n
        return {"status": "success", "message_id": message_id, "error": None, "channel_type": self.channel_type}


class PushNotificationService(ChannelSender):
    """
    Обробляє надсилання Push-сповіщень (наприклад, через FCM, APNS).
    Фактична логіка надсилання push-сповіщень є заглушкою.
    """
    channel_type = "PUSH"

    def __init__(self):
        # TODO: Ініціалізувати клієнт для FCM/APNS.
        # firebase_admin.initialize_app(...) # Якщо використовується Firebase Admin SDK
        logger.info(f"{self.channel_type} сервіс ініціалізовано (заглушка).")

    async def send(
        self, user_to_notify: User, notification_content: Notification,
    ) -> Dict[str, Any]:
        # Припускаємо, що User модель має поле або зв'язок для активних push-токенів
        push_tokens: List[str] = getattr(user_to_notify, 'active_push_tokens', [])
        if not isinstance(push_tokens, list) or not push_tokens: # Додаткова перевірка типу
             push_tokens = [] # Якщо атрибут є, але не список, або порожній

        if not push_tokens:
            msg = f"У користувача ID '{user_to_notify.id}' відсутні активні push-токени. Неможливо надіслати PUSH ID '{notification_content.id}'." # i18n
            logger.warning(msg)
            return {"status": "failed", "error": msg, "channel_type": self.channel_type}

        title = notification_content.title
        body = notification_content.message
        # Дані для PUSH можуть включати додатковий payload для навігації в додатку
        payload = notification_content.payload or {}
        payload.update({"notification_id": str(notification_content.id)}) # Додаємо ID сповіщення в payload

        # TODO: Реалізувати фактичне надсилання PUSH через FCM/APNS.
        # try:
        #     # Для FCM:
        #     # message = FirebaseMessage(notification=firebase_admin.messaging.Notification(title=title, body=body),
        #     #                           data=payload, tokens=push_tokens) # Або multicast_message для кількох токенів
        #     # response = firebase_admin.messaging.send_multicast(message)
        #     # message_id = response.success_count # Або інший ідентифікатор відповіді
        #     message_id = f"placeholder_push_batch_id_{notification_content.id}_{uuid4()}" # Заглушка
        #     logger.info(f"PUSH успішно надіслано користувачу {user_to_notify.id} для сповіщення ID '{notification_content.id}'.")
        #     return {"status": "success", "message_id": message_id, "sent_to_tokens": len(push_tokens), "channel_type": self.channel_type}
        # except Exception as e:
        #     logger.error(f"Помилка надсилання PUSH для сповіщення ID '{notification_content.id}': {e}", exc_info=True)
        #     return {"status": "failed", "error": str(e), "channel_type": self.channel_type}

        message_id = f"placeholder_push_batch_id_{notification_content.id}_{uuid4()}"
        logger.info(f"[ЗАГЛУШКА] Надсилання PUSH сповіщення ID '{notification_content.id}':")
        logger.info(f"  Кому: {getattr(user_to_notify, 'username', user_to_notify.id)} (Токени: {push_tokens})")
        logger.info(f"  Заголовок: {title}")
        logger.info(f"  Тіло: {body[:100]}...")
        logger.info(f"  Payload: {payload}")
        logger.info(f"  PUSH надіслано (симуляція). ID Пакету: {message_id}")
        # i18n
        return {"status": "success", "message_id": message_id, "sent_to_tokens": len(push_tokens), "error": None, "channel_type": self.channel_type}

# TODO: Додати MessengerNotificationService, який може бути обгорткою для конкретних месенджер-сервісів
# class MessengerNotificationService(ChannelSender):
#     def __init__(self, messenger_service: BaseMessengerIntegrationService, channel_name: str):
#         self.messenger_service = messenger_service
#         self.channel_type = channel_name # e.g., "TELEGRAM", "SLACK"
#         logger.info(f"{self.channel_type} messenger channel sender initialized using {messenger_service.__class__.__name__}.")

#     async def send(self, user_to_notify: User, notification_content: Notification) -> Dict[str, Any]:
#         platform_user_id = await self.messenger_service.get_user_platform_id(user_to_notify.id)
#         if not platform_user_id:
#             msg = f"User ID '{user_to_notify.id}' has no platform ID for {self.channel_type}." # i18n
#             logger.warning(msg)
#             return {"status": "failed", "error": msg, "channel_type": self.channel_type}

#         message_text = f"{notification_content.title}\n{notification_content.message}" if notification_content.title else notification_content.message
#         command = MessageSendCommand(
#             recipient_platform_id=platform_user_id,
#             message=MessengerMessage(text=message_text)
#         )
#         response = await self.messenger_service.send_message(command)
#         return {
#             "status": response.status,
#             "message_id": response.platform_message_id,
#             "error": response.error_message,
#             "channel_type": self.channel_type
#         }

logger.info("Сервіси каналів доставки сповіщень (Email, SMS, Push - заглушки) визначено.")
