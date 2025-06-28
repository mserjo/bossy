# backend/app/src/tasks/notifications/reminders.py
# -*- coding: utf-8 -*-
"""
Фонові завдання для надсилання нагадувань.
"""
from backend.app.src.config.logging import get_logger
# TODO: Імпортувати екземпляр Celery app
# from backend.app.src.workers import celery_app as app # Приклад
# TODO: Імпортувати сервіси для роботи з завданнями та сповіщеннями
# from backend.app.src.services.task.task_service import TaskService
# from backend.app.src.services.notifications.notification_creation_service import NotificationCreationService # Сервіс, що створює та надсилає сповіщення
# from backend.app.src.config.database import SessionLocal
# from datetime import datetime, timedelta

logger = get_logger(__name__)

# @app.task(name="tasks.notifications.reminders.send_task_deadline_reminders_task") # Приклад для Celery
def send_task_deadline_reminders_task():
    """
    Періодичне завдання для надсилання нагадувань користувачам про завдання,
    термін виконання яких наближається або вже минув.
    """
    logger.info("Запуск завдання надсилання нагадувань про дедлайни завдань...")
    # db = None
    # try:
    #     db = SessionLocal()
    #     task_service = TaskService(db)
    #     notification_creator = NotificationCreationService(db) # Або частина NotificationService
    #
    #     # 1. Отримати завдання, дедлайн яких наближається (наприклад, наступні 24 години)
    #     # now = datetime.utcnow()
    #     # reminder_threshold_soon = now + timedelta(hours=settings.TASK_DEADLINE_REMINDER_HOURS_SOON) # Налаштування
    #     # upcoming_deadline_tasks = await task_service.get_tasks_with_deadline_between(now, reminder_threshold_soon)
    #
    #     # for task in upcoming_deadline_tasks:
    #     #     # Отримати призначених користувачів
    #     #     assignees = await task_service.get_task_assignees(task.id)
    #     #     for assignee in assignees:
    #     #         # TODO: Перевірити налаштування сповіщень користувача
    #     #         # TODO: Перевірити, чи не надсилалося вже нагадування нещодавно
    #     #         logger.info(f"Надсилання нагадування про наближення дедлайну завдання '{task.name}' користувачу {assignee.email} (ЗАГЛУШКА).")
    #     #         # await notification_creator.create_and_send_task_deadline_soon_notification(
    #     #         #     user_id=assignee.id, task_id=task.id, task_name=task.name, due_date=task.due_date
    #     #         # )
    #
    #     # 2. Отримати завдання, дедлайн яких минув, але вони ще не виконані
    #     # reminder_threshold_overdue = now - timedelta(hours=settings.TASK_OVERDUE_CHECK_HOURS) # Налаштування
    #     # overdue_tasks = await task_service.get_overdue_uncompleted_tasks(reminder_threshold_overdue)
    #
    #     # for task in overdue_tasks:
    #     #     assignees = await task_service.get_task_assignees(task.id)
    #     #     for assignee in assignees:
    #     #         # TODO: Перевірка налаштувань, частоти нагадувань
    #     #         logger.info(f"Надсилання нагадування про прострочене завдання '{task.name}' користувачу {assignee.email} (ЗАГЛУШКА).")
    #     #         # await notification_creator.create_and_send_task_overdue_notification(
    #     #         #     user_id=assignee.id, task_id=task.id, task_name=task.name, due_date=task.due_date
    #     #         # )
    #     #     # Можливо, сповіщення адміну групи про прострочене завдання
    #     #     # group_admin = await task_service.get_task_group_admin(task.id)
    #     #     # if group_admin:
    #     #     #     logger.info(f"Надсилання сповіщення адміну {group_admin.email} про прострочене завдання '{task.name}' (ЗАГЛУШКА).")
    #
    # except Exception as e:
    #     logger.error(f"Помилка в завданні надсилання нагадувань про дедлайни: {e}", exc_info=True)
    # finally:
    #     if db:
    #         db.close()

    logger.info("Завдання надсилання нагадувань про дедлайни завдань завершено (ЗАГЛУШКА).")
    return {"status": "completed", "message": "Task deadline reminders task finished (stub)."}

# TODO: Додати інші типи нагадувань, якщо потрібно (наприклад, про неактивність).
