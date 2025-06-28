# backend/app/src/tasks/notifications/digests.py
# -*- coding: utf-8 -*-
"""
Фонові завдання для надсилання дайджестів (наприклад, щоденних, щотижневих).
"""
from backend.app.src.config.logging import get_logger
# TODO: Імпортувати екземпляр Celery app
# from backend.app.src.workers import celery_app as app # Приклад
# TODO: Імпортувати сервіси для збору даних для дайджесту та надсилання сповіщень
# from backend.app.src.services.user_activity_service import UserActivityService
# from backend.app.src.services.task_service import TaskSummaryService
# from backend.app.src.services.notification_creation_service import NotificationCreationService
# from backend.app.src.config.database import SessionLocal
# from datetime import datetime, timedelta

logger = get_logger(__name__)

# @app.task(name="tasks.notifications.digests.send_daily_activity_digest_task") # Приклад для Celery
def send_daily_activity_digest_task():
    """
    Періодичне завдання для надсилання щоденного дайджесту активності
    користувачам або адміністраторам груп.
    """
    logger.info("Запуск завдання надсилання щоденного дайджесту активності...")
    # db = None
    # try:
    #     db = SessionLocal()
    #     # user_activity_service = UserActivityService(db)
    #     # notification_creator = NotificationCreationService(db)
    #
    #     # 1. Визначити користувачів/групи, яким потрібно надіслати дайджест.
    #     # users_to_notify = await get_users_for_daily_digest()
    #
    #     # for user_or_group_admin in users_to_notify:
    #     #     # 2. Зібрати дані для дайджесту за попередній день.
    #     #     # - Нові завдання в групах користувача.
    #     #     # - Виконані завдання користувачем / в його групах.
    #     #     # - Отримані бонуси/нагороди.
    #     #     # - Нові досягнення.
    #     #     # - Важливі події в групах.
    #     #     digest_data = await user_activity_service.generate_daily_digest_for_user(user_or_group_admin.id)
    #     #
    #     #     if digest_data and digest_data.has_content: # Перевірка, чи є що надсилати
    #     #         logger.info(f"Надсилання щоденного дайджесту користувачу {user_or_group_admin.email} (ЗАГЛУШКА).")
    #     #         # await notification_creator.create_and_send_digest_notification(
    #     #         #     user_id=user_or_group_admin.id,
    #     #         #     digest_type="daily_activity",
    #     #         #     digest_html_content=render_digest_template(digest_data), # Потрібен шаблонізатор
    #     #         #     channel="email" # Або інший канал
    #     #         # )
    #     #     else:
    #     #         logger.info(f"Немає даних для щоденного дайджесту для користувача {user_or_group_admin.email}.")
    #
    # except Exception as e:
    #     logger.error(f"Помилка в завданні надсилання щоденного дайджесту: {e}", exc_info=True)
    # finally:
    #     if db:
    #         db.close()

    logger.info("Завдання надсилання щоденного дайджесту активності завершено (ЗАГЛУШКА).")
    return {"status": "completed", "message": "Daily activity digest task finished (stub)."}

# TODO: Додати завдання для щотижневих/щомісячних дайджестів, якщо потрібно.
# TODO: Реалізувати логіку get_users_for_daily_digest(), generate_daily_digest_for_user()
# та render_digest_template().
