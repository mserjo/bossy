# backend/app/src/workers/celery_app.py
# -*- coding: utf-8 -*-
"""
Конфігурація та ініціалізація Celery додатку.

Цей модуль створює та налаштовує екземпляр Celery, який буде використовуватися
для виконання фонових завдань.
"""

from celery import Celery
from kombu import Queue

# TODO: Імпортувати налаштування Celery з конфігураційного файлу
# from backend.app.src.core.config import settings # Припускаючи, що там є CELERY_BROKER_URL, CELERY_RESULT_BACKEND тощо

# TODO: Тимчасові заглушки для налаштувань, поки settings не налаштовано повністю для Celery
class CelerySettingsStub:
    CELERY_BROKER_URL: str = "redis://localhost:6379/0" # Приклад
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1" # Приклад
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 30 * 60 # 30 хвилин
    CELERY_RESULT_EXTENDED: bool = True
    CELERY_WORKER_CONCURRENCY: Optional[int] = None # None - автовизначення за CPU
    CELERY_ACCEPT_CONTENT: List[str] = ['json', 'application/json']
    CELERY_TASK_SERIALIZER: str = 'json'
    CELERY_RESULT_SERIALIZER: str = 'json'
    CELERY_TIMEZONE: str = 'Europe/Kiev' # Або settings.TIMEZONE
    # CELERY_ENABLE_UTC: bool = True # За замовчуванням True, якщо TIMEZONE встановлено

    # Налаштування для Celery Beat (планувальника)
    CELERY_BEAT_SCHEDULER: str = 'django_celery_beat.schedulers:DatabaseScheduler' # Якщо використовується django-celery-beat
    # Або 'celery.beat.PersistentScheduler' для стандартного файлового шедулера
    # Або кастомний, якщо завдання визначаються в коді (як у нас в scheduler.py)
    # CELERY_BEAT_SCHEDULE_FILENAME: str = '/path/to/celerybeat-schedule' # Для PersistentScheduler

    # Якщо CELERY_BEAT_SCHEDULE визначається в коді (наприклад, в tasks/scheduler.py)
    # то його потрібно буде завантажити в конфігурацію app.conf.beat_schedule

    # Черги завдань (приклади)
    CELERY_TASK_QUEUES: tuple = (
        Queue('default', routing_key='task.default'),
        Queue('system_tasks', routing_key='task.system'),
        Queue('notification_tasks', routing_key='task.notification'),
        Queue('integration_tasks', routing_key='task.integration'),
        Queue('gamification_tasks', routing_key='task.gamification'),
        Queue('group_tasks', routing_key='task.group'),
    )
    CELERY_TASK_DEFAULT_QUEUE: str = 'default'
    CELERY_TASK_DEFAULT_EXCHANGE: str = 'tasks'
    CELERY_TASK_DEFAULT_EXCHANGE_TYPE: str = 'topic'
    CELERY_TASK_DEFAULT_ROUTING_KEY: str = 'task.default'

    # TODO: Можливо, CELERY_IMPORTS для автодискавері завдань
    CELERY_IMPORTS: tuple = (
        'backend.app.src.tasks.system.cleanup',
        'backend.app.src.tasks.system.backup',
        'backend.app.src.tasks.system.cron_task_executor',
        'backend.app.src.tasks.system.group_tasks_processor',
        'backend.app.src.tasks.notifications.reminders',
        'backend.app.src.tasks.notifications.digests',
        'backend.app.src.tasks.notifications.email',
        'backend.app.src.tasks.notifications.sms',
        'backend.app.src.tasks.notifications.messenger',
        'backend.app.src.tasks.integrations.calendar',
        'backend.app.src.tasks.integrations.messenger', # Обробка вхідних, якщо є
        'backend.app.src.tasks.integrations.tracker',
        'backend.app.src.tasks.gamification.levels',
        'backend.app.src.tasks.gamification.badges',
        'backend.app.src.tasks.gamification.ratings',
        # Додати інші модулі з завданнями Celery
    )

settings = CelerySettingsStub() # Використовуємо заглушку

# Створення екземпляру Celery
# Перший аргумент - назва поточного модуля, важлива для автогенерації імен завдань.
# Другий аргумент - broker URL.
celery_app = Celery(
    'bossy_tasks', # Назва проекту або модуля
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=settings.CELERY_IMPORTS # Список модулів, де Celery шукатиме завдання
)

# Завантаження конфігурації з об'єкта settings
# celery_app.config_from_object(settings, namespace='CELERY')
# Або встановлюємо налаштування вручну:
celery_app.conf.update(
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    result_extended=settings.CELERY_RESULT_EXTENDED,
    worker_concurrency=settings.CELERY_WORKER_CONCURRENCY,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    timezone=settings.CELERY_TIMEZONE,
    # enable_utc=settings.CELERY_ENABLE_UTC, # Зазвичай встановлюється автоматично з timezone

    # Налаштування черг
    task_queues=settings.CELERY_TASK_QUEUES,
    task_default_queue=settings.CELERY_TASK_DEFAULT_QUEUE,
    task_default_exchange=settings.CELERY_TASK_DEFAULT_EXCHANGE,
    task_default_exchange_type=settings.CELERY_TASK_DEFAULT_EXCHANGE_TYPE,
    task_default_routing_key=settings.CELERY_TASK_DEFAULT_ROUTING_KEY,
)


# Завантаження розкладу для Celery Beat
# Якщо CELERY_BEAT_SCHEDULE визначено в tasks/scheduler.py
try:
    from backend.app.src.tasks.scheduler import CELERY_BEAT_SCHEDULE
    celery_app.conf.beat_schedule = CELERY_BEAT_SCHEDULE
    celery_app.conf.beat_scheduler = 'celery.beat:PersistentScheduler' # Або інший, якщо потрібно
    # celery_app.conf.beat_schedule_filename = '/tmp/celerybeat-schedule' # Для PersistentScheduler, якщо не django-celery-beat
except ImportError:
    # logger = get_logger(__name__) # Потрібен logger
    # logger.warning("CELERY_BEAT_SCHEDULE не знайдено в tasks.scheduler. Періодичні завдання не будуть запущені.")
    print("WARNING: CELERY_BEAT_SCHEDULE not found in tasks.scheduler. Periodic tasks will not be scheduled.")


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


# Експорт екземпляру celery_app для використання в декораторах завдань
# та для запуску воркера.
__all__ = ('celery_app',)
