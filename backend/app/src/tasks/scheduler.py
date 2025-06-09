# backend/app/src/tasks/scheduler.py
# -*- coding: utf-8 -*-
"""
Конфігурація та управління планувальником завдань.

Цей модуль відповідає за налаштування, запуск та управління планувальником
фонових завдань. Це може бути реалізовано за допомогою APScheduler для
внутрішньо-процесних завдань або як клієнт для Celery Beat, якщо
використовується розподілена система завдань.

Основні компоненти:
    scheduler: Екземпляр планувальника (наприклад, APScheduler).
    init_scheduler(): Функція для ініціалізації та запуску планувальника.
    shutdown_scheduler(): Функція для коректної зупинки планувальника.
    add_scheduled_task(): Допоміжна функція для додавання нових завдань до планувальника.
"""

import logging
import asyncio
from typing import Callable, Any, Dict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from pytz import utc

# from app.src.config.settings import settings # Потенційно для налаштувань часової зони, тощо
from app.src.tasks.system.cleanup import CleanupTask
from app.src.tasks.system.backup import DatabaseBackupTask
from app.src.tasks.system.monitoring import SystemMetricsCollectorTask
# from app.src.tasks.notifications.email import SendEmailTask # Приклад імпорту завдання

# Налаштування логера для цього модуля
logger = logging.getLogger(__name__)

# Словник для зберігання посилань на екземпляри завдань, якщо це потрібно
# registered_tasks: Dict[str, Any] = {} # Наприклад, для перевикористання екземплярів

# Конфігурація JobStore та Executor для APScheduler
# JobStore зберігає завдання (тут в пам'яті, для продакшену може бути БД)
jobstores = {
    'default': MemoryJobStore()
}
# Executor відповідає за виконання завдань
executors = {
    'default': AsyncIOExecutor()
}
# Налаштування часової зони за замовчуванням для планувальника
job_defaults = {
    'coalesce': False,  # Не об'єднувати пропущені запуски
    'max_instances': 3  # Максимальна кількість одночасних екземплярів одного завдання
}

# Створення екземпляру планувальника APScheduler
scheduler = AsyncIOScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone=utc # Використання UTC як стандартної часової зони
)

def add_scheduled_task(func: Callable, trigger: str, **trigger_args: Any) -> None:
    """
    Додає завдання до планувальника.

    Args:
        func (Callable): Функція або метод завдання для виконання.
        trigger (str): Тип тригера (наприклад, 'interval', 'cron', 'date').
        **trigger_args: Аргументи для тригера (наприклад, minutes=1, day_of_week='mon-fri', hour='00').
    """
    try:
        scheduler.add_job(func, trigger=trigger, **trigger_args)
        logger.info(f"Завдання '{getattr(func, '__name__', str(func))}' додано до планувальника. Тригер: {trigger}, Аргументи: {trigger_args}")
    except Exception as e:
        logger.error(f"Помилка додавання завдання '{getattr(func, '__name__', str(func))}' до планувальника: {e}", exc_info=True)

# async def example_task_function():
#     """Приклад простої функції, яку можна запускати за розкладом."""
#     logger.info("Приклад запланованого завдання виконано!")
#     # Тут може бути логіка вашого завдання, наприклад:
#     # cleanup_task_instance = CleanupTask()
#     # await cleanup_task_instance.execute()


