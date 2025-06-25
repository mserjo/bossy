# backend/app/src/schemas/reports/report.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `ReportModel`,
яка зберігає метадані про згенеровані звіти або запити на їх генерацію.
"""

from pydantic import Field, HttpUrl
from typing import Optional, List, Any, ForwardRef, Dict # Додано Dict
import uuid
from datetime import datetime

from backend.app.src.schemas.base import BaseSchema, AuditDatesSchema
# Потрібно буде імпортувати схеми для зв'язків:
# from backend.app.src.schemas.auth.user import UserPublicSchema
# from backend.app.src.schemas.groups.group import GroupSimpleSchema
# from backend.app.src.schemas.dictionaries.status import StatusSchema
# from backend.app.src.schemas.files.file import FileSchema # Або URL файлу

UserPublicSchema = ForwardRef('backend.app.src.schemas.auth.user.UserPublicSchema')
GroupSimpleSchema = ForwardRef('backend.app.src.schemas.groups.group.GroupSimpleSchema')
StatusSchema = ForwardRef('backend.app.src.schemas.dictionaries.status.StatusSchema')
FileSchema = ForwardRef('backend.app.src.schemas.files.file.FileSchema')

# --- Схема для відображення метаданих звіту (для читання) ---
class ReportSchema(AuditDatesSchema): # Успадковує id, created_at, updated_at
    """
    Схема для представлення метаданих про згенерований звіт або запит на нього.
    `created_at` - час запиту на звіт.
    `updated_at` - час останньої зміни статусу.
    """
    report_code: str = Field(..., max_length=100, description="Код (тип) звіту")
    requested_by_user_id: Optional[uuid.UUID] = Field(None, description="ID користувача, який замовив звіт")
    group_id: Optional[uuid.UUID] = Field(None, description="ID групи, для якої згенеровано звіт")

    parameters: Optional[Dict[str, Any]] = Field(None, description="Параметри, використані для генерації звіту (JSON)")
    status_id: uuid.UUID = Field(..., description="ID статусу генерації звіту")

    generated_at: Optional[datetime] = Field(None, description="Час, коли звіт був успішно згенерований")
    file_id: Optional[uuid.UUID] = Field(None, description="ID файлу, якщо звіт збережено як файл")
    # file_url: Optional[HttpUrl] = Field(None, description="URL для завантаження файлу звіту") # Може генеруватися

    # --- Розгорнуті зв'язки (приклад) ---
    requester: Optional[UserPublicSchema] = Field(None, description="Користувач, який замовив звіт")
    group: Optional[GroupSimpleSchema] = Field(None, description="Група, для якої звіт")
    status: Optional[StatusSchema] = Field(None, description="Статус генерації звіту")
    generated_file_info: Optional[FileSchema] = Field(None, alias="generated_file", description="Інформація про згенерований файл звіту")
    # `file_url` генерується сервісом і додається до `FileSchema` або окремо.


# --- Схема для створення запиту на генерацію звіту ---
# Ця схема буде дуже схожа на `ReportRequestSchema` з `request.py`,
# але `ReportCreateSchema` призначена для створення запису в `ReportModel` (зазвичай сервісом).
class ReportCreateSchema(BaseSchema):
    """
    Схема для створення запису про запит на генерацію звіту.
    Зазвичай використовується внутрішньою логікою системи.
    """
    report_code: str = Field(..., max_length=100, description="Код типу звіту")
    requested_by_user_id: Optional[uuid.UUID] = Field(None, description="ID користувача, який замовив звіт")
    group_id: Optional[uuid.UUID] = Field(None, description="ID групи (якщо звіт специфічний для групи)")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Параметри для генерації звіту")
    status_id: uuid.UUID = Field(..., description="Початковий ID статусу (наприклад, 'в черзі', 'замовлено')")

    # `generated_at` та `file_id` встановлюються пізніше, після генерації.
    # `id`, `created_at`, `updated_at` встановлюються автоматично.


# --- Схема для оновлення статусу або результатів генерації звіту ---
class ReportUpdateSchema(BaseSchema):
    """
    Схема для оновлення запису про звіт (наприклад, зміна статусу, додавання файлу).
    """
    status_id: Optional[uuid.UUID] = Field(None, description="Новий ID статусу генерації звіту")
    generated_at: Optional[datetime] = Field(None, description="Час успішної генерації (якщо змінюється)")
    file_id: Optional[uuid.UUID] = Field(None, description="ID згенерованого файлу (якщо змінюється або додається)")
    # parameters: Optional[Dict[str, Any]] # Параметри зазвичай не змінюються для існуючого запиту

    # Можна додати поля для оновлення помилок, якщо статус "помилка"
    # error_message: Optional[str] = Field(None, description="Повідомлення про помилку генерації")

# ReportSchema.model_rebuild() # Для ForwardRef

# TODO: Переконатися, що схеми відповідають моделі `ReportModel`.
# `ReportModel` успадковує від `BaseModel`.
# `ReportSchema` успадковує від `AuditDatesSchema` і відображає поля метаданих звіту.
#
# Поля: `report_code`, `requested_by_user_id`, `group_id`, `parameters` (JSONB/Dict),
# `status_id`, `generated_at`, `file_id`.
#
# `ReportCreateSchema` для створення запису в `ReportModel`.
# `ReportUpdateSchema` для оновлення статусу/результатів.
#
# Розгорнуті зв'язки в `ReportSchema` (requester, group, status, generated_file_info)
# додані з `ForwardRef` або як похідні поля (`file_url`).
#
# Все виглядає узгоджено.
# `AuditDatesSchema` надає `id, created_at, updated_at`.
# `created_at` - час запиту на звіт.
# `updated_at` - час останньої зміни (наприклад, статусу).
#
# `file_url` (закоментоване) - це похідне поле, яке генерується сервісом на основі `file_id`
# та конфігурації файлового сховища.
#
# Ця модель/схеми призначені для управління життєвим циклом генерації звітів,
# особливо якщо вони генеруються асинхронно.
# Самі дані звіту (якщо це не файл) будуть представлені іншими схемами
# (наприклад, в `response.py`).
#
# Все виглядає добре.
