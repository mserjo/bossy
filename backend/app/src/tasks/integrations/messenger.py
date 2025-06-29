# backend/app/src/tasks/integrations/messenger.py
# -*- coding: utf-8 -*-
"""
Фонові завдання для обробки інтеграцій з месенджерами.
Наприклад, обробка вхідних команд або повідомлень, отриманих через вебхуки.
"""
from backend.app.src.config.logging import get_logger
# TODO: Імпортувати екземпляр Celery app
# from backend.app.src.workers import celery_app as app # Приклад
from typing import Optional, Dict, Any # Додано для Optional, Dict, Any
# TODO: Імпортувати сервіси для взаємодії з логікою бота або командами
# from backend.app.src.services.bot.command_handler_service import CommandHandlerService
# from backend.app.src.services.integrations.messenger_service_factory import MessengerServiceFactory # Для відправки відповідей
# from backend.app.src.config.database import SessionLocal

logger = get_logger(__name__)

# @app.task(name="tasks.integrations.messenger.process_incoming_messenger_message_task") # Приклад для Celery
def process_incoming_messenger_message_task(
    provider_name: str, # Наприклад, 'telegram', 'slack'
    user_messenger_id: str, # ID користувача в месенджері (chat_id, user_id в Slack)
    full_payload: Dict[str, Any], # Повний payload від месенджера
    text_message: Optional[str] = None,
    # command: Optional[str] = None, # Якщо це команда
    # callback_query_data: Optional[str] = None, # Для Telegram inline кнопок
    # event_payload: Optional[Dict[str, Any]] = None # Повний payload від месенджера (схоже на full_payload)
):
    """
    Асинхронне завдання для обробки вхідного повідомлення або команди від месенджера.

    Args:
        provider_name (str): Провайдер месенджера.
        user_messenger_id (str): Ідентифікатор користувача в месенджері.
        text_message (Optional[str]): Текст повідомлення, якщо є.
        full_payload (Dict[str, Any]): Повний об'єкт події/повідомлення від месенджера.
    """
    logger.info(
        f"Обробка вхідного повідомлення/події від {provider_name} для користувача {user_messenger_id}. "
        f"Текст: '{text_message[:50] if text_message else 'N/A'}'..."
    )
    # db = None
    # try:
    #     db = SessionLocal()
    #     # 1. Ідентифікувати користувача системи Bossy за user_messenger_id та provider_name
    #     # Це може вимагати запиту до БД (таблиця UserIntegrations або подібна)
    #     # user_integration_service = UserIntegrationService(db)
    #     # bossy_user = await user_integration_service.get_user_by_messenger_id(provider_name, user_messenger_id)
    #     #
    #     # if not bossy_user:
    #     #     logger.warning(f"Не вдалося знайти користувача Bossy для {provider_name} ID {user_messenger_id}.")
    #     #     # Можливо, надіслати відповідь "зареєструйтесь" або проігнорувати
    #     #     return {"status": "failed", "reason": "user_not_found_in_bossy"}
    #
    #     # 2. Визначити тип дії (команда, текст, callback_query) та обробити
    #     # command_handler_service = CommandHandlerService(db, user=bossy_user, provider=provider_name, messenger_user_id=user_messenger_id)
    #     # response_text = await command_handler_service.handle_message(
    #     # text=text_message,
    #     # payload=full_payload
    #     # )
    #
    #     # 3. Якщо є відповідь, надіслати її назад користувачу через сервіс месенджера
    #     # if response_text:
    #     #     messenger_service = MessengerServiceFactory.get_service(provider_name, db, bossy_user.id)
    #     #     await messenger_service.send_message_to_messenger_user(
    #     #         user_messenger_id=user_messenger_id,
    #     #         text=response_text
    #     #     )
    #     #     logger.info(f"Відповідь надіслано користувачу {user_messenger_id} ({provider_name}): '{response_text[:50]}...'")
    #
    #     logger.info(f"Вхідне повідомлення від {provider_name} для {user_messenger_id} оброблено (ЗАГЛУШКА).")
    #     return {"status": "completed_stub", "provider": provider_name, "messenger_user_id": user_messenger_id}
    #
    # except Exception as e:
    #     logger.error(f"Помилка обробки повідомлення від {provider_name} для {user_messenger_id}: {e}", exc_info=True)
    #     # TODO: Можливо, надіслати повідомлення про помилку користувачу, якщо це доречно
    #     return {"status": "error", "provider": provider_name, "messenger_user_id": user_messenger_id, "error": str(e)}
    # finally:
    #     if db:
    #         db.close()
    logger.info(f"Обробка вхідного повідомлення від {provider_name} для {user_messenger_id} завершена (ЗАГЛУШКА).")
    return {"status": "completed", "message": "Incoming messenger message processing finished (stub)."}

# TODO: Додати інші завдання, специфічні для інтеграцій з месенджерами, якщо потрібно.
