# backend/app/src/workers/system_tasks.py
# -*- coding: utf-8 -*-
"""
Реєстрація або визначення системних фонових завдань Celery.

Цей модуль може:
1. Визначати системні завдання Celery безпосередньо тут.
2. Або імпортувати системні завдання, визначені в `backend.app.src.tasks.system.*`,
   щоб вони були зареєстровані в Celery додатку, якщо `CELERY_IMPORTS`
   включає цей модуль.

Перевага надається визначенню логіки завдань в пакеті `tasks/`,
а тут лише імпорту для реєстрації, якщо це потрібно.
"""

# from backend.app.src.config.logging import get_logger
# logger = get_logger(__name__)

# Приклад імпорту завдань з пакету tasks/system/ для їх реєстрації в Celery,
# якщо CELERY_IMPORTS в celery_app.py налаштований на цей модуль,
# або якщо використовується явне імпортування для реєстрації.

# from backend.app.src.tasks.system.cleanup import cleanup_old_logs_task, cleanup_temp_files_task, cleanup_stale_sessions_task
# from backend.app.src.tasks.system.backup import backup_database_task
# from backend.app.src.tasks.system.cron_task_executor import execute_due_cron_tasks
# from backend.app.src.tasks.system.group_tasks_processor import process_all_group_recurring_tasks

# logger.info("Системні завдання Celery (посилання на tasks.system.*) зареєстровано.")

# Якщо завдання визначаються тут (менш бажаний варіант, якщо вони вже є в tasks/):
# from backend.app.src.workers import celery_app as app
#
# @app.task(name="workers.system.example_worker_system_task")
# def example_worker_system_task(x, y):
#     logger.info(f"Виконується example_worker_system_task з {x} та {y}")
#     return x + y

# На даний момент, якщо всі завдання визначаються та імпортуються через
# `CELERY_IMPORTS` в `celery_app.py` безпосередньо з пакету `tasks`,
# цей файл може бути порожнім або містити лише коментарі.
# Його наявність може бути корисною, якщо структура проекту передбачає,
# що Celery шукає завдання саме в пакеті `workers`.

pass
