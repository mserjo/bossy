# backend/app/src/tasks/system/cron_task_executor.py
# -*- coding: utf-8 -*-
"""
Фонове завдання для виконання системних cron-задач, визначених у базі даних.
"""
from backend.app.src.config.logging import get_logger
# TODO: Імпортувати екземпляр Celery app
# from backend.app.src.workers import celery_app as app # Приклад
# TODO: Імпортувати сервіс для роботи з CronTaskModel
# from backend.app.src.services.system.cron_task_service import CronTaskService
# from backend.app.src.config.database import SessionLocal # Для створення сесії БД в завданні
# from croniter import croniter # Для перевірки розкладу cron
# from datetime import datetime

logger = get_logger(__name__)

# @app.task(name="tasks.system.cron_task_executor.execute_due_cron_tasks") # Приклад для Celery
def execute_due_cron_tasks():
    """
    Періодичне завдання, що перевіряє та виконує системні cron-задачі,
    які визначені в базі даних (наприклад, в CronTaskModel) і час виконання яких настав.
    """
    logger.info("Запуск завдання виконання динамічних cron-задач...")
    # db = None
    # try:
    #     db = SessionLocal()
    #     cron_service = CronTaskService(db)
    #     active_cron_tasks = await cron_service.get_active_and_due_tasks() # Метод, що повертає задачі, які мають виконатися
    #
    #     if not active_cron_tasks:
    #         logger.info("Немає активних динамічних cron-задач для виконання.")
    #         return {"status": "completed", "message": "No due dynamic cron tasks."}
    #
    #     for cron_task_model in active_cron_tasks:
    #         logger.info(f"Обробка cron-задачі: {cron_task_model.name} (ID: {cron_task_model.id})")
    #         # Перевірка, чи дійсно час виконання (може бути подвійною перевіркою, якщо get_active_and_due_tasks це вже робить)
    #         # now = datetime.utcnow()
    #         # iter = croniter(cron_task_model.cron_expression, now)
    #         # scheduled_time = iter.get_prev(datetime) # Час попереднього запуску за розкладом
    #         # if now < scheduled_time + timedelta(minutes=1): # Приклад перевірки, щоб не запускати занадто часто
    #
    #         try:
    #             # TODO: Реалізувати механізм виконання завдання
    #             # Це може бути виклик іншого Celery завдання, запуск скрипта, HTTP запит тощо,
    #             # залежно від того, як визначено `task_action` або `command` в `CronTaskModel`.
    #             # Наприклад:
    #             # if cron_task_model.task_type == "celery":
    #             #     app.send_task(cron_task_model.task_name, args=cron_task_model.args, kwargs=cron_task_model.kwargs)
    #             # elif cron_task_model.task_type == "script":
    #             #     subprocess.run([cron_task_model.command, cron_task_model.args_str], check=True)
    #
    #             logger.info(f"Cron-задача '{cron_task_model.name}' успішно запущена/оброблена (ЗАГЛУШКА).")
    #             # Оновити час останнього запуску в CronTaskModel
    #             # await cron_service.update_task_last_run(cron_task_model.id, now)
    #         except Exception as task_exec_error:
    #             logger.error(f"Помилка виконання cron-задачі '{cron_task_model.name}': {task_exec_error}", exc_info=True)
    #             # Оновити статус помилки в CronTaskModel
    #             # await cron_service.update_task_last_error(cron_task_model.id, str(task_exec_error))
    #
    # except Exception as e:
    #     logger.error(f"Загальна помилка в завданні execute_due_cron_tasks: {e}", exc_info=True)
    # finally:
    #     if db:
    #         db.close()

    logger.info("Завдання виконання динамічних cron-задач завершено (ЗАГЛУШКА).")
    return {"status": "completed", "message": "Dynamic cron tasks execution finished (stub)."}

# TODO: Визначити структуру CronTaskModel (name, cron_expression, task_type, task_name/command, args, kwargs, is_active, last_run_at, last_error).
# TODO: Реалізувати CronTaskService для CRUD операцій з CronTaskModel та для отримання завдань до виконання.
