# backend/app/src/workers/celery_app.py
# -*- coding: utf-8 -*-
"""
Конфігурація та ініціалізація Celery додатку.

Цей модуль створює та налаштовує екземпляр Celery, який буде використовуватися
для виконання фонових завдань.
"""

from celery import Celery
from kombu import Queue

from typing import Optional, List # Додано для Optional, List
from backend.app.src.config.settings import settings as app_settings # Імпортуємо головні налаштування

# Використовуємо реальні налаштування, якщо Celery увімкнено
if app_settings.app.USE_CELERY and app_settings.celery:
    celery_config = app_settings.celery
    # Додаткові налаштування, які можуть бути не в CelerySettings, але потрібні для Celery
    CELERY_TASK_TRACK_STARTED = getattr(celery_config, 'CELERY_TASK_TRACK_STARTED', True)
    CELERY_TASK_TIME_LIMIT = getattr(celery_config, 'CELERY_TASK_TIME_LIMIT', 30 * 60)
    CELERY_RESULT_EXTENDED = getattr(celery_config, 'CELERY_RESULT_EXTENDED', True)
    CELERY_WORKER_CONCURRENCY = getattr(celery_config, 'CELERY_WORKER_CONCURRENCY', None)
    CELERY_ACCEPT_CONTENT = getattr(celery_config, 'CELERY_ACCEPT_CONTENT', ['json', 'application/json'])
    CELERY_TASK_SERIALIZER = getattr(celery_config, 'CELERY_TASK_SERIALIZER', 'json')
    CELERY_RESULT_SERIALIZER = getattr(celery_config, 'CELERY_RESULT_SERIALIZER', 'json')
    CELERY_TIMEZONE = getattr(celery_config, 'CELERY_TIMEZONE', 'Europe/Kiev') # Або app_settings.app.TIMEZONE
    # CELERY_ENABLE_UTC = getattr(celery_config, 'CELERY_ENABLE_UTC', True)

    CELERY_BEAT_SCHEDULER = getattr(celery_config, 'CELERY_BEAT_SCHEDULER', 'celery.beat:PersistentScheduler')
    CELERY_BEAT_SCHEDULE_FILENAME = getattr(celery_config, 'CELERY_BEAT_SCHEDULE_FILENAME', '/tmp/celerybeat-schedule')


    CELERY_TASK_QUEUES = getattr(celery_config, 'CELERY_TASK_QUEUES', (
        Queue('default', routing_key='task.default'),
        Queue('system_tasks', routing_key='task.system'),
        Queue('notification_tasks', routing_key='task.notification'),
        # Додати інші черги, якщо потрібно
    ))
    CELERY_TASK_DEFAULT_QUEUE = getattr(celery_config, 'CELERY_TASK_DEFAULT_QUEUE', 'default')
    CELERY_TASK_DEFAULT_EXCHANGE = getattr(celery_config, 'CELERY_TASK_DEFAULT_EXCHANGE', 'tasks')
    CELERY_TASK_DEFAULT_EXCHANGE_TYPE = getattr(celery_config, 'CELERY_TASK_DEFAULT_EXCHANGE_TYPE', 'topic')
    CELERY_TASK_DEFAULT_ROUTING_KEY = getattr(celery_config, 'CELERY_TASK_DEFAULT_ROUTING_KEY', 'task.default')

    CELERY_IMPORTS = getattr(celery_config, 'CELERY_IMPORTS', (
        'backend.app.src.tasks.system.cleanup', # Приклад
        # 'backend.app.src.tasks.notifications.email', # Приклад
        # Додати інші модулі з завданнями Celery
    ))
    BROKER_URL = str(celery_config.CELERY_BROKER_URL) if celery_config.CELERY_BROKER_URL else None
    RESULT_BACKEND = str(celery_config.CELERY_RESULT_BACKEND_URL) if celery_config.CELERY_RESULT_BACKEND_URL else None
else:
    # Заглушки, якщо Celery вимкнено або не налаштовано, щоб файл міг імпортуватися без помилок
    # Але celery_app не буде функціональним.
    BROKER_URL = "redis://localhost:6379/0" # Заглушка
    RESULT_BACKEND = "redis://localhost:6379/1" # Заглушка
    CELERY_TASK_TRACK_STARTED = True
    CELERY_TASK_TIME_LIMIT = 1800
    CELERY_RESULT_EXTENDED = True
    CELERY_WORKER_CONCURRENCY = None
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_TIMEZONE = 'Europe/Kiev'
    CELERY_BEAT_SCHEDULER = 'celery.beat:PersistentScheduler'
    CELERY_BEAT_SCHEDULE_FILENAME = '/tmp/celerybeat-schedule-disabled'
    CELERY_TASK_QUEUES = (Queue('default'),)
    CELERY_TASK_DEFAULT_QUEUE = 'default'
    CELERY_TASK_DEFAULT_EXCHANGE = 'tasks'
    CELERY_TASK_DEFAULT_EXCHANGE_TYPE = 'topic'
    CELERY_TASK_DEFAULT_ROUTING_KEY = 'task.default'
    CELERY_IMPORTS = ()
    if not app_settings.app.USE_CELERY:
        print("INFO: Celery is disabled via USE_CELERY=False. Celery app will use stub settings.")
    else:
        print("WARNING: Celery is enabled (USE_CELERY=True) but Celery settings (app_settings.celery) are missing or incomplete. Celery app will use stub settings.")


