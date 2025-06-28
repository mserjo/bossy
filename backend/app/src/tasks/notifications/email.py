# backend/app/src/tasks/notifications/email.py
# -*- coding: utf-8 -*-
"""
Фонові завдання для надсилання email сповіщень.
Цей файл може містити загальне завдання для відправки email,
яке викликається іншими сервісами/завданнями.
"""
from backend.app.src.config.logging import get_logger
# TODO: Імпортувати екземпляр Celery app
# from backend.app.src.workers import celery_app as app # Приклад
# TODO: Імпортувати сервіс для надсилання email
# from backend.app.src.services.notifications.email_service import EmailService

logger = get_logger(__name__)

# @app.task(name="tasks.notifications.email.send_email_notification_task") # Приклад для Celery
def send_email_notification_task(recipient_email: str, subject: str, html_content: str, text_content: Optional[str] = None):
    """
    Асинхронне завдання для надсилання одного email сповіщення.

    Args:
        recipient_email (str): Email адреса отримувача.
        subject (str): Тема листа.
        html_content (str): HTML вміст листа.
        text_content (Optional[str]): Текстовий вміст листа (для клієнтів, що не підтримують HTML).
    """
    logger.info(f"Спроба надсилання email сповіщення на {recipient_email} з темою '{subject}'...")
    # try:
    #     email_service = EmailService() # Може ініціалізуватися з налаштуваннями SMTP
    #     await email_service.send_email(
    #         to_email=recipient_email,
    #         subject=subject,
    #         html_body=html_content,
    #         text_body=text_content
    #     )
    #     logger.info(f"Email сповіщення успішно надіслано на {recipient_email}.")
    #     return {"status": "success", "recipient": recipient_email}
    # except Exception as e:
    #     logger.error(f"Помилка надсилання email на {recipient_email}: {e}", exc_info=True)
    #     # TODO: Можливо, повторна спроба або логування для ручного втручання
    #     # raise self.retry(exc=e, countdown=60) # Приклад повторної спроби в Celery
    #     return {"status": "failed", "recipient": recipient_email, "error": str(e)}
    logger.info(f"Email сповіщення надіслано (ЗАГЛУШКА) на {recipient_email}.")
    return {"status": "completed_stub", "recipient": recipient_email}

# @app.task(name="tasks.notifications.email.send_bulk_email_task") # Приклад для Celery
def send_bulk_email_task(recipients: List[str], subject: str, html_content: str, text_content: Optional[str] = None):
    """
    Асинхронне завдання для масової розсилки однакових email сповіщень.
    """
    logger.info(f"Запуск масової розсилки email з темою '{subject}' для {len(recipients)} отримувачів...")
    # successful_sends = 0
    # failed_sends = 0
    # for email_addr in recipients:
    #     # Можна викликати send_email_notification_task.delay(email_addr, ...) для кожного,
    #     # або мати окрему логіку в EmailService для пакетної відправки.
    #     # result = send_email_notification_task(email_addr, subject, html_content, text_content)
    #     # if result.get("status") == "success" or result.get("status") == "completed_stub":
    #     #     successful_sends +=1
    #     # else:
    #     #     failed_sends +=1
    #     pass # Заглушка
    # logger.info(f"Масова розсилка email завершена. Успішно: {successful_sends}, Невдало: {failed_sends} (ЗАГЛУШКА).")
    logger.info(f"Масова розсилка email завершена (ЗАГЛУШКА).")
    return {"status": "completed_stub", "total_recipients": len(recipients)}

# TODO: Додати інші специфічні завдання, пов'язані з email, якщо потрібно.
