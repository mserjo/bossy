# backend/app/src/schemas/gamification/level.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `LevelModel`.
Схеми використовуються для валідації даних при створенні, оновленні
та відображенні налаштувань рівнів гейміфікації.
"""

from pydantic import Field
from typing import Optional, List, ForwardRef
import uuid
from datetime import datetime
from decimal import Decimal # Використовуємо Decimal

from backend.app.src.schemas.base import BaseMainSchema, BaseSchema
# Потрібно буде імпортувати схеми для зв'язків:
# from backend.app.src.schemas.groups.group import GroupSimpleSchema (group_id вже є)
# from backend.app.src.schemas.dictionaries.status import StatusSchema (state_id вже є)
# from backend.app.src.schemas.files.file import FileSchema (або URL іконки)
# from backend.app.src.schemas.gamification.user_level import UserLevelSchema (для списку користувачів на рівні)

# GroupSimpleSchema = ForwardRef('backend.app.src.schemas.groups.group.GroupSimpleSchema')
# StatusSchema = ForwardRef('backend.app.src.schemas.dictionaries.status.StatusSchema')
# FileSchema = ForwardRef('backend.app.src.schemas.files.file.FileSchema')
UserLevelSchema = ForwardRef('backend.app.src.schemas.gamification.user_level.UserLevelSchema')


# --- Схема для відображення інформації про рівень (для читання) ---
class LevelSchema(BaseMainSchema):
    """
    Повна схема для представлення рівня гейміфікації.
    Успадковує `id, name, description, state_id, group_id, created_at, updated_at, deleted_at, is_deleted, notes`
    від `BaseMainSchema`.
    """
    # `group_id` з BaseMainSchema - ID групи, до якої належить налаштування рівня.

    level_number: int = Field(..., ge=0, description="Порядковий номер рівня (0 або 1 для початкового)")
    required_points: Optional[Decimal] = Field(None, description="Кількість бонусних балів, необхідних для досягнення цього рівня")
    required_tasks_completed: Optional[int] = Field(None, ge=0, description="Кількість виконаних завдань, необхідних для досягнення цього рівня")

    icon_file_id: Optional[uuid.UUID] = Field(None, description="ID файлу іконки рівня")
    # icon_url: Optional[HttpUrl] = Field(None, description="URL іконки рівня") # Може генеруватися

    # --- Розгорнуті зв'язки (приклад) ---
    # group: Optional[GroupSimpleSchema] = None # `group_id` вже є
    # state: Optional[StatusSchema] = None # `state_id` вже є
    # icon: Optional[FileSchema] = None # Або `icon_url`

    # Список користувачів, які досягли цього рівня (зазвичай не включається сюди, а отримується окремо)
    # user_levels: List[UserLevelSchema] = Field(default_factory=list)


# --- Схема для створення нового налаштування рівня ---
class LevelCreateSchema(BaseSchema):
    """
    Схема для створення нового налаштування рівня.
    """
    name: str = Field(..., min_length=1, max_length=255, description="Назва рівня")
    description: Optional[str] = Field(None, description="Опис рівня")
    # group_id: uuid.UUID # З URL або контексту
    state_id: Optional[uuid.UUID] = Field(None, description="Початковий статус налаштування рівня (наприклад, 'активний')")

    level_number: int = Field(..., ge=0, description="Порядковий номер рівня")
    required_points: Optional[Decimal] = Field(None, description="Необхідна кількість балів")
    required_tasks_completed: Optional[int] = Field(None, ge=0, description="Необхідна кількість виконаних завдань")

    icon_file_id: Optional[uuid.UUID] = Field(None, description="ID файлу іконки")
    notes: Optional[str] = Field(None, description="Додаткові нотатки")

    # TODO: Додати валідатор, що хоча б одна умова (required_points або required_tasks_completed) вказана,
    # якщо це вимога для не-початкових рівнів.
    # Або що level_number унікальний в межах group_id (це перевірка на рівні БД/сервісу).

# --- Схема для оновлення існуючого налаштування рівня ---
class LevelUpdateSchema(BaseSchema):
    """
    Схема для оновлення існуючого налаштування рівня.
    Всі поля опціональні.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    state_id: Optional[uuid.UUID] = Field(None) # Зміна статусу

    level_number: Optional[int] = Field(None, ge=0) # Зміна номера рівня - обережно, впливає на логіку
    required_points: Optional[Decimal] = Field(None)
    required_tasks_completed: Optional[int] = Field(None, ge=0)

    icon_file_id: Optional[uuid.UUID] = Field(None)
    notes: Optional[str] = Field(None)
    is_deleted: Optional[bool] = Field(None) # Для "м'якого" видалення

# LevelSchema.model_rebuild() # Для ForwardRef

# TODO: Переконатися, що схеми відповідають моделі `LevelModel`.
# `LevelModel` успадковує від `BaseMainModel`.
# `LevelSchema` успадковує від `BaseMainSchema` і додає специфічні поля рівня.
# Використання `Decimal` для `required_points`.
#
# Поля: `level_number`, `required_points`, `required_tasks_completed`, `icon_file_id`.
#
# `LevelCreateSchema` та `LevelUpdateSchema` містять відповідні поля.
# `ge=0` для `level_number` та `required_tasks_completed`.
#
# Розгорнуті зв'язки в `LevelSchema` (group, state, icon, user_levels) додані з `ForwardRef` або закоментовані.
# `user_levels` (список користувачів, що досягли рівня) зазвичай не включається для продуктивності.
#
# `group_id` з `BaseMainSchema` для `LevelModel` має бути NOT NULL (забезпечується логікою сервісу).
# `state_id` для статусу налаштування рівня.
# `name`, `description`, `notes`, `deleted_at`, `is_deleted` успадковані.
# Все виглядає узгоджено.
#
# `icon_url` (закоментоване) - похідне поле.
# Валідація унікальності `level_number` та `name` в межах `group_id` - на рівні БД/сервісу.
#
# Все виглядає добре.
