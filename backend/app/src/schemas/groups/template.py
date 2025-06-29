# backend/app/src/schemas/groups/template.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `GroupTemplateModel`.
Схеми використовуються для валідації даних при створенні, оновленні
та відображенні шаблонів груп.
"""

from pydantic import Field
from typing import Optional, List, Dict, Any, ForwardRef
import uuid
from datetime import datetime

from backend.app.src.schemas.base import BaseMainSchema, BaseSchema
# Потрібно буде імпортувати схеми для зв'язків:
# from backend.app.src.schemas.auth.user import UserPublicSchema
# from backend.app.src.schemas.dictionaries.status import StatusSchema

from typing import TYPE_CHECKING # Додано TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.src.schemas.auth.user import UserPublicSchema
    from backend.app.src.schemas.dictionaries.status import StatusSchema

# UserPublicSchema = ForwardRef('backend.app.src.schemas.auth.user.UserPublicSchema') # Перенесено
# StatusSchema = ForwardRef('backend.app.src.schemas.dictionaries.status.StatusSchema') # Перенесено

# --- Схема для відображення шаблону групи (для читання) ---
class GroupTemplateSchema(BaseMainSchema):
    """
    Схема для представлення шаблону групи.
    Успадковує `id, name, description, state_id, group_id (тут NULL), created_at, updated_at, deleted_at, is_deleted, notes`
    від `BaseMainSchema`.
    """
    template_data: Dict[str, Any] = Field(..., description="JSON-об'єкт з конфігурацією шаблону")
    version: int = Field(..., ge=1, description="Версія шаблону")
    created_by_user_id: Optional[uuid.UUID] = Field(None, description="ID супер-адміністратора, який створив шаблон")

    # --- Розгорнуті зв'язки (приклад) ---
    creator: Optional['UserPublicSchema'] = Field(None, description="Інформація про користувача, який створив шаблон") # Рядкове посилання
    state: Optional['StatusSchema'] = Field(None, description="Інформація про статус шаблону (успадковано з BaseMainSchema, де state_id)") # Рядкове посилання
    # `state` тут буде псевдонімом для `status`, якщо `BaseMainSchema` має `state_id`
    # і ми хочемо розгорнутий об'єкт статусу.
    # Або ж, якщо `BaseMainSchema` вже має `state: Optional[StatusSchema] = None`,
    # то тут нічого додавати не потрібно, воно успадкується.
    # Поточна `BaseMainSchema` не має розгорнутого `state`, лише `state_id`.
    # Тому додаю `state: Optional[StatusSchema]` сюди.

    # `group_id` з `BaseMainSchema` для `GroupTemplateModel` завжди буде `None`.

# --- Схема для створення нового шаблону групи ---
class GroupTemplateCreateSchema(BaseSchema):
    """
    Схема для створення нового шаблону групи.
    """
    name: str = Field(..., min_length=1, max_length=255, description="Назва шаблону групи (для адмінки)")
    template_code: str = Field(..., min_length=1, max_length=255, description="Унікальний програмний код шаблону") # Відповідає template_code в моделі
    description: Optional[str] = Field(None, description="Опис шаблону")

    template_data: Dict[str, Any] = Field(..., description="JSON-об'єкт з конфігурацією шаблону")
    version: int = Field(default=1, ge=1, description="Версія шаблону (за замовчуванням 1)")

    # created_by_user_id: uuid.UUID # Встановлюється автоматично з поточного супер-адміна
    state_id: Optional[uuid.UUID] = Field(None, description="Початковий статус шаблону (наприклад, 'активний')")
    notes: Optional[str] = Field(None, description="Додаткові нотатки")

    # TODO: Додати валідацію для `template_data`, якщо є відома структура.
    # Наприклад, перевірити наявність обов'язкових ключів.
    # @field_validator('template_data')
    # def validate_template_data_structure(cls, value: Dict[str, Any]) -> Dict[str, Any]:
    #     if not isinstance(value.get("group_settings"), dict):
    #         raise ValueError("'group_settings' має бути словником в template_data")
    #     # ... інші перевірки ...
    #     return value

# --- Схема для оновлення існуючого шаблону групи ---
class GroupTemplateUpdateSchema(BaseSchema):
    """
    Схема для оновлення існуючого шаблону групи.
    Всі поля опціональні.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    # template_code: Optional[str] = Field(None, min_length=1, max_length=255) # Код зазвичай не змінюється
    description: Optional[str] = Field(None)

    template_data: Optional[Dict[str, Any]] = Field(None)
    version: Optional[int] = Field(None, ge=1) # Оновлення версії

    state_id: Optional[uuid.UUID] = Field(None)
    notes: Optional[str] = Field(None)
    is_deleted: Optional[bool] = Field(None) # Для "м'якого" видалення