# Створення екземпляру Celery
# Перший аргумент - назва поточного модуля, важлива для автогенерації імен завдань.
# Другий аргумент - broker URL.
celery_app = Celery(
    'bossy_tasks', # Назва проекту або модуля
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=CELERY_IMPORTS # Список модулів, де Celery шукатиме завдання
)

# Завантаження конфігурації з об'єкта settings
# celery_app.config_from_object(settings, namespace='CELERY')
# Або встановлюємо налаштування вручну:
celery_app.conf.update(
    task_track_started=CELERY_TASK_TRACK_STARTED,
    task_time_limit=CELERY_TASK_TIME_LIMIT,
    result_extended=CELERY_RESULT_EXTENDED,
    worker_concurrency=CELERY_WORKER_CONCURRENCY,
    accept_content=CELERY_ACCEPT_CONTENT,
    task_serializer=CELERY_TASK_SERIALIZER,
    result_serializer=CELERY_RESULT_SERIALIZER,
    timezone=CELERY_TIMEZONE,
    # enable_utc=settings.CELERY_ENABLE_UTC, # Зазвичай встановлюється автоматично з timezone

    # Налаштування черг
    task_queues=CELERY_TASK_QUEUES,
    task_default_queue=CELERY_TASK_DEFAULT_QUEUE,
    task_default_exchange=CELERY_TASK_DEFAULT_EXCHANGE,
    task_default_exchange_type=CELERY_TASK_DEFAULT_EXCHANGE_TYPE,
    task_default_routing_key=CELERY_TASK_DEFAULT_ROUTING_KEY,
)

# Налаштування Celery Beat, якщо увімкнено
if app_settings.app.USE_CELERY and app_settings.celery:
    celery_app.conf.beat_scheduler = CELERY_BEAT_SCHEDULER
    if CELERY_BEAT_SCHEDULER == 'celery.beat:PersistentScheduler':
        celery_app.conf.beat_schedule_filename = CELERY_BEAT_SCHEDULE_FILENAME

# Завантаження розкладу для Celery Beat
# Якщо CELERY_BEAT_SCHEDULE визначено в tasks/scheduler.py
try:
    from backend.app.src.tasks.scheduler import CELERY_BEAT_SCHEDULE
    if app_settings.app.USE_CELERY and app_settings.celery: # Застосовувати розклад тільки якщо Celery активний
        celery_app.conf.beat_schedule = CELERY_BEAT_SCHEDULE
except ImportError:
    # logger = get_logger(__name__) # Потрібен logger
    # logger.warning("CELERY_BEAT_SCHEDULE не знайдено в tasks.scheduler. Періодичні завдання не будуть запущені.")
    print("WARNING: CELERY_BEAT_SCHEDULE not found in tasks.scheduler. Periodic tasks will not be scheduled by default.")


# Автоматичне виявлення завдань (tasks) з модулів, вказаних в `include` або `CELERY_IMPORTS`.
# celery_app.autodiscover_tasks(lambda: settings.INSTALLED_APPS) # Для Django
# Для FastAPI, якщо завдання декоровані правильно, `include` в конструкторі Celery має бути достатньо.
# Або можна явно імпортувати модулі з завданнями тут, щоб вони зареєструвалися.
# Наприклад:
# import backend.app.src.tasks.system.cleanup
# import backend.app.src.tasks.notifications.email
# ... (але це вже зроблено через CELERY_IMPORTS та параметр include)

# from backend.app.src.config.logging import get_logger # TODO: Розкоментувати, якщо потрібне логування
# app_logger = get_logger(__name__)
# app_logger.info(f"Celery app '{celery_app.main}' configured with broker: {celery_app.conf.broker_url}")
print(f"Celery app '{celery_app.main}' configured with broker: {celery_app.conf.broker_url}")
if not (app_settings.app.USE_CELERY and app_settings.celery and app_settings.celery.CELERY_BROKER_URL):
    print(f"INFO: Celery app '{celery_app.main}' is using STUB/DEFAULT broker settings as Celery is disabled or not fully configured in settings.py.")

# Експорт екземпляру celery_app для використання в декораторах завдань
# та для запуску воркера.
__all__ = ('celery_app',)
