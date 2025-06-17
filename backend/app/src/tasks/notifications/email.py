# backend/app/src/tasks/notifications/email.py
# -*- coding: utf-8 -*-
"""
Модуль для завдання відправки Email сповіщень.

Визначає `SendEmailTask`, відповідальний за асинхронну відправку
електронних листів.
"""

import asyncio
import smtplib
import ssl # Для SSL context при SMTP_SSL
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, Optional

from app.src.tasks.base import BaseTask
# from app.src.config.settings import settings # Для доступу до конфігурації SMTP
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Приклад конфігурації SMTP (має бути винесено в settings та захищено)
SMTP_SERVER = "localhost"  # settings.SMTP_SERVER Зазвичай "smtp.example.com"
SMTP_PORT = 1025             # settings.SMTP_PORT (587 for TLS, 465 for SSL, 1025 для локального DebuggingServer)
SMTP_USERNAME = ""    # settings.SMTP_USERNAME Зазвичай "user@example.com"
SMTP_PASSWORD = "" # settings.SMTP_PASSWORD (зберігати безпечно, через env var або vault!)
SMTP_SENDER_EMAIL = "noreply@kudos.example.com" # settings.SMTP_SENDER_EMAIL
SMTP_USE_TLS = False        # settings.SMTP_USE_TLS (True для порту 587)
SMTP_USE_SSL = False        # settings.SMTP_USE_SSL (True для порту 465)


class SendEmailTask(BaseTask):
    """
    Завдання для асинхронної відправки електронних листів.

    Використовує `smtplib` для взаємодії з SMTP сервером.
    У реальній системі рекомендується використовувати більш високорівневі
    бібліотеки або сервіси для відправки email, які обробляють
    шаблони, MIME типи, відписки, відстеження тощо (наприклад, SendGrid, Mailgun).
    """

    def __init__(self, name: str = "SendEmailTask"):
        """
        Ініціалізація завдання відправки email.
        """
        super().__init__(name)
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.smtp_username = SMTP_USERNAME
        self.smtp_password = SMTP_PASSWORD # УВАГА: Не зберігайте паролі так у продакшені! Використовуйте змінні середовища або сервіси секретів.
        self.sender_email = SMTP_SENDER_EMAIL
        self.use_tls = SMTP_USE_TLS # Для STARTTLS
        self.use_ssl = SMTP_USE_SSL # Для прямого SSL з'єднання

        if self.use_tls and self.use_ssl:
            self.logger.warning("SMTP_USE_TLS та SMTP_USE_SSL обидва встановлені в True. Пріоритет буде надано SMTP_USE_SSL (порт 465).")
            self.use_tls = False # Щоб уникнути конфлікту логіки


    async def _send_email_notification(
        self,
        recipient_email: str,
        subject: str,
        html_body: Optional[str] = None,
        text_body: Optional[str] = None,
        sender_name: Optional[str] = None
    ) -> bool:
        """
        Виконує фактичну відправку email.
        """
        if not recipient_email or not subject or (not html_body and not text_body):
            self.logger.error("Недостатньо даних для відправки email: відсутній отримувач, тема або тіло листа.")
            return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject

        from_email_display = f"{sender_name} <{self.sender_email}>" if sender_name else self.sender_email
        msg['From'] = from_email_display
        msg['To'] = recipient_email

        if text_body:
            msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
        if html_body:
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        if not msg.get_payload():
             self.logger.error("Тіло листа порожнє (не додано ані text_body, ані html_body). Email не буде відправлено.")
             return False

        self.logger.info(f"Спроба відправки email на '{recipient_email}' з темою '{subject}' через {self.smtp_server}:{self.smtp_port}")

        try:
            loop = asyncio.get_event_loop()
            # Використовуємо run_in_executor для блокуючої операції smtplib
            await loop.run_in_executor(None, self._blocking_smtp_send, msg)
            self.logger.info(f"Email успішно передано для відправки на '{recipient_email}'.")
            return True
        except smtplib.SMTPAuthenticationError as e:
            self.logger.error(f"Помилка SMTP автентифікації ({self.smtp_username}) при відправці email на '{recipient_email}': {e}", exc_info=True)
        except smtplib.SMTPServerDisconnected as e:
            self.logger.error(f"SMTP сервер ({self.smtp_server}) розірвав з'єднання: {e}", exc_info=True)
        except smtplib.SMTPRecipientsRefused as e:
            self.logger.error(f"SMTP сервер відхилив отримувачів ('{recipient_email}'): {e.rcptfailed}", exc_info=True)
        except smtplib.SMTPSenderRefused as e:
            self.logger.error(f"SMTP сервер відхилив відправника ('{self.sender_email}'): {e}", exc_info=True)
        except ConnectionRefusedError:
             self.logger.error(f"Не вдалося підключитися до SMTP серверу {self.smtp_server}:{self.smtp_port}. Перевірте налаштування та доступність сервера.")
        except smtplib.SMTPException as e: # Загальний SMTP виняток
            self.logger.error(f"Загальна помилка SMTP при відправці email на '{recipient_email}': {e}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Непередбачена помилка під час відправки email на '{recipient_email}': {e}", exc_info=True)

        return False

    def _blocking_smtp_send(self, msg: MIMEMultipart):
        """
        Блокуюча частина логіки відправки SMTP. Виконується в окремому потоці.
        """
        server: Optional[smtplib.SMTP] = None
        try:
            if self.use_ssl: # Пряме SSL з'єднання (зазвичай порт 465)
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=10, context=context)
            else: # Звичайне з'єднання, може бути оновлене до TLS (зазвичай порт 587 або 25)
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
                if self.use_tls: # Оновлення до TLS (STARTTLS)
                    server.ehlo() # Обов'язково перед starttls
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo() # Повторний ehlo після STARTTLS також є хорошою практикою

            # Автентифікація, якщо ім'я користувача та пароль надані
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)

            server.send_message(msg)
            self.logger.debug(f"SMTP: Лист '{msg['Subject']}' до '{msg['To']}' відправлено через {self.smtp_server}.")

        # Не ловимо тут конкретні SMTP винятки, щоб вони спливли до _send_email_notification
        finally:
            if server:
                try:
                    server.quit()
                except smtplib.SMTPServerDisconnected:
                    self.logger.debug("SMTP: Сервер вже відключився, quit не потрібен.")
                except Exception as e_quit:
                    self.logger.warning(f"SMTP: Помилка під час server.quit(): {e_quit}", exc_info=False)


    async def run(
        self,
        recipient_email: str,
        subject: str,
        html_body: Optional[str] = None,
        text_body: Optional[str] = None,
        sender_name: Optional[str] = None,
        **kwargs: Any # Для сумісності з BaseTask та можливих майбутніх розширень
    ) -> Dict[str, Any]:
        """
        Виконує відправку email сповіщення.

        Args:
            recipient_email (str): Email адреса отримувача.
            subject (str): Тема листа.
            html_body (Optional[str]): HTML версія тіла листа.
            text_body (Optional[str]): Текстова версія тіла листа (рекомендовано надавати разом з HTML).
            sender_name (Optional[str]): Ім'я відправника, яке буде відображатися.
                                         Якщо не надано, використовується тільки `sender_email`.
            **kwargs: Додаткові аргументи (наразі не використовуються).

        Returns:
            Dict[str, Any]: Результат операції, що містить {'sent': True/False,
                                                         'recipient': str,
                                                         'error': Optional[str]}.
        """
        self.logger.info(f"Завдання '{self.name}' отримало запит на відправку email на '{recipient_email}' з темою '{subject}'.")

        if not html_body and not text_body:
            error_msg = "Не надано ані HTML, ані текстового тіла для email."
            self.logger.error(f"{error_msg} Одержувач: {recipient_email}, Тема: {subject}")
            # Відповідно до BaseTask, якщо завдання не може виконати свою роботу через невірні вхідні дані,
            # воно може повернути результат з помилкою, але не обов'язково має прокидати виняток,
            # якщо це не системна помилка самого завдання.
            return {"sent": False, "error": error_msg, "recipient": recipient_email}

        success = await self._send_email_notification(
            recipient_email=recipient_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            sender_name=sender_name
        )

        result = {"sent": success, "recipient": recipient_email}
        if not success:
            # Деталі помилки вже залоговані в _send_email_notification
            result["error"] = f"Не вдалося надіслати email на {recipient_email}. Дивіться логи для деталей."
            # Якщо потрібно, щоб BaseTask.on_failure спрацював, можна прокинути виняток тут.
            # raise EmailSendingFailedError(f"Failed to send email to {recipient_email}")

        return result