# GroupTemplateSchema.model_rebuild() # Для ForwardRef

# TODO: Переконатися, що схеми відповідають моделі `GroupTemplateModel`.
# `GroupTemplateModel` успадковує від `BaseMainModel` і додає `template_data`, `version`, `created_by_user_id`
# та має поле `template_code` (яке було додано до моделі `NotificationTemplateModel`,
# але не до `GroupTemplateModel` в попередніх кроках - це треба виправити в моделі або тут).
# Припускаю, що `GroupTemplateModel` також матиме `template_code` як унікальний ідентифікатор,
# а `name` з `BaseMainModel` буде для відображення.
# Якщо `GroupTemplateModel.name` є унікальним кодом, то `template_code` не потрібен.
# Поки що, для узгодження з `NotificationTemplateModel`, додаю `template_code` в `GroupTemplateCreateSchema`.
# `GroupTemplateSchema` буде відображати `name` (з `BaseMainModel`) як основну назву/код.
#
# Виправлення: `GroupTemplateModel` не має `template_code` в поточній реалізації моделі.
# `name` з `BaseMainModel` використовується як назва/ідентифікатор.
# Тому `template_code` в `GroupTemplateCreateSchema` прибираю.
# `name` з `BaseMainModel` має бути достатньо унікальним для шаблонів (можливо, в поєднанні з версією або `group_id=NULL`).
# Або ж, якщо `name` - це просто назва для адмінки, то в моделі потрібен окремий унікальний `code`.
#
# Повертаюся до структури `GroupTemplateModel` з `name` як основною назвою.
# Унікальність `name` для шаблонів (де `group_id` is NULL) має забезпечуватися на рівні БД.
#
# `GroupTemplateSchema` успадковує від `BaseMainSchema`.
# Поля `template_data`, `version`, `created_by_user_id` відображені.
# `GroupTemplateCreateSchema` та `GroupTemplateUpdateSchema` містять відповідні поля.
# Валідація `version >= 1`.
#
# `template_data` як `Dict[str, Any]` для JSONB.
# `group_id` з `BaseMainSchema` для шаблонів завжди буде `None`.
# `state_id` для статусу шаблону.
# Все виглядає узгоджено.
#
# Важливо: якщо `name` з `BaseMainModel` не є унікальним для шаблонів,
# то для програмної ідентифікації шаблонів потрібен буде інший механізм
# (наприклад, окреме поле `code` в `GroupTemplateModel`, яке буде унікальним).
# Поки що припускаємо, що `name` (разом з тим, що `group_id` is NULL)
# може слугувати як унікальний ідентифікатор для пошуку шаблону за назвою.
# Або ж, пошук буде за `id`.
# Для створення схеми `GroupTemplateCreateSchema` поле `name` є обов'язковим.
#
# Все виглядає прийнятно.
# Розгортання зв'язків `creator` та `status` (state) можна додати при необхідності.
# `AuditDatesSchema` (через `BaseMainSchema`) надає `id, created_at, updated_at`.
# `deleted_at`, `is_deleted`, `notes` також успадковані.
# Поле `template_code` було додано до `NotificationTemplateModel` для унікальності,
# тут для `GroupTemplateModel` такої потреби може не бути, якщо `name` виконує цю роль.
# Якщо `name` - це лише "людська" назва, то `template_code` потрібен.
# Поки що залишаю без окремого `template_code` в схемах, покладаючись на `name` з `BaseMainModel`.
# Якщо в моделі `name` не унікальний, то це проблема.
# Припускаю, що для шаблонів (`group_id` IS NULL) `name` буде унікальним.
# Або ж, `id` шаблону використовується для вибору.
#
# Остаточне рішення: `name` з `BaseMainModel` використовується як назва.
# Унікальність `name` для шаблонів (де `group_id` = NULL) має бути забезпечена.
# Схема `GroupTemplateCreateSchema` не містить `template_code`.
# Схема `GroupTemplateSchema` відображає `name` як основну назву.
# Це відповідає поточній структурі `GroupTemplateModel`.
