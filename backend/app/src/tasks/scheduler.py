# backend/app/src/tasks/scheduler.py
# -*- coding: utf-8 -*-
"""
Конфігурація планувальника завдань Celery Beat.

Цей модуль визначає словник `CELERY_BEAT_SCHEDULE`, який використовується
Celery Beat для запуску періодичних фонових завдань за розкладом.

Кожен запис у словнику визначає:
- `task`: Повний шлях до функції завдання Celery.
- `schedule`: Розклад виконання (наприклад, `crontab`, `timedelta`).
- `args`: (Опціонально) Позиційні аргументи для завдання.
- `kwargs`: (Опціонально) Іменовані аргументи для завдання.
- `options`: (Опціонально) Додаткові опції для завдання (наприклад, черга).
"""

from celery.schedules import crontab # Для розкладів cron-типу
# from datetime import timedelta # Для розкладів типу "кожні X секунд/хвилин/годин"

# TODO: Імпортувати реальні завдання або переконатися, що шляхи до них правильні,
# коли самі завдання будуть визначені в відповідних модулях.

CELERY_BEAT_SCHEDULE = {
    # --- Системні завдання ---
    'cleanup-old-logs-daily': {
        'task': 'backend.app.src.tasks.system.cleanup.cleanup_old_logs_task',
        'schedule': crontab(hour=3, minute=0), # Щоночі о 3:00
        'args': (90,), # Наприклад, видаляти логи, старші за 90 днів
        'options': {'queue': 'system_tasks'},
    },
    'backup-database-daily': {
        'task': 'backend.app.src.tasks.system.backup.backup_database_task',
        'schedule': crontab(hour=2, minute=0), # Щоночі о 2:00
        'options': {'queue': 'system_tasks'},
    },
    # TODO: Завдання для виконання користувацьких CronTask з моделі Cron (якщо такі є)
    # 'execute-dynamic-cron-tasks': {
    #     'task': 'backend.app.src.tasks.system.cron_task_executor.execute_due_cron_tasks',
    #     'schedule': crontab(minute='*/5'), # Кожні 5 хвилин
    #     'options': {'queue': 'system_tasks'},
    # },

    # --- Сповіщення ---
    'send-task-deadline-reminders': {
        'task': 'backend.app.src.tasks.notifications.reminders.send_task_deadline_reminders_task',
        'schedule': crontab(hour='*/1'), # Щогодини
        'options': {'queue': 'notification_tasks'},
    },
    # 'send-daily-activity-digest': { # Приклад
    #     'task': 'backend.app.src.tasks.notifications.digests.send_daily_activity_digest_task',
    #     'schedule': crontab(hour=7, minute=30), # Щодня о 7:30
    #     'options': {'queue': 'notification_tasks'},
    # },

    # --- Інтеграції ---
    'sync-all-active-calendar-integrations': {
        'task': 'backend.app.src.tasks.integrations.calendar.sync_all_active_calendars_task',
        'schedule': crontab(minute='*/30'), # Кожні 30 хвилин
        'options': {'queue': 'integration_tasks'},
    },
    # 'sync-all-active-tracker-integrations': {
    #     'task': 'backend.app.src.tasks.integrations.tracker.sync_all_active_trackers_task',
    #     'schedule': crontab(hour='*/2'), # Кожні 2 години
    #     'options': {'queue': 'integration_tasks'},
    # },

    # --- Гейміфікація ---
    'recalculate-user-ratings-nightly': {
        'task': 'backend.app.src.tasks.gamification.ratings.recalculate_all_group_ratings_task',
        'schedule': crontab(hour=1, minute=0), # Щоночі о 1:00
        'options': {'queue': 'gamification_tasks'},
    },
    'award-activity-badges-hourly': { # Приклад, якщо бейджі видаються за періодичну активність
        'task': 'backend.app.src.tasks.gamification.badges.award_periodic_activity_badges_task',
        'schedule': crontab(minute=0), # Щогодини
        'options': {'queue': 'gamification_tasks'},
    },

    # --- Специфічні для груп завдання (можуть запускатися загальним завданням, що перебирає групи) ---
    'process-group-specific-recurring-tasks': {
        'task': 'backend.app.src.tasks.system.group_tasks_processor.process_all_group_recurring_tasks',
        # Це завдання має ітерувати по групах та їх налаштуваннях для "Привітати з ДН", "Річниця в групі"
        'schedule': crontab(hour=6, minute=0), # Щодня о 6:00
        'options': {'queue': 'group_tasks'},
    },
}

# Цей словник `CELERY_BEAT_SCHEDULE` буде підхоплено Celery,
# якщо в конфігураційному файлі Celery (наприклад, `celery_app.py` або `config/celery.py`)
# вказано `app.conf.beat_schedule = CELERY_BEAT_SCHEDULE`
# та запущено Celery Beat.

# from backend.app.src.config.logging import get_logger # TODO: Розкоментувати, якщо потрібне логування
# logger = get_logger(__name__)
# logger.info("Celery Beat schedule configured.")

# Важливо: Самі функції завдань (наприклад, `cleanup_old_logs_task`) мають бути
# визначені у відповідних модулях та декоровані за допомогою `@celery_app.task`.
# Екземпляр `celery_app` має бути доступний для цих модулів.
