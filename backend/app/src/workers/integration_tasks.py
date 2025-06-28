# backend/app/src/workers/integration_tasks.py
# -*- coding: utf-8 -*-
"""
Реєстрація або визначення фонових завдань Celery, пов'язаних з інтеграціями.

Аналогічно до інших `*_tasks.py` в цьому пакеті, цей модуль може:
1. Визначати завдання Celery для інтеграцій тут.
2. Або імпортувати завдання, визначені в `backend.app.src.tasks.integrations.*`,
   для їх реєстрації в Celery.
"""

# from backend.app.src.config.logging import get_logger
# logger = get_logger(__name__)

# Приклад імпорту завдань з пакету tasks/integrations/
# from backend.app.src.tasks.integrations.calendar import sync_all_active_calendars_task, sync_single_calendar_integration_task
# from backend.app.src.tasks.integrations.messenger import process_incoming_messenger_message_task
# from backend.app.src.tasks.integrations.tracker import sync_all_active_trackers_task, sync_single_tracker_integration_task

# logger.info("Завдання Celery для інтеграцій (посилання на tasks.integrations.*) зареєстровано.")

# Якщо CELERY_IMPORTS в celery_app.py вже включає шляхи до модулів в `tasks/integrations/`,
# то явний імпорт тут може бути не потрібний для простої реєстрації.
# Цей файл може слугувати для групування або якщо є специфічна логіка для воркера інтеграцій.

pass
