# backend/app/src/schemas/groups/settings.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `GroupSettingsModel`.
Схеми використовуються для валідації даних при створенні (хоча налаштування
зазвичай створюються разом з групою або за замовчуванням), оновленні
та відображенні налаштувань групи.
"""

from pydantic import Field, model_validator
from typing import Optional, List, Dict, Any # Додано Dict, Any для custom_settings
import uuid
from datetime import datetime, time # Додано time для daily_standup_time

from backend.app.src.schemas.base import BaseSchema, AuditDatesSchema # IdentifiedSchema, TimestampedSchema
# Потрібно буде імпортувати схему BonusTypeSchema для зв'язку
# from backend.app.src.schemas.dictionaries.bonus_type import BonusTypeSchema (приклад)
from typing import ForwardRef

BonusTypeSchema = ForwardRef('backend.app.src.schemas.dictionaries.bonus_type.BonusTypeSchema')

# --- Схема для відображення налаштувань групи (для читання) ---
class GroupSettingsSchema(AuditDatesSchema): # Успадковує id, created_at, updated_at
    """
    Схема для представлення налаштувань групи.
    """
    group_id: uuid.UUID = Field(..., description="ID групи, до якої належать ці налаштування")

    # Налаштування бонусів
    currency_name: Optional[str] = Field(None, max_length=100, description="Назва валюти бонусів для групи")
    bonus_type_id: Optional[uuid.UUID] = Field(None, description="ID обраного типу бонусу з довідника")
    # selected_bonus_type: Optional[BonusTypeSchema] = None # Розгорнутий об'єкт типу бонусу
    allow_decimal_bonuses: bool = Field(..., description="Чи дозволені дробові значення для бонусів")
    max_debt_allowed: Optional[float] = Field(None, description="Максимально допустимий борг (використовуємо float для Numeric)")
                                           # Pydantic не має прямого аналога Numeric, float або Decimal з 'decimal' типу
                                           # Якщо потрібна висока точність, краще використовувати Decimal.
                                           # from decimal import Decimal; max_debt_allowed: Optional[Decimal]

    # Налаштування завдань/подій
    task_proposals_enabled: bool = Field(..., description="Чи можуть користувачі пропонувати завдання")
    task_reviews_enabled: bool = Field(..., description="Чи можуть користувачі залишати відгуки/рейтинги на завдання")
    default_task_visibility: str = Field(..., description="Видимість завдань за замовчуванням ('all_members', 'assignees_only')")

    # Налаштування сповіщень
    notify_admin_on_task_completion_check: bool = Field(..., description="Сповіщати адміна, коли завдання позначено 'на перевірку'")
    notify_user_on_task_status_change: bool = Field(..., description="Сповіщати користувача про зміну статусу його завдання")
    notify_user_on_account_change: bool = Field(..., description="Сповіщати користувача про рухи по його рахунку")
    task_deadline_reminder_days: Optional[int] = Field(None, ge=0, description="За скільки днів до дедлайну надсилати нагадування (NULL - вимкнено)")

    # Налаштування приватності та видимості
    profile_visibility: str = Field(..., description="Налаштування видимості профілів учасників ('public_in_group', 'admins_only')")
    activity_feed_enabled: bool = Field(..., description="Чи ввімкнена стрічка активності в групі")

    # Інтеграції
    calendar_integration_enabled: bool = Field(..., description="Чи ввімкнена інтеграція з календарями")
    default_calendar_id: Optional[str] = Field(None, max_length=255, description="Зовнішній ID календаря за замовчуванням для групи")

    # Інші налаштування
    welcome_message: Optional[str] = Field(None, description="Привітальне повідомлення для нових учасників групи")
    daily_standup_time: Optional[time] = Field(None, description="Час для щоденного стендапу (тільки час)")

    # Налаштування гейміфікації
    levels_enabled: bool = Field(..., description="Чи ввімкнена система рівнів")
    badges_enabled: bool = Field(..., description="Чи ввімкнена система бейджів")

    custom_settings: Optional[Dict[str, Any]] = Field(None, description="Додаткові кастомні налаштування групи (JSON)")

# --- Схема для створення налаштувань групи (зазвичай не використовується окремо від створення групи) ---
# Якщо налаштування створюються разом з групою, вони можуть бути частиною GroupCreateSchema.
# Або ж, якщо є дефолтні налаштування, то ця схема може не знадобитися.
# Поки що створюємо для повноти, але з коментарем.
class GroupSettingsCreateSchema(BaseSchema):
    """
    Схема для створення налаштувань групи.
    Зазвичай налаштування створюються з значеннями за замовчуванням при створенні групи.
    Ця схема може використовуватися, якщо потрібно явно задати налаштування при створенні.
    """
    # group_id: uuid.UUID # Встановлюється автоматично при зв'язуванні з групою

    currency_name: Optional[str] = Field(None, max_length=100)
    bonus_type_id: Optional[uuid.UUID] = Field(None)
    allow_decimal_bonuses: bool = Field(default=False)
    max_debt_allowed: Optional[float] = Field(None) # Або Decimal

    task_proposals_enabled: bool = Field(default=True)
    task_reviews_enabled: bool = Field(default=True)
    default_task_visibility: str = Field(default="all_members")

    notify_admin_on_task_completion_check: bool = Field(default=True)
    notify_user_on_task_status_change: bool = Field(default=True)
    notify_user_on_account_change: bool = Field(default=True)
    task_deadline_reminder_days: Optional[int] = Field(None, ge=0)

    profile_visibility: str = Field(default="public_in_group")
    activity_feed_enabled: bool = Field(default=True)

    calendar_integration_enabled: bool = Field(default=False)
    default_calendar_id: Optional[str] = Field(None, max_length=255)

    welcome_message: Optional[str] = Field(None)
    daily_standup_time: Optional[time] = Field(None)

    levels_enabled: bool = Field(default=True)
    badges_enabled: bool = Field(default=True)

    custom_settings: Optional[Dict[str, Any]] = Field(None)


# --- Схема для оновлення налаштувань групи ---
class GroupSettingsUpdateSchema(BaseSchema):
    """
    Схема для оновлення налаштувань групи. Всі поля опціональні.
    """
    currency_name: Optional[str] = Field(None, max_length=100)
    bonus_type_id: Optional[uuid.UUID] = Field(None)
    allow_decimal_bonuses: Optional[bool] = Field(None)
    max_debt_allowed: Optional[float] = Field(None) # Або Decimal

    task_proposals_enabled: Optional[bool] = Field(None)
    task_reviews_enabled: Optional[bool] = Field(None)
    default_task_visibility: Optional[str] = Field(None)

    notify_admin_on_task_completion_check: Optional[bool] = Field(None)
    notify_user_on_task_status_change: Optional[bool] = Field(None)
    notify_user_on_account_change: Optional[bool] = Field(None)
    task_deadline_reminder_days: Optional[int] = Field(None, ge=0) # Дозволяємо NULL для вимкнення

    profile_visibility: Optional[str] = Field(None)
    activity_feed_enabled: Optional[bool] = Field(None)

    calendar_integration_enabled: Optional[bool] = Field(None)
    default_calendar_id: Optional[str] = Field(None, max_length=255)

    welcome_message: Optional[str] = Field(None)
    daily_standup_time: Optional[time] = Field(None) # Дозволяємо NULL для видалення часу

    levels_enabled: Optional[bool] = Field(None)
    badges_enabled: Optional[bool] = Field(None)

    custom_settings: Optional[Dict[str, Any]] = Field(None) # Для оновлення всього JSON або його частини

    # TODO: Додати валідатори для default_task_visibility, profile_visibility,
    # щоб значення були з дозволеного списку (якщо це Enum або фіксований набір).

# GroupSettingsSchema.model_rebuild() # Якщо є залежності від інших схем, що визначаються пізніше

# TODO: Переконатися, що схеми відповідають моделі `GroupSettingsModel`.
# `GroupSettingsModel` успадковує від `BaseModel` (id, created_at, updated_at).
# `GroupSettingsSchema` успадковує від `AuditDatesSchema` і додає всі поля налаштувань.
# Поля: group_id, currency_name, bonus_type_id, allow_decimal_bonuses, max_debt_allowed,
# task_proposals_enabled, task_reviews_enabled, default_task_visibility,
# налаштування сповіщень, приватності, інтеграцій, welcome_message, daily_standup_time,
# налаштування гейміфікації, custom_settings.
# Це виглядає узгоджено.
#
# `GroupSettingsCreateSchema` містить поля з значеннями за замовчуванням,
# що відповідає логіці створення налаштувань з дефолтами.
# `GroupSettingsUpdateSchema` має всі поля як опціональні.
#
# Використання `float` для `max_debt_allowed` є наближенням до `Numeric`.
# Для фінансових даних краще використовувати `Decimal` з `from decimal import Decimal`.
# Поки що залишаю `float` для простоти, але з коментарем.
#
# `daily_standup_time` використовує `datetime.time`.
# `custom_settings` використовує `Dict[str, Any]` для JSONB.
#
# Зв'язок `selected_bonus_type: Optional[BonusTypeSchema]` закоментований,
# оскільки потребує імпорту `BonusTypeSchema` та `model_rebuild`.
# Це можна буде додати пізніше для розгортання інформації про тип бонусу.
# Поки що достатньо `bonus_type_id`.
#
# Все виглядає добре.
# Схема `GroupSettingsCreateSchema` може бути не потрібна, якщо налаштування
# завжди створюються з дефолтами сервісом при створенні групи.
# Однак, якщо API дозволяє передавати початкові налаштування, то вона корисна.
# Залишаю її для гнучкості.
# `AuditDatesSchema` надає `id, created_at, updated_at`.
# `group_id` є ключовим для зв'язку з `GroupModel`.
# `ge=0` для `task_deadline_reminder_days` (не може бути від'ємним).
# `max_length` для рядкових полів.
# Все виглядає коректно.
