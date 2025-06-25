# backend/app/src/schemas/system/cron_task.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `CronTaskModel`.
Схеми використовуються для валідації даних при створенні, оновленні
та відображенні системних cron-задач.
"""

from pydantic import Field, field_validator, model_validator
from typing import Optional, Dict, Any
import uuid
from datetime import datetime, timedelta # timedelta для `interval_schedule`

from backend.app.src.schemas.base import BaseMainSchema, BaseSchema # Успадковуємо від BaseMainSchema для CRUD
from backend.app.src.schemas.dictionaries.status import StatusSchema # Для відображення статусу

# --- Схема для відображення cron-задачі (для читання) ---
class CronTaskSchema(BaseMainSchema):
    """
    Схема для представлення системної cron-задачі.
    Успадковує `id, name, description, state_id, group_id (тут NULL), created_at, updated_at, deleted_at, is_deleted, notes`
    від `BaseMainSchema`.
    """
    task_identifier: str = Field(..., description="Унікальний ідентифікатор задачі в системі планувальника (наприклад, шлях до функції)")
    cron_expression: Optional[str] = Field(None, description="Вираз cron для періодичних задач (наприклад, '0 0 * * *')")
    run_once_at: Optional[datetime] = Field(None, description="Дата та час для разового запуску задачі")
    interval_schedule: Optional[timedelta] = Field(None, description="Інтервал для задач, що повторюються (наприклад, кожні 5 хвилин)")
    task_parameters: Optional[Dict[str, Any]] = Field(None, description="Параметри, що передаються у задачу під час виконання (JSON)")

    last_run_at: Optional[datetime] = Field(None, description="Час останнього успішного запуску задачі")
    next_run_at: Optional[datetime] = Field(None, description="Розрахунковий час наступного запуску задачі")
    is_enabled: bool = Field(..., description="Прапорець, чи активна задача для виконання")
    timeout_seconds: Optional[int] = Field(None, ge=0, description="Максимальний час виконання задачі в секундах")

    last_run_status: Optional[str] = Field(None, description="Статус останнього виконання ('success', 'failure', 'running')")
    last_run_log: Optional[str] = Field(None, description="Лог або повідомлення про помилку останнього виконання")

    # Зв'язок зі статусом (якщо state_id є в BaseMainSchema і хочемо розгорнутий об'єкт)
    # state: Optional[StatusSchema] = None # Буде автоматично завантажено, якщо є в моделі та from_attributes=True

    # `group_id` з `BaseMainSchema` тут буде `None`, оскільки це системні задачі.

    # @model_validator(mode='before')
    # @classmethod
    # def interval_to_timedelta(cls, data: Any) -> Any:
    #     # Якщо interval_schedule з БД приходить як рядок або інший тип,
    #     # його треба конвертувати в timedelta. SQLAlchemy зазвичай робить це автоматично для типу Interval.
    #     # Цей валідатор може бути непотрібним, якщо SQLAlchemy ORM коректно обробляє тип Interval.
    #     if isinstance(data, dict) and 'interval_schedule' in data and data['interval_schedule'] is not None:
    #         # Приклад, якщо б interval_schedule зберігався як { "seconds": 300 }
    #         # if isinstance(data['interval_schedule'], dict) and 'seconds' in data['interval_schedule']:
    #         #     data['interval_schedule'] = timedelta(seconds=data['interval_schedule']['seconds'])
    #         pass # Залежить від формату зберігання/передачі
    #     return data
    pass


# --- Схема для створення нової cron-задачі ---
class CronTaskCreateSchema(BaseSchema):
    """
    Схема для створення нової системної cron-задачі.
    """
    name: str = Field(..., min_length=1, max_length=255, description="Назва cron-задачі")
    description: Optional[str] = Field(None, description="Детальний опис задачі")
    state_id: Optional[uuid.UUID] = Field(None, description="Ідентифікатор статусу задачі (наприклад, 'активна')")

    task_identifier: str = Field(..., description="Ідентифікатор задачі в планувальнику")

    cron_expression: Optional[str] = Field(None, description="Cron-вираз")
    run_once_at: Optional[datetime] = Field(None, description="Час разового запуску")
    # Для interval_schedule очікуємо кількість секунд як int, або рядок типу "5 minutes", "1 day"
    # який потім буде конвертовано в timedelta на сервісному рівні.
    # Або ж, якщо модель приймає timedelta, то тут теж може бути timedelta.
    # Поки що, для простоти API, можна очікувати рядок або словник.
    # Наприклад: interval_seconds: Optional[int]
    interval_seconds: Optional[int] = Field(None, ge=1, description="Інтервал повторення в секундах (якщо використовується)")

    task_parameters: Optional[Dict[str, Any]] = Field(None, description="Параметри задачі (JSON)")

    is_enabled: bool = Field(default=True, description="Чи активна задача для виконання")
    timeout_seconds: Optional[int] = Field(None, ge=0, description="Тайм-аут виконання в секундах")
    notes: Optional[str] = Field(None, description="Додаткові нотатки")

    # Валідація, щоб був вказаний лише один тип розкладу
    @model_validator(mode='after')
    def check_schedule_type_exclusive(cls, data: 'CronTaskCreateSchema') -> 'CronTaskCreateSchema':
        schedule_fields = [data.cron_expression, data.run_once_at, data.interval_seconds]
        if sum(f is not None for f in schedule_fields) > 1:
            raise ValueError("Має бути вказаний лише один тип розкладу: cron_expression, run_once_at або interval_seconds.")
        # Можна додати перевірку, що хоча б один вказаний, якщо це вимога.
        # if sum(f is not None for f in schedule_fields) == 0:
        #     raise ValueError("Необхідно вказати тип розкладу: cron_expression, run_once_at або interval_seconds.")
        return data

    # TODO: Додати валідацію для cron_expression, якщо можливо (наприклад, через бібліотеку croniter).
    # @field_validator('cron_expression')
    # def validate_cron_expression(cls, value: Optional[str]) -> Optional[str]:
    #     if value is not None:
    #         try:
    #             # from croniter import croniter
    #             # if not croniter.is_valid(value):
    #             #     raise ValueError("Некоректний cron-вираз")
    #             # Проста перевірка на кількість частин
    #             if len(value.split()) not in [5, 6]: # 5 частин стандарт, 6 з секундами
    #                 raise ValueError("Cron-вираз повинен мати 5 або 6 частин")
    #         except Exception as e:
    #             raise ValueError(f"Помилка валідації cron-виразу: {e}")
    #     return value


# --- Схема для оновлення існуючої cron-задачі ---
class CronTaskUpdateSchema(BaseSchema):
    """
    Схема для оновлення існуючої системної cron-задачі.
    Всі поля опціональні.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    state_id: Optional[uuid.UUID] = Field(None)

    task_identifier: Optional[str] = Field(None) # Зазвичай не змінюється, але можливо

    cron_expression: Optional[str] = Field(None)
    run_once_at: Optional[datetime] = Field(None)
    interval_seconds: Optional[int] = Field(None, ge=1)

    task_parameters: Optional[Dict[str, Any]] = Field(None)

    is_enabled: Optional[bool] = Field(None)
    timeout_seconds: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = Field(None)
    is_deleted: Optional[bool] = Field(None) # Для "м'якого" видалення

    # Валідація ексклюзивності типів розкладу також потрібна тут,
    # але вона складніша, бо треба враховувати поточні значення з БД, якщо поля не передані.
    # Цю логіку краще залишити на сервісному рівні при оновленні.
    # Або ж, якщо передається один тип розкладу, інші автоматично стають None.
    # @model_validator(mode='after')
    # def check_schedule_type_exclusive_update(cls, data: 'CronTaskUpdateSchema') -> 'CronTaskUpdateSchema':
    #     # Потрібно знати, які поля були передані, а які ні.
    #     # Якщо, наприклад, передано cron_expression, то run_once_at та interval_seconds мають стати None.
    #     # Це краще обробляти в логіці оновлення.
    #     # ...
    #     return data
    pass