def initialize_scheduled_tasks():
    """
    Ініціалізує та додає всі заплановані завдання до планувальника.
    Ця функція повинна викликатися при старті додатку.
    """
    logger.info("Ініціалізація запланованих завдань...")
    logger.info("Ініціалізація системних завдань...")

    # Завдання для очищення системи (щодня о 02:00)
    cleanup_task = CleanupTask()
    add_scheduled_task(
        cleanup_task.execute,
        'cron',
        hour=2,
        minute=0,
        day_of_week='*', # Щодня
        id="system_cleanup_task", # Важливо давати ID для можливості управління завданням
        replace_existing=True     # Замінити, якщо завдання з таким ID вже існує
    )
    # registered_tasks["cleanup_task"] = cleanup_task # Якщо потрібно зберігати екземпляр

    # Завдання для резервного копіювання бази даних (щодня о 03:30)
    # Переконайтеся, що pg_dump налаштований та доступний, і є права на запис в директорію бекапів.
    db_backup_task = DatabaseBackupTask()
    add_scheduled_task(
        db_backup_task.execute,
        'cron',
        hour=3,
        minute=30,
        day_of_week='*', # Щодня
        kwargs={"keep_last_n_backups": 7}, # Приклад передачі аргументів у завдання
        id="database_backup_task",
        replace_existing=True
    )
    # registered_tasks["db_backup_task"] = db_backup_task

    # Завдання для збору системних метрик (кожні 15 хвилин)
    # Переконайтеся, що бібліотека psutil встановлена.
    system_metrics_task = SystemMetricsCollectorTask()
    add_scheduled_task(
        system_metrics_task.execute,
        'interval',
        minutes=15,
        id="system_metrics_collector_task",
        replace_existing=True
    )
    # registered_tasks["system_metrics_task"] = system_metrics_task

    # Приклад додавання завдання, яке виконується щодня о 3:00 ночі (інший приклад, якщо потрібно)
    # add_scheduled_task(some_other_function, 'cron', hour=3, minute=0)

    # Додайте сюди інші ваші заплановані завдання
    # Наприклад, для синхронізації, відправки сповіщень, оновлення рейтингів тощо.
    # Згідно з structure-claude-v2.md, сюди можуть входити:
    # - tasks.system.cleanup.CleanupTask
    # - tasks.system.backup.DatabaseBackupTask
    # - tasks.system.monitoring.SystemMetricsCollectorTask
    # - tasks.notifications.email.SendEmailTask (для масових розсилок або повторних спроб)
    # - tasks.integrations.calendar.SyncCalendarTask
    # - tasks.gamification.levels.RecalculateUserLevelsTask
    # - tasks.gamification.badges.AwardBadgesTask
    # - tasks.gamification.ratings.UpdateUserRatingsTask

    logger.info("Заплановані завдання ініціалізовано.")


async def init_scheduler():
    """
    Ініціалізує та запускає планувальник завдань.
    Цю функцію слід викликати при старті FastAPI додатку.
    """
    try:
        if not scheduler.running:
            initialize_scheduled_tasks() # Додавання всіх завдань
            scheduler.start()
            logger.info("Планувальник завдань APScheduler запущено.")
        else:
            logger.info("Планувальник завдань APScheduler вже запущено.")
    except Exception as e:
        logger.error(f"Помилка запуску планувальника APScheduler: {e}", exc_info=True)
        # Можливо, тут варто прокинути виняток далі, щоб зупинити запуск додатку
        # raise

async def shutdown_scheduler(wait: bool = True):
    """
    Коректно зупиняє планувальник завдань.
    Цю функцію слід викликати при зупинці FastAPI додатку.

    Args:
        wait (bool): Чи чекати завершення поточних завдань.
    """
    try:
        if scheduler.running:
            scheduler.shutdown(wait=wait)
            logger.info(f"Планувальник завдань APScheduler зупинено (очікування завершення: {wait}).")
        else:
            logger.info("Планувальник завдань APScheduler не був запущений.")
    except Exception as e:
        logger.error(f"Помилка зупинки планувальника APScheduler: {e}", exc_info=True)

# Приклад того, як це може бути інтегровано з FastAPI (в main.py):
#
# from app.src.tasks.scheduler import init_scheduler, shutdown_scheduler
#
# @app.on_event("startup")
# async def startup_event():
#     # ... інші ініціалізації ...
#     await init_scheduler()
#
# @app.on_event("shutdown")
# async def shutdown_event():
#     # ... інші операції при зупинці ...
#     await shutdown_scheduler()

# Для тестування цього модуля окремо:
# async def main():
#     logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#     await init_scheduler()
#     try:
#         # Дати планувальнику попрацювати деякий час
#         while True:
#             await asyncio.sleep(1)
#     except (KeyboardInterrupt, SystemExit):
#         await shutdown_scheduler()

# if __name__ == "__main__":
#     asyncio.run(main())
