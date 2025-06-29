# backend/app/src/schemas/groups/settings.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `GroupSettingsModel`.
Схеми використовуються для валідації даних при створенні (хоча налаштування
зазвичай створюються разом з групою або за замовчуванням), оновленні
та відображенні налаштувань групи.
"""

from pydantic import Field, model_validator, field_validator
from typing import Optional, List, Dict, Any, ForwardRef
import uuid
from datetime import datetime, time
from decimal import Decimal # Використовуємо Decimal

from backend.app.src.schemas.base import BaseSchema, AuditDatesSchema
from typing import TYPE_CHECKING # Додано TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.src.schemas.dictionaries.bonus_type import BonusTypeSchema

# BonusTypeSchema = ForwardRef('backend.app.src.schemas.dictionaries.bonus_type.BonusTypeSchema') # Перенесено

# --- Схема для відображення налаштувань групи (для читання) ---
class GroupSettingsSchema(AuditDatesSchema): # Успадковує id, created_at, updated_at
    """
    Схема для представлення налаштувань групи.
    """
    group_id: uuid.UUID = Field(..., description="ID групи, до якої належать ці налаштування")

    # Налаштування бонусів
    currency_name: Optional[str] = Field(None, max_length=100, description="Назва валюти бонусів для групи")
    bonus_type_id: Optional[uuid.UUID] = Field(None, description="ID обраного типу бонусу з довідника")
    selected_bonus_type: Optional['BonusTypeSchema'] = Field(None, description="Розгорнутий об'єкт обраного типу бонусу") # Рядкове посилання
    allow_decimal_bonuses: bool = Field(..., description="Чи дозволені дробові значення для бонусів")
    max_debt_allowed: Optional[Decimal] = Field(None, description="Максимально допустимий борг")

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

# --- Схема для створення налаштувань групи ---
class GroupSettingsCreateSchema(BaseSchema):
    """
    Схема для створення налаштувань групи.
    """
    currency_name: Optional[str] = Field(None, max_length=100)
    bonus_type_id: Optional[uuid.UUID] = Field(None)
    allow_decimal_bonuses: bool = Field(default=False)
    max_debt_allowed: Optional[Decimal] = Field(None)

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

    @field_validator('default_task_visibility')
    @classmethod
    def validate_default_task_visibility_create(cls, value: str) -> str:
        allowed_values = ['all_members', 'assignees_only']
        if value not in allowed_values:
            raise ValueError(f"Недопустиме значення для default_task_visibility. Дозволені: {', '.join(allowed_values)}")
        return value

    @field_validator('profile_visibility')
    @classmethod
    def validate_profile_visibility_create(cls, value: str) -> str:
        allowed_values = ['public_in_group', 'admins_only']
        if value not in allowed_values:
            raise ValueError(f"Недопустиме значення для profile_visibility. Дозволені: {', '.join(allowed_values)}")
        return value

# --- Схема для оновлення налаштувань групи ---
class GroupSettingsUpdateSchema(BaseSchema):
    """
    Схема для оновлення налаштувань групи. Всі поля опціональні.
    """
    currency_name: Optional[str] = Field(None, max_length=100)
    bonus_type_id: Optional[uuid.UUID] = Field(None)
    allow_decimal_bonuses: Optional[bool] = Field(None)
    max_debt_allowed: Optional[Decimal] = Field(None)

    task_proposals_enabled: Optional[bool] = Field(None)
    task_reviews_enabled: Optional[bool] = Field(None)
    default_task_visibility: Optional[str] = Field(None)

    notify_admin_on_task_completion_check: Optional[bool] = Field(None)
    notify_user_on_task_status_change: Optional[bool] = Field(None)
    notify_user_on_account_change: Optional[bool] = Field(None)
    task_deadline_reminder_days: Optional[int] = Field(None, ge=0)

    profile_visibility: Optional[str] = Field(None)
    activity_feed_enabled: Optional[bool] = Field(None)

    calendar_integration_enabled: Optional[bool] = Field(None)
    default_calendar_id: Optional[str] = Field(None, max_length=255)

    welcome_message: Optional[str] = Field(None)
    daily_standup_time: Optional[time] = Field(None)

    levels_enabled: Optional[bool] = Field(None)
    badges_enabled: Optional[bool] = Field(None)

    custom_settings: Optional[Dict[str, Any]] = Field(None)

    @field_validator('default_task_visibility')
    @classmethod
    def validate_default_task_visibility_update(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            allowed_values = ['all_members', 'assignees_only']
            if value not in allowed_values:
                raise ValueError(f"Недопустиме значення для default_task_visibility. Дозволені: {', '.join(allowed_values)}")
        return value

    @field_validator('profile_visibility')
    @classmethod
    def validate_profile_visibility_update(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            allowed_values = ['public_in_group', 'admins_only']
            if value not in allowed_values:
                raise ValueError(f"Недопустиме значення для profile_visibility. Дозволені: {', '.join(allowed_values)}")
        return value

# GroupSettingsSchema.model_rebuild()
# BonusTypeSchema.model_rebuild() # Якщо BonusTypeSchema використовує ForwardRef на щось, що тут імпортується

# Перевірки:
# - `selected_bonus_type: Optional[BonusTypeSchema]` додано до `GroupSettingsSchema`.
# - `max_debt_allowed` тепер `Optional[Decimal]`.
# - Валідатори для `default_task_visibility` та `profile_visibility` додані до `GroupSettingsCreateSchema` (для значень за замовчуванням, хоча вони вже валідні) та `GroupSettingsUpdateSchema` (для нових значень).
# - Валідатори в CreateSchema перевіряють значення, що передаються (хоча тут вони мають default). Це корисно, якщо default буде змінено або якщо значення передаються явно.
# - `ge=0` для `task_deadline_reminder_days` в UpdateSchema також виправлено (було ge=0 в Create).
# - `daily_standup_time` дозволяє NULL в UpdateSchema.
# - `max_members` в `GroupSettingsUpdateSchema` (або `max_debt_allowed`) дозволяє NULL для зняття обмеження.
# - `from decimal import Decimal` додано.
# - `from pydantic import field_validator` (вже було, але перевірив).
#
# Все виглядає добре.
