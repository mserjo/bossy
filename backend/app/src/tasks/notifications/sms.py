# backend/app/src/tasks/notifications/sms.py
# -*- coding: utf-8 -*-
"""
Фонові завдання для надсилання SMS сповіщень.
"""
from backend.app.src.config.logging import get_logger
# TODO: Імпортувати екземпляр Celery app
# from backend.app.src.workers import celery_app as app # Приклад
# TODO: Імпортувати сервіс для надсилання SMS
# from backend.app.src.services.notifications.sms_service import SmsService

logger = get_logger(__name__)

# @app.task(name="tasks.notifications.sms.send_sms_notification_task") # Приклад для Celery
def send_sms_notification_task(phone_number: str, message_text: str):
    """
    Асинхронне завдання для надсилання одного SMS сповіщення.

    Args:
        phone_number (str): Номер телефону отримувача.
        message_text (str): Текст SMS повідомлення.
    """
    logger.info(f"Спроба надсилання SMS сповіщення на {phone_number} з текстом: '{message_text[:30]}...'")
    # try:
    #     sms_service = SmsService() # Може ініціалізуватися з налаштуваннями SMS-шлюзу
    #     await sms_service.send_sms(
    #         to_phone_number=phone_number,
    #         text=message_text
    #     )
    #     logger.info(f"SMS сповіщення успішно надіслано на {phone_number}.")
    #     return {"status": "success", "recipient": phone_number}
    # except Exception as e:
    #     logger.error(f"Помилка надсилання SMS на {phone_number}: {e}", exc_info=True)
    #     # return {"status": "failed", "recipient": phone_number, "error": str(e)}
    logger.info(f"SMS сповіщення надіслано (ЗАГЛУШКА) на {phone_number}.")
    return {"status": "completed_stub", "recipient": phone_number}

# TODO: Додати завдання для масової розсилки SMS, якщо потрібно.
