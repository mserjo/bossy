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

from app.src.tasks.system.cleanup import CleanupTask
from app.src.tasks.system.backup import DatabaseBackupTask
from app.src.tasks.system.monitoring import SystemMetricsCollectorTask
# from app.src.tasks.notifications.email import SendEmailTask # Example: Keep commented, event-driven mostly
# from app.src.tasks.notifications.sms import SendSmsTask # Example: Keep commented, event-driven mostly
# from app.src.tasks.notifications.messenger import SendMessengerNotificationTask # Example: Keep commented, event-driven mostly
from app.src.tasks.integrations.calendar import SyncCalendarTask # To be scheduled
# ProcessIncomingMessageTask зазвичай не додається в планувальник, а викликається вебхуками
from app.src.tasks.gamification.levels import RecalculateUserLevelsTask
from app.src.tasks.gamification.badges import AwardBadgesTask
from app.src.tasks.gamification.ratings import UpdateUserRatingsTask

# Налаштування логера для цього модуля
logger = logging.getLogger(__name__)

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

    # Додайте сюди інші ваші заплановані завдання
    # Наприклад, для синхронізації, відправки сповіщень, оновлення рейтингів тощо.
    # Згідно з structure-claude-v2.md, сюди можуть входити (деякі вже додані вище):
    # - tasks.system.cleanup.CleanupTask (вже реалізовано та заплановано)
    # - tasks.system.backup.DatabaseBackupTask (вже реалізовано та заплановано)
    # - tasks.system.monitoring.SystemMetricsCollectorTask (вже реалізовано та заплановано)
    # - tasks.notifications.email.SendEmailTask (для масових розсилок або повторних спроб) - див. приклади нижче
    # - tasks.integrations.calendar.SyncCalendarTask
    # - tasks.gamification.levels.RecalculateUserLevelsTask
    # - tasks.gamification.badges.AwardBadgesTask
    # - tasks.gamification.ratings.UpdateUserRatingsTask

    # --- Приклади для завдань сповіщень (зазвичай викликаються на вимогу, а не за розкладом) ---
    # logger.info("Ініціалізація завдань сповіщень (приклади, закоментовано)...")

    # Приклад: щотижневий дайджест новин на email (якщо такий функціонал потрібен)
    # weekly_digest_email_task = SendEmailTask(name="WeeklyDigestEmail")
    # add_scheduled_task(
    #     weekly_digest_email_task.execute,
    #     trigger='cron',
    #     day_of_week='mon', # Щопонеділка
    #     hour=9,
    #     minute=0,
    #     kwargs={ # Аргументи для методу run таска SendEmailTask
    #         "recipient_email": "all_users_group@example.com", # Потребує логіки отримання списку
    #         "subject": "Щотижневий Дайджест Kudos",
    #         "html_body": "<h1>Ваш тижневий дайджест...</h1><p>Деталі...</p>", # Потребує генерації контенту
    #         "text_body": "Ваш тижневий дайджест...
