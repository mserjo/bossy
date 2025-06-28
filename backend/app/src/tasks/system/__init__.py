# backend/app/src/tasks/system/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету 'system' фонових завдань.

Цей пакет містить фонові завдання, пов'язані з загальними системними
операціями. Наприклад:
- `cleanup.py`: Завдання для періодичного очищення даних (старі логи,
  тимчасові файли, застарілі сесії тощо).
- `backup.py`: Завдання для створення резервних копій системи (наприклад, бази даних).
- `cron_task.py`: Завдання для виконання користувацьких системних задач,
  визначених в моделі CronTask.
- `monitoring.py`: Завдання для збору даних моніторингу системи.

Кожен файл зазвичай визначає одну або декілька функцій завдань
(наприклад, для Celery, декорованих `@celery_app.task`).

Цей файл робить каталог 'system' (в contexti tasks) пакетом Python.
Він може експортувати завдання для їх реєстрації в планувальнику
або для прямого виклику з інших частин системи.
"""

# TODO: Імпортувати та експортувати конкретні функції завдань,
# коли вони будуть визначені у файлах цього пакету.

# Приклад експорту для Celery завдань:
# from .cleanup import cleanup_old_logs_task, cleanup_temp_files_task
# from .backup import create_database_backup_task
# from .cron_task import execute_cron_task
# from .monitoring import collect_system_metrics_task
#
# __all__ = [
#     "cleanup_old_logs_task",
#     "cleanup_temp_files_task",
#     "create_database_backup_task",
#     "execute_cron_task",
#     "collect_system_metrics_task",
# ]

# На даний момент, поки завдання не визначені, файл може залишатися таким.
pass
