# backend/app/src/schemas/notifications/template.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `NotificationTemplateModel`.
Схеми використовуються для валідації даних при створенні, оновленні
та відображенні шаблонів сповіщень.
"""

from pydantic import Field
from typing import Optional, List, ForwardRef
import uuid
from datetime import datetime

from backend.app.src.schemas.base import BaseMainSchema, BaseSchema
# Потрібно буде імпортувати схеми для зв'язків:
# from backend.app.src.schemas.groups.group import GroupSimpleSchema (group_id вже є)
# from backend.app.src.schemas.dictionaries.status import StatusSchema (state_id вже є)
from backend.app.src.core.dicts import NotificationChannelEnum # Імпорт Enum для каналів
# TODO: Імпортувати Enum для notification_type_code, коли він буде створений в core.dicts
# from backend.app.src.core.dicts import NotificationTypeEnum

GroupSimpleSchema = ForwardRef('backend.app.src.schemas.groups.group.GroupSimpleSchema')
StatusSchema = ForwardRef('backend.app.src.schemas.dictionaries.status.StatusSchema')

# --- Схема для відображення інформації про шаблон сповіщення (для читання) ---
class NotificationTemplateSchema(BaseMainSchema):
    """
    Повна схема для представлення шаблону сповіщення.
    Успадковує `id, name (використовується як назва для адмінки), description, state_id, group_id,
    created_at, updated_at, deleted_at, is_deleted, notes`
    від `BaseMainSchema`.
    """
    template_code: str = Field(..., max_length=255, description="Унікальний програмний код шаблону")
    # notification_type_code: NotificationTypeEnum = Field(..., description="Тип сповіщення, для якого призначений шаблон") # Використання Enum
    notification_type_code: str = Field(..., max_length=100, description="Код типу сповіщення, для якого призначений шаблон") # Поки що рядок
    channel_code: NotificationChannelEnum = Field(..., description="Канал доставки")
    language_code: str = Field(..., max_length=10, description="Код мови шаблону (наприклад, 'uk', 'en')")
    template_content: str = Field(..., description="Вміст шаблону (може містити плейсхолдери)")

    # --- Розгорнуті зв'язки (приклад) ---
    group: Optional[GroupSimpleSchema] = Field(None, description="Група, до якої належить шаблон (якщо є)")
    state: Optional[StatusSchema] = Field(None, description="Статус шаблону")


# --- Схема для створення нового шаблону сповіщення ---
class NotificationTemplateCreateSchema(BaseSchema):
    """
    Схема для створення нового шаблону сповіщення.
    """
    name: str = Field(..., min_length=1, max_length=255, description="Назва шаблону (для адмінки)")
    description: Optional[str] = Field(None, description="Опис призначення шаблону")
    state_id: Optional[uuid.UUID] = Field(None, description="Початковий статус шаблону (наприклад, 'активний')")
    group_id: Optional[uuid.UUID] = Field(None, description="ID групи (якщо шаблон специфічний для групи)")

    template_code: str = Field(..., min_length=1, max_length=255, description="Унікальний програмний код шаблону")
    # notification_type_code: NotificationTypeEnum = Field(..., description="Тип сповіщення") # Використання Enum
    notification_type_code: str = Field(..., max_length=100, description="Код типу сповіщення") # Поки що рядок
    channel_code: NotificationChannelEnum = Field(..., description="Канал доставки")
    language_code: str = Field(..., max_length=10, description="Код мови шаблону")
    template_content: str = Field(..., description="Вміст шаблону")
    notes: Optional[str] = Field(None, description="Додаткові нотатки")

    @field_validator('language_code')
    @classmethod
    def validate_language_code(cls, value: str) -> str:
        # TODO: Використовувати SUPPORTED_LOCALES з i18n.py або settings
        # from backend.app.src.core.i18n import SUPPORTED_LOCALES
        supported_languages = ["uk", "en"] # Тимчасово
        if value.lower() not in supported_languages:
            raise ValueError(f"Непідтримуваний код мови: '{value}'. Дозволені: {', '.join(supported_languages)}.")
        return value.lower()

# --- Схема для оновлення існуючого шаблону сповіщення ---
class NotificationTemplateUpdateSchema(BaseSchema):
    """
    Схема для оновлення існуючого шаблону сповіщення.
    Всі поля опціональні.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    state_id: Optional[uuid.UUID] = Field(None) # Зміна статусу
    group_id: Optional[uuid.UUID] = Field(None) # Зміна прив'язки до групи (обережно)

    # template_code: Optional[str] = Field(None, min_length=1, max_length=255) # Код зазвичай не змінюється
    # notification_type_code: Optional[NotificationTypeEnum] = Field(None)
    notification_type_code: Optional[str] = Field(None, max_length=100)
    channel_code: Optional[NotificationChannelEnum] = Field(None)
    language_code: Optional[str] = Field(None, max_length=10)
    template_content: Optional[str] = Field(None)
    notes: Optional[str] = Field(None)
    is_deleted: Optional[bool] = Field(None) # Для "м'якого" видалення

    @field_validator('language_code')
    @classmethod
    def validate_language_code_optional(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            supported_languages = ["uk", "en"] # Тимчасово
            if value.lower() not in supported_languages:
                raise ValueError(f"Непідтримуваний код мови: '{value}'. Дозволені: {', '.join(supported_languages)}.")
            return value.lower()
        return value

# NotificationTemplateSchema.model_rebuild() # Для ForwardRef

# TODO: Переконатися, що схеми відповідають моделі `NotificationTemplateModel`.
# `NotificationTemplateModel` успадковує від `BaseMainModel` і додає
# `template_code`, `notification_type_code`, `channel_code`, `language_code`, `template_content`.
# `NotificationTemplateSchema` успадковує від `BaseMainSchema` і відображає ці поля.
#
# `name` з `BaseMainModel` використовується як назва для адмінки.
# `template_code` - унікальний програмний ідентифікатор.
#
# `NotificationTemplateCreateSchema` та `NotificationTemplateUpdateSchema` містять відповідні поля.
#
# Розгорнуті зв'язки в `NotificationTemplateSchema` (group, state) успадковані.
#
# Все виглядає узгоджено.
# `AuditDatesSchema` (через `BaseMainSchema`) надає `id, created_at, updated_at`.
# `deleted_at`, `is_deleted`, `notes` також успадковані.
#
# Важливо, щоб комбінація (`template_code`) або
# (`notification_type_code`, `channel_code`, `language_code`, `group_id` з урахуванням NULL)
# була унікальною для коректного вибору шаблону.
# Модель `NotificationTemplateModel` має унікальний `template_code`.
# Сервіс буде відповідати за пошук потрібного `template_code` на основі
# типу сповіщення, каналу, мови та групи (з логікою пріоритетів: груповий -> глобальний).
#
# Все виглядає добре.