Деталі..."
    #     },
    #     id="weekly_digest_email_task",
    #     replace_existing=True
    # )

    # Приклад: щоденне SMS нагадування (дуже специфічний випадок)
    # daily_sms_reminder_task = SendSmsTask(name="DailyReminderSMS")
    # add_scheduled_task(
    #     daily_sms_reminder_task.execute,
    #     trigger='cron',
    #     hour=8,
    #     minute=0,
    #     kwargs={
    #         "phone_number": "+380XXXXXXXXX", # Конкретний номер або логіка вибору
    #         "message": "Щоденне нагадування від Kudos!"
    #     },
    #     id="daily_sms_reminder_task",
    #     replace_existing=True
    # )

    # Приклад: періодичне повідомлення в Telegram канал про оновлення
    # (якщо SendMessengerNotificationTask може приймати chat_id каналу)
    # telegram_update_task = SendMessengerNotificationTask(name="TelegramChannelUpdate")
    # add_scheduled_task(
    #     telegram_update_task.execute,
    #     trigger='interval',
    #     hours=6, # Кожні 6 годин
    #     kwargs={
    #         "target_identifier": "@kudos_channel_id", # ID каналу Telegram
    #         "message_text": "Перевірте останні оновлення в системі Kudos!",
    #         "platform": "telegram"
    #     },
    #     id="telegram_channel_update_task",
    #     replace_existing=True
    # )
    # --- Кінець прикладів для завдань сповіщень ---

    logger.info("Ініціалізація завдань інтеграцій...")

    # Приклад: періодична синхронізація календарів для активних користувачів
    # Ця логіка потребуватиме отримання списку користувачів з активними інтеграціями.
    # Тут показано лише концептуальний виклик для одного користувача/провайдера.
    # Важливо: user_id та calendar_provider мають бути реальними або мати механізм отримання.
    # Для прикладу, це завдання може бути заплановане для кожного активного користувача
    # з підключеним календарем, або мати внутрішню логіку для перебору користувачів.
    # Тут планується загальний таск, який, можливо, сам перебирає користувачів.
    sync_calendar_task_instance = SyncCalendarTask(name="AllUserCalendarSync")
    add_scheduled_task(
        sync_calendar_task_instance.execute, # Викликаємо execute, який потім викличе run
        trigger='interval',
        hours=1, # Наприклад, кожну годину
        kwargs={ # Ці kwargs будуть передані в SyncCalendarTask.run
            # "user_id": "all_active_users_with_calendar", # Спеціальний маркер або логіка всередині таска
            "calendar_provider": "all_available" # Або конкретний, якщо таск для одного провайдера
            # Додаткові kwargs можуть включати time_min, time_max, specific_calendar_ids тощо.
        },
        id="sync_all_calendars_hourly", # ID має бути унікальним
        replace_existing=True
    )

    # Примітка: ProcessIncomingMessageTask зазвичай не запускається за розкладом,
    # а викликається напряму вебхуком або іншим обробником подій, передаючи payload.
    # Наприклад:
    # incoming_message_task = ProcessIncomingMessageTask()
    # result = await incoming_message_task.execute(platform="telegram", payload=telegram_update_payload)
    # --- Кінець прикладів для завдань інтеграцій ---

    logger.info("Ініціалізація завдань гейміфікації...")

    # Завдання для перерахунку рівнів користувачів (наприклад, щогодини)
    # Може бути менш часто, залежно від активності системи та логіки нарахування досвіду.
    recalculate_levels_task = RecalculateUserLevelsTask()
    add_scheduled_task(
        recalculate_levels_task.execute, # Викликаємо execute з BaseTask
        trigger='interval',
        hours=1,
        id="recalculate_user_levels_task",
        replace_existing=True
        # Можна передати kwargs, якщо потрібно, наприклад, user_id=None для всіх
    )

    # Завдання для періодичної перевірки та видачі бейджів (наприклад, кожні 6 годин)
    # Цей таск також може викликатися подіями, але періодичний запуск може ловити умови,
    # які не пов'язані з миттєвими подіями (наприклад, стріки, загальна кількість балів).
    award_badges_periodic_task = AwardBadgesTask(name="PeriodicBadgeAwards") # Даємо інше ім'я для ясності
    add_scheduled_task(
        award_badges_periodic_task.execute, # Викликаємо без аргументів для періодичної перевірки
        trigger='interval',
        hours=6,
        id="periodic_badge_awards_task",
        replace_existing=True
    )

    # Завдання для оновлення рейтингів користувачів (наприклад, щодня о 01:00)
    # Можна запускати для всіх груп та глобальний рейтинг.
    update_ratings_task = UpdateUserRatingsTask()
    add_scheduled_task(
        update_ratings_task.execute,
        trigger='cron',
        hour=1,
        minute=0,
        day_of_week='*', # Щодня
        kwargs={"calculate_global": True, "rating_period": "daily"}, # Оновлювати і глобальний рейтинг, вказуємо період
        id="update_user_ratings_daily_task", # Унікальний ID для щоденного завдання
        replace_existing=True
    )

    # Можна додати ще одне завдання для оновлення рейтингів, наприклад, щотижневе/щомісячне
    # update_ratings_weekly_task = UpdateUserRatingsTask(name="WeeklyRatingsUpdate")
    # add_scheduled_task(
    #     update_ratings_weekly_task.execute,
    #     trigger='cron',
    #     day_of_week='sun', # Щонеділі
    #     hour=2, minute=0,
    #     kwargs={"calculate_global": True, "rating_period": "weekly"},
    #     id="update_user_ratings_weekly_task",
    #     replace_existing=True
    # )

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