# TODO: Переконатися, що схеми відповідають моделі `CronTaskModel`.
# `CronTaskModel` успадковує від `BaseMainModel`.
# `CronTaskSchema` успадковує від `BaseMainSchema` і додає специфічні поля cron-задачі.
# Поля: task_identifier, cron_expression, run_once_at, interval_schedule (timedelta в моделі, interval_seconds в CreateSchema),
# task_parameters, last_run_at, next_run_at, is_enabled, timeout_seconds, last_run_status, last_run_log.
# `interval_schedule` в `CronTaskSchema` має тип `Optional[timedelta]`.
# `CronTaskCreateSchema` має `interval_seconds: Optional[int]`, який сервіс має конвертувати в `timedelta` для моделі.
# Це нормальний підхід для API.
#
# Валідатор `check_schedule_type_exclusive` в `CronTaskCreateSchema` важливий.
# Валідація `cron_expression` також корисна.
# `group_id` з `BaseMainSchema` для `CronTaskSchema` буде `None` (системні задачі).
# `state_id` використовується для статусу задачі (активна, неактивна, помилка тощо).
# `is_enabled` - додатковий прапорець для швидкого ввімкнення/вимкнення.
# Все виглядає узгоджено.
# `deleted_at` та `is_deleted` успадковані для "м'якого" видалення.
# `notes` для додаткових нотаток.
# `BaseMainSchema` надає `id, name, description, created_at, updated_at`.
# Поле `state` (розгорнутий об'єкт статусу) може бути додано в `CronTaskSchema`, якщо потрібно.
# `model_validator` для `interval_to_timedelta` в `CronTaskSchema` закоментований,
# оскільки SQLAlchemy зазвичай коректно обробляє тип `Interval` в `timedelta`.
# Якщо ні, його можна буде розкоментувати та адаптувати.
# Все виглядає добре.
