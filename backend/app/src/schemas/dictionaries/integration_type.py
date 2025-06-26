# backend/app/src/schemas/dictionaries/integration_type.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `IntegrationModel` (довідник типів інтеграцій).
Схеми використовуються для валідації даних при створенні, оновленні
та відображенні типів зовнішніх інтеграцій.
"""

from pydantic import Field, HttpUrl
from typing import Optional, List, Dict, Any
import uuid

from backend.app.src.schemas.dictionaries.base_dict import BaseDictSchema, BaseDictCreateSchema, BaseDictUpdateSchema

# --- Схема для відображення типу інтеграції (для читання) ---
class IntegrationTypeSchema(BaseDictSchema):
    """
    Схема для представлення типу зовнішньої інтеграції. Успадковує всі поля від BaseDictSchema.
    Додає специфічне поле `category`.
    """
    # `IntegrationModel` має поле `category`.
    category: Optional[str] = Field(None, max_length=100, description="Категорія інтеграції (наприклад, 'messenger', 'calendar', 'task_tracker')")
    api_docs_url: Optional[HttpUrl] = Field(None, description="URL документації API для інтеграції") # type: ignore
    base_api_url: Optional[HttpUrl] = Field(None, description="Базовий URL API для інтеграції") # type: ignore
    required_settings_schema: Optional[Dict[str, Any]] = Field(None, description="JSON схема необхідних полів для налаштування цієї інтеграції")

# --- Схема для створення нового типу інтеграції ---
class IntegrationTypeCreateSchema(BaseDictCreateSchema):
    """
    Схема для створення нового типу інтеграції. Успадковує поля від BaseDictCreateSchema.
    Додає поле `category` та інші специфічні поля.
    """
    category: Optional[str] = Field(None, max_length=100, description="Категорія інтеграції")
    api_docs_url: Optional[HttpUrl] = Field(None, description="URL документації API") # type: ignore
    base_api_url: Optional[HttpUrl] = Field(None, description="Базовий URL API") # type: ignore
    required_settings_schema: Optional[Dict[str, Any]] = Field(None, description="JSON схема необхідних налаштувань")

# --- Схема для оновлення існуючого типу інтеграції ---
class IntegrationTypeUpdateSchema(BaseDictUpdateSchema):
    """
    Схема для оновлення існуючого типу інтеграції. Успадковує поля від BaseDictUpdateSchema.
    Додає поле `category` та інші специфічні поля.
    """
    category: Optional[str] = Field(None, max_length=100, description="Нова категорія інтеграції")
    api_docs_url: Optional[HttpUrl] = Field(None, description="Новий URL документації API") # type: ignore
    base_api_url: Optional[HttpUrl] = Field(None, description="Новий базовий URL API") # type: ignore
    required_settings_schema: Optional[Dict[str, Any]] = Field(None, description="Нова JSON схема необхідних налаштувань")

# TODO: Переконатися, що схеми відповідають моделі `IntegrationModel`.
# `IntegrationModel` успадковує від `BaseDictModel` і додає поле `category`.
# Схеми `IntegrationTypeSchema`, `IntegrationTypeCreateSchema`, `IntegrationTypeUpdateSchema`
# також успадковують від базових схем довідників і додають `category`.
# Це виглядає коректним.
#
# Назва файлу `integration_type.py` для схем відповідає `structure-claude-v3.md`,
# хоча модель називається `IntegrationModel`, а таблиця `integrations`.
# Назва схеми `IntegrationTypeSchema` також відповідає цій логіці.
#
# Поля `id, name, description, code, state_id, group_id, created_at, updated_at, deleted_at, is_deleted, notes`
# успадковуються з `BaseDictSchema`.
# `group_id` для типів інтеграцій, ймовірно, завжди буде `None`, оскільки це глобальний довідник.
#
# Валідація `code` успадкована.
# Поле `category` важливе для класифікації інтеграцій.
# Потенційні поля `api_docs_url` та `required_settings_schema` (якщо будуть в моделі)
# також відображені як закоментовані приклади.
# Все виглядає узгоджено.
# Приклади типів інтеграцій: Telegram, Google Calendar, Jira тощо, кожен зі своєю категорією.
# Ці типи потім використовуються для налаштування конкретних інтеграцій користувачами або групами.
