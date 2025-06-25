# backend/app/src/config/celery.py
# -*- coding: utf-8 -*-
"""
Цей модуль відповідає за налаштування Celery для виконання фонових завдань.
Celery використовує брокер повідомлень (наприклад, RabbitMQ або Redis)
та може використовувати бекенд результатів (наприклад, Redis або PostgreSQL)
для зберігання статусів та результатів завдань.
"""

from celery import Celery # type: ignore # Celery може не мати повних стабів
from kombu import Exchange, Queue # type: ignore # Для налаштування черг

# Імпорт налаштувань Celery з settings.py
from backend.app.src.config.settings import settings
from backend.app.src.config.logging import logger # Використовуємо налаштований логгер

# Створення екземпляра Celery.
# Перший аргумент - назва поточного модуля (для генерації імен завдань).
# `broker` та `backend` беруться з налаштувань.

# Перевіряємо, чи налаштування Celery доступні
if settings.celery and settings.celery.CELERY_BROKER_URL:
    celery_app = Celery(
        # Назва додатку Celery, зазвичай назва основного модуля проекту
        # або просто 'tasks'. Можна взяти з settings.app.APP_NAME.
        settings.app.APP_NAME.lower().replace(" ", "_") + "_celery",
        broker=str(settings.celery.CELERY_BROKER_URL), # URL брокера
        backend=str(settings.celery.CELERY_RESULT_BACKEND_URL) if settings.celery.CELERY_RESULT_BACKEND_URL else None, # URL бекенда результатів (опціонально)
        include=[ # Список модулів, де Celery буде шукати задачі (@app.task)
            # Наприклад:
            'backend.app.src.workers.system_tasks', # TODO: Створити цей модуль
            'backend.app.src.workers.notification_tasks', # TODO: Створити цей модуль
            'backend.app.src.workers.integration_tasks', # TODO: Створити цей модуль
            # ... інші модулі з задачами ...
            # Ці шляхи мають відповідати структурі проекту, де будуть визначені Celery tasks.
            # Поки що це заглушки, оскільки модулі `workers` ще не створені.
        ]
    )

    # --- Конфігурація Celery ---
    # Завантаження конфігурації з об'єкта (можна створити окремий клас CeleryConfig)
    # або напряму встановлювати параметри.
    # celery_app.config_from_object('backend.app.src.config.celery_config.CeleryConfig') # Якщо є окремий файл/клас конфігурації

    # Деякі важливі налаштування:
    # Часовий пояс (рекомендовано UTC)
    celery_app.conf.timezone = 'UTC'

    # Серіалізатор завдань та результатів
    celery_app.conf.task_serializer = 'json'
    celery_app.conf.result_serializer = 'json'
    celery_app.conf.accept_content = ['json'] # Дозволені формати контенту

    # Налаштування надійності та обробки помилок
    # celery_app.conf.task_acks_late = True # Підтвердження після виконання задачі (для надійності)
    # celery_app.conf.worker_prefetch_multiplier = 1 # По одній задачі на воркера (для довгих задач)
    # celery_app.conf.task_reject_on_worker_lost = True # Відхиляти задачі, якщо воркер втрачено

    # Налаштування Celery Beat (планувальник періодичних задач)
    # celery_app.conf.beat_schedule = {
    #     'example-periodic-task': {
    #         'task': 'backend.app.src.workers.system_tasks.run_example_task', # Шлях до задачі
    #         'schedule': timedelta(seconds=30), # Виконувати кожні 30 секунд
    #         # 'schedule': crontab(hour=7, minute=30, day_of_week=1), # Або crontab
    #         'args': (16, 16), # Аргументи для задачі
    #     },
    # }
    # TODO: Налаштування beat_schedule буде залежати від конкретних періодичних задач.
    # Можливо, вони будуть завантажуватися з CronTaskModel.

    # Налаштування черг (якщо потрібно розділяти задачі за пріоритетом або типом)
    # celery_app.conf.task_default_queue = 'default'
    # celery_app.conf.task_queues = (
    #     Queue('default', Exchange('default'), routing_key='default'),
    #     Queue('high_priority', Exchange('high_priority'), routing_key='high_priority'),
    #     Queue('low_priority', Exchange('low_priority'), routing_key='low_priority'),
    # )
    # # Приклад маршрутизації задач
    # celery_app.conf.task_routes = {
    #     'backend.app.src.workers.notification_tasks.send_email_task': {'queue': 'high_priority'},
    #     'backend.app.src.workers.system_tasks.cleanup_old_logs_task': {'queue': 'low_priority'},
    # }
    # TODO: Налаштувати черги та маршрутизацію, якщо це потрібно для проекту.

    # Якщо Celery працює в тому ж процесі, що й FastAPI (для розробки/тестування)
    # if getattr(settings.celery, "CELERY_TASK_ALWAYS_EAGER", False):
    #     celery_app.conf.task_always_eager = True
    #     # celery_app.conf.task_eager_propagates = True # Поширювати винятки

    logger.info("Celery додаток налаштовано.")

else:
    # Якщо Celery не налаштований, створюємо "пустий" об'єкт або None,
    # щоб уникнути помилок при імпорті в інших частинах коду.
    celery_app = None # type: ignore
    logger.warning("Налаштування Celery (CELERY_BROKER_URL) не знайдено. Celery не буде використовуватися.")


# Приклад визначення задачі (має бути в модулях, вказаних в `include`):
# from backend.app.src.config.celery import celery_app
#
# @celery_app.task(name="add_together") # Явне ім'я задачі
# def add(x: int, y: int) -> int:
#     return x + y

# Щоб запустити воркера Celery:
# celery -A backend.app.src.config.celery.celery_app worker -l info
# (шлях `-A` має вказувати на екземпляр `celery_app`)
# Або, якщо `main.py` імпортує та створює `celery_app`:
# celery -A backend.app.main.celery_app worker -l info
#
# Щоб запустити Celery Beat (планувальник):
# celery -A backend.app.src.config.celery.celery_app beat -l info

# TODO: Переконатися, що шляхи в `include` та для задач в `beat_schedule` / `task_routes`
# відповідають реальній структурі проекту, коли модулі `workers` будуть створені.
#
# TODO: Розглянути можливість завантаження `beat_schedule` з бази даних (з `CronTaskModel`),
# щоб періодичні задачі можна було налаштовувати динамічно через адмін-інтерфейс.
# Це потребує кастомного шедулера для Celery Beat або періодичного оновлення конфігурації.
#
# Налаштування `task_acks_late`, `worker_prefetch_multiplier`, `task_reject_on_worker_lost`
# важливі для надійності, але їх значення залежать від типу задач та вимог.
#
# `include` - це список модулів, де Celery буде автоматично шукати задачі,
# декоровані `@celery_app.task`.
#
# Якщо `settings.celery` або `settings.celery.CELERY_BROKER_URL` не задані,
# `celery_app` буде `None`, і спроби використовувати його (наприклад, `my_task.delay()`)
# призведуть до помилки. Це потрібно обробляти в коді, який викликає задачі,
# або гарантувати, що Celery завжди налаштований, якщо він використовується.
# Поточна логіка дозволяє "м'яку" відмову.
#
# Все готово для базового налаштування Celery.
# Подальша конфігурація (черги, beat) залежатиме від конкретних потреб.