# # Приклад використання (можна видалити або закоментувати):
# # class EmailSendingFailedError(Exception): pass
#
# # async def main():
# #     logging.basicConfig(
# #         level=logging.DEBUG, # DEBUG для детальних логів SMTP
# #         format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# #     )
# #
# #     # Для тестування: запустіть локальний SMTP сервер:
# #     # python -m smtpd -c DebuggingServer -n localhost:1025
# #     # І переконайтеся, що константи SMTP_* встановлені відповідно:
# #     # SMTP_SERVER = "localhost"
# #     # SMTP_PORT = 1025
# #     # SMTP_USERNAME = ""
# #     # SMTP_PASSWORD = ""
# #     # SMTP_SENDER_EMAIL = "testsender@kudos.example.com"
# #     # SMTP_USE_TLS = False
# #     # SMTP_USE_SSL = False
# #
# #     email_task = SendEmailTask()
# #
# #     # Тест 1: Успішна відправка
# #     logger.info("Тест 1: Спроба успішної відправки...")
# #     result_test_1 = await email_task.execute(
# #         recipient_email="recipient1@example.com",
# #         subject="Тестовий лист 1 (HTML + Text)",
# #         text_body="Це простий текстовий лист, відправлений через SendEmailTask.",
# #         html_body="<h1>Привіт!</h1><p>Це <b>HTML</b> лист, відправлений через <code>SendEmailTask</code>.</p>",
# #         sender_name="Kudos Система"
# #     )
# #     logger.info(f"Результат тесту 1: {result_test_1}")
# #
# #     # Тест 2: Лист без тіла
# #     logger.info("\nТест 2: Спроба відправки листа без тіла...")
# #     result_test_2 = await email_task.execute(
# #         recipient_email="recipient2@example.com",
# #         subject="Тестовий лист 2 (Без тіла)"
# #     )
# #     logger.info(f"Результат тесту 2: {result_test_2}")
# #
# #     # Тест 3: Лист тільки з текстовим тілом
# #     logger.info("\nТест 3: Спроба відправки листа тільки з текстом...")
# #     result_test_3 = await email_task.execute(
# #         recipient_email="recipient3@example.com",
# #         subject="Тестовий лист 3 (Тільки текст)",
# #         text_body="Це лист, що містить лише текстову версію."
# #     )
# #     logger.info(f"Результат тесту 3: {result_test_3}")
# #
# # if __name__ == "__main__":
# #     # Для Windows може знадобитися: asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# #     asyncio.run(main())
