# backend/app/src/schemas/gamification/badge.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `BadgeModel`.
Схеми використовуються для валідації даних при створенні, оновленні
та відображенні налаштувань бейджів гейміфікації.
"""

from pydantic import Field
from typing import Optional, List, Any, ForwardRef, Dict # Додано Dict
import uuid
from datetime import datetime

from backend.app.src.schemas.base import BaseMainSchema, BaseSchema
# Потрібно буде імпортувати схеми для зв'язків:
# from backend.app.src.schemas.groups.group import GroupSimpleSchema (group_id вже є)
# from backend.app.src.schemas.dictionaries.status import StatusSchema (state_id вже є)
# from backend.app.src.schemas.files.file import FileSchema (або URL іконки)
# from backend.app.src.schemas.gamification.achievement import AchievementSchema (для списку отриманих)

# GroupSimpleSchema = ForwardRef('backend.app.src.schemas.groups.group.GroupSimpleSchema')
# StatusSchema = ForwardRef('backend.app.src.schemas.dictionaries.status.StatusSchema')
# FileSchema = ForwardRef('backend.app.src.schemas.files.file.FileSchema')
AchievementSchema = ForwardRef('backend.app.src.schemas.gamification.achievement.AchievementSchema')

# --- Схема для відображення інформації про бейдж (для читання) ---
class BadgeSchema(BaseMainSchema):
    """
    Повна схема для представлення бейджа гейміфікації.
    Успадковує `id, name, description, state_id, group_id, created_at, updated_at, deleted_at, is_deleted, notes`
    від `BaseMainSchema`.
    """
    # `group_id` з BaseMainSchema - ID групи, до якої належить налаштування бейджа.

    condition_type_code: str = Field(..., max_length=100, description="Код типу умови для отримання бейджа")
    condition_details: Optional[Dict[str, Any]] = Field(None, description="Деталі умови у форматі JSON")

    icon_file_id: Optional[uuid.UUID] = Field(None, description="ID файлу іконки бейджа")
    # icon_url: Optional[HttpUrl] = Field(None, description="URL іконки бейджа") # Може генеруватися

    is_repeatable: bool = Field(..., description="Чи можна отримувати цей бейдж повторно")

    # --- Розгорнуті зв'язки (приклад) ---
    # group: Optional[GroupSimpleSchema] = Field(None, description="Група, якій належить бейдж") # `group_id` вже є
    state: Optional[ForwardRef('backend.app.src.schemas.dictionaries.status.StatusSchema')] = Field(None, description="Статус налаштування бейджа")
    icon: Optional[ForwardRef('backend.app.src.schemas.files.file.FileSchema')] = Field(None, description="Файл іконки бейджа") # Або `icon_url`

    # Список досягнень (хто і коли отримав цей бейдж)
    achievements: List[AchievementSchema] = Field(default_factory=list, description="Записи про отримання цього бейджа користувачами")


# --- Схема для створення нового налаштування бейджа ---
class BadgeCreateSchema(BaseSchema):
    """
    Схема для створення нового налаштування бейджа.
    """
    name: str = Field(..., min_length=1, max_length=255, description="Назва бейджа")
    description: Optional[str] = Field(None, description="Опис бейджа та умов його отримання")
    # group_id: uuid.UUID # З URL або контексту
    state_id: Optional[uuid.UUID] = Field(None, description="Початковий статус налаштування бейджа (наприклад, 'активний')")

    condition_type_code: str = Field(..., max_length=100, description="Код типу умови для отримання бейджа")
    condition_details: Optional[Dict[str, Any]] = Field(None, description="Деталі умови у форматі JSON")

    icon_file_id: Optional[uuid.UUID] = Field(None, description="ID файлу іконки бейджа")
    is_repeatable: bool = Field(default=False, description="Чи можна отримувати цей бейдж повторно (за замовчуванням False)")
    notes: Optional[str] = Field(None, description="Додаткові нотатки")

    # TODO: Додати валідатор для `condition_details` залежно від `condition_type_code`,
    # якщо є відома структура для кожного типу умови.

# --- Схема для оновлення існуючого налаштування бейджа ---
class BadgeUpdateSchema(BaseSchema):
    """
    Схема для оновлення існуючого налаштування бейджа.
    Всі поля опціональні.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    state_id: Optional[uuid.UUID] = Field(None) # Зміна статусу

    condition_type_code: Optional[str] = Field(None, max_length=100)
    condition_details: Optional[Dict[str, Any]] = Field(None) # Дозволяє оновити весь JSON або його частину (потребує логіки PATCH)

    icon_file_id: Optional[uuid.UUID] = Field(None)
    is_repeatable: Optional[bool] = Field(None)
    notes: Optional[str] = Field(None)
    is_deleted: Optional[bool] = Field(None) # Для "м'якого" видалення

# BadgeSchema.model_rebuild() # Для ForwardRef

# TODO: Переконатися, що схеми відповідають моделі `BadgeModel`.
# `BadgeModel` успадковує від `BaseMainModel`.
# `BadgeSchema` успадковує від `BaseMainSchema` і додає специфічні поля бейджа.
#
# Поля: `condition_type_code`, `condition_details` (JSONB в моделі, Dict в схемі),
# `icon_file_id`, `is_repeatable`.
#
# `BadgeCreateSchema` та `BadgeUpdateSchema` містять відповідні поля.
#
# Розгорнуті зв'язки в `BadgeSchema` (group, state, icon, achievements) додані з `ForwardRef` або закоментовані.
# `achievements` (список, хто отримав бейдж) зазвичай не включається для продуктивності.
#
# `group_id` з `BaseMainSchema` для `BadgeModel` має бути NOT NULL.
# `state_id` для статусу налаштування бейджа.
# `name`, `description`, `notes`, `deleted_at`, `is_deleted` успадковані.
# Все виглядає узгоджено.
#
# `icon_url` (закоментоване) - похідне поле.
# Валідація унікальності `name` в межах `group_id` - на рівні БД/сервісу.
# Валідація `condition_details` залежно від `condition_type_code` може бути складною
# і вимагати кастомних валідаторів або обробки на сервісному рівні.
# Поки що `condition_details` приймається як загальний `Dict`.
#
# Все виглядає добре.

BadgeSchema.model_rebuild()
BadgeCreateSchema.model_rebuild()
BadgeUpdateSchema.model_rebuild()
