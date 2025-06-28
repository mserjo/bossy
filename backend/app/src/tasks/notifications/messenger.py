# backend/app/src/tasks/notifications/messenger.py
# -*- coding: utf-8 -*-
"""
Фонові завдання для надсилання сповіщень через месенджери.
"""
from backend.app.src.config.logging import get_logger
# TODO: Імпортувати екземпляр Celery app
# from backend.app.src.workers import celery_app as app # Приклад
# TODO: Імпортувати фабрику сервісів месенджерів або конкретні сервіси
# from backend.app.src.services.integrations.messenger_service_factory import MessengerServiceFactory
# from backend.app.src.config.database import SessionLocal # Якщо потрібен доступ до БД для отримання деталей інтеграції

logger = get_logger(__name__)

# @app.task(name="tasks.notifications.messenger.send_messenger_notification_task") # Приклад для Celery
def send_messenger_notification_task(
    user_id: int, # ID користувача в нашій системі
    provider_name: str, # Наприклад, 'telegram', 'slack'
    message_text: str,
    # Можливо, додаткові параметри для форматування або специфіки месенджера
    # message_params: Optional[Dict[str, Any]] = None
):
    """
    Асинхронне завдання для надсилання сповіщення через вказаний месенджер
    конкретному користувачу.

    Args:
        user_id (int): ID користувача, якому надсилається сповіщення.
        provider_name (str): Код провайдера месенджера.
        message_text (str): Текст повідомлення.
    """
    logger.info(
        f"Спроба надсилання сповіщення через месенджер {provider_name} "
        f"користувачу ID {user_id} з текстом: '{message_text[:50]}...'"
    )
    # db = None
    # try:
    #     db = SessionLocal()
    #     # Отримати активну інтеграцію месенджера для користувача та провайдера
    #     # Це може робити MessengerServiceFactory або окремий UserIntegrationService
    #     messenger_service = MessengerServiceFactory.get_service_for_user_and_provider(
    #         user_id=user_id,
    #         provider_name=provider_name,
    #         db_session=db # Сервіс може потребувати сесію для завантаження токенів/ідентифікаторів
    #     )
    #
    #     if not messenger_service:
    #         logger.warning(f"Не знайдено активної інтеграції {provider_name} для користувача ID {user_id}.")
    #         return {"status": "failed", "reason": "integration_not_found"}
    #
    #     # Сервіс месенджера має метод для надсилання повідомлення
    #     # (наприклад, на основі збереженого chat_id або user_id в месенджері)
    #     await messenger_service.send_message_to_user(
    #         # user_messenger_identifier= ..., # Отримується з налаштувань інтеграції
    #         text=message_text,
    #         # params=message_params
    #     )
    #     logger.info(f"Сповіщення через {provider_name} успішно надіслано користувачу ID {user_id}.")
    #     return {"status": "success", "user_id": user_id, "provider": provider_name}
    # except Exception as e:
    #     logger.error(f"Помилка надсилання сповіщення через {provider_name} користувачу ID {user_id}: {e}", exc_info=True)
    #     return {"status": "failed", "user_id": user_id, "provider": provider_name, "error": str(e)}
    # finally:
    #     if db:
    #         db.close()
    logger.info(f"Сповіщення через месенджер {provider_name} надіслано (ЗАГЛУШКА) користувачу ID {user_id}.")
    return {"status": "completed_stub", "user_id": user_id, "provider": provider_name}

# TODO: Додати завдання для масової розсилки через месенджери, якщо це підтримується
# і потрібно (наприклад, розсилка в групові чати бота або всім підписаним користувачам).
