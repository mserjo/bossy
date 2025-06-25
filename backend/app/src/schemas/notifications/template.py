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
    # `name` з BaseMainSchema - назва шаблону для адміністрування.
    # `group_id` з BaseMainSchema - ID групи, якщо шаблон специфічний для групи (NULL для глобальних).

    template_code: str = Field(..., max_length=255, description="Унікальний програмний код шаблону")
    notification_type_code: str = Field(..., max_length=100, description="Код типу сповіщення, для якого призначений шаблон")
    channel_code: str = Field(..., max_length=50, description="Код каналу доставки (наприклад, 'IN_APP', 'EMAIL_BODY_HTML')")
    language_code: str = Field(..., max_length=10, description="Код мови шаблону (наприклад, 'uk', 'en')")
    template_content: str = Field(..., description="Вміст шаблону (може містити плейсхолдери)")

    # --- Розгорнуті зв'язки (приклад) ---
    # group: Optional[GroupSimpleSchema] = None # `group_id` вже є
    # state: Optional[StatusSchema] = None # `state_id` вже є


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
    notification_type_code: str = Field(..., max_length=100, description="Код типу сповіщення")
    channel_code: str = Field(..., max_length=50, description="Код каналу доставки")
    language_code: str = Field(..., max_length=10, description="Код мови шаблону")
    template_content: str = Field(..., description="Вміст шаблону")
    notes: Optional[str] = Field(None, description="Додаткові нотатки")

    # TODO: Додати валідатори для кодів (type, channel, language), щоб вони були з дозволених списків/Enum.
    # TODO: Додати валідатор для `template_code` на унікальність (це перевірка на рівні БД).
    # Тут можна перевірити формат, якщо є специфічні вимоги.

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
    notification_type_code: Optional[str] = Field(None, max_length=100)
    channel_code: Optional[str] = Field(None, max_length=50)
    language_code: Optional[str] = Field(None, max_length=10)
    template_content: Optional[str] = Field(None)
    notes: Optional[str] = Field(None)
    is_deleted: Optional[bool] = Field(None) # Для "м'якого" видалення

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
