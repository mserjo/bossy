# backend/app/src/schemas/files/file.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `FileModel`.
Схеми використовуються для валідації даних при завантаженні файлів (створення метаданих),
оновленні метаданих та відображенні інформації про файли.
"""

from pydantic import Field, HttpUrl
from typing import Optional, List, Any, ForwardRef, Dict, TYPE_CHECKING # Додано TYPE_CHECKING
import uuid
from datetime import datetime

from backend.app.src.schemas.base import BaseSchema, AuditDatesSchema

if TYPE_CHECKING:
    from backend.app.src.schemas.auth.user import UserPublicSchema
    from backend.app.src.schemas.groups.group import GroupSimpleSchema
    # from backend.app.src.schemas.dictionaries.status import StatusSchema


# --- Схема для відображення метаданих файлу (для читання) ---
class FileSchema(AuditDatesSchema): # Успадковує id, created_at, updated_at
    """
    Схема для представлення метаданих про завантажений файл.
    `created_at` - час завантаження файлу.
    """
    # storage_path: str # Зазвичай не віддається клієнту напряму
    original_filename: str = Field(..., max_length=255, description="Оригінальна назва файлу")
    mime_type: str = Field(..., max_length=100, description="MIME-тип файлу")
    file_size_bytes: int = Field(..., ge=0, description="Розмір файлу в байтах")

    uploaded_by_user_id: Optional[uuid.UUID] = Field(None, description="ID користувача, який завантажив файл")
    group_context_id: Optional[uuid.UUID] = Field(None, description="ID групи, в контексті якої завантажено файл")

    file_category_code: Optional[str] = Field(None, max_length=50, description="Код категорії файлу (наприклад, 'AVATAR', 'TASK_ATTACHMENT')")
    additional_info: Optional[Dict[str, Any]] = Field(None, description="Додаткові метадані про файл (JSON)") # Перейменовано з metadata
    # status_id: Optional[uuid.UUID] = Field(None, description="ID статусу файлу (якщо є)")

    is_public: bool = Field(..., description="Чи є файл публічно доступним")

    # Додаткове поле для URL доступу до файлу (генерується сервісом)
    file_url: Optional[HttpUrl] = Field(None, description="URL для доступу/завантаження файлу")

    # --- Розгорнуті зв'язки (приклад) ---
    uploader: Optional['UserPublicSchema'] = Field(None, description="Користувач, який завантажив файл") # Використовуємо рядкове посилання
    group_context: Optional['GroupSimpleSchema'] = Field(None, description="Група, в контексті якої завантажено файл") # Використовуємо рядкове посилання
    # status: Optional['StatusSchema'] = Field(None, description="Статус файлу (якщо є)")


# --- Схема для створення метаданих файлу (після завантаження файлу на сервер/сховище) ---
class FileCreateSchema(BaseSchema):
    """
    Схема для створення запису метаданих файлу.
    Зазвичай використовується сервісом після успішного завантаження файлу.
    """
    storage_path: str = Field(..., max_length=1024, description="Шлях до файлу в сховищі (унікальний)")
    original_filename: str = Field(..., max_length=255, description="Оригінальна назва файлу")
    mime_type: str = Field(..., max_length=100, description="MIME-тип файлу")
    file_size_bytes: int = Field(..., ge=0, description="Розмір файлу в байтах")

    uploaded_by_user_id: Optional[uuid.UUID] = Field(None, description="ID користувача, який завантажив")
    group_context_id: Optional[uuid.UUID] = Field(None, description="ID групи-контексту")

    file_category_code: Optional[str] = Field(None, max_length=50, description="Код категорії файлу")
    additional_info: Optional[Dict[str, Any]] = Field(None, description="Додаткові метадані (JSON)") # Перейменовано з metadata
    # status_id: Optional[uuid.UUID] # Початковий статус (наприклад, "доступний")
    is_public: bool = Field(default=False, description="Чи є файл публічним (за замовчуванням False)")

    # `id`, `created_at`, `updated_at` встановлюються автоматично.


# --- Схема для оновлення метаданих файлу ---
class FileUpdateSchema(BaseSchema):
    """
    Схема для оновлення метаданих існуючого файлу.
    Дозволяє змінювати, наприклад, original_filename, file_category_code, metadata, is_public.
    `storage_path`, `mime_type`, `file_size_bytes` зазвичай не змінюються для вже завантаженого файлу.
    """
    original_filename: Optional[str] = Field(None, max_length=255)
    file_category_code: Optional[str] = Field(None, max_length=50)
    additional_info: Optional[Dict[str, Any]] = Field(None) # Перейменовано з metadata
    # status_id: Optional[uuid.UUID] = Field(None)
    is_public: Optional[bool] = Field(None)
    # group_context_id: Optional[uuid.UUID] # Зміна контексту групи - обережно

# FileSchema.model_rebuild() # Для ForwardRef

# TODO: Переконатися, що схеми відповідають моделі `FileModel`.
# `FileModel` успадковує від `BaseModel`.
# `FileSchema` успадковує від `AuditDatesSchema` і відображає поля метаданих файлу.
# Поле `storage_path` не включено в `FileSchema` для відповіді клієнту з міркувань безпеки,
# замість нього є `file_url` (яке генерується сервісом).
#
# Поля: `original_filename`, `mime_type`, `file_size_bytes`, `uploaded_by_user_id`,
# `group_context_id`, `file_category_code`, `metadata`, `is_public`.
# `status_id` (закоментоване) - якщо буде в моделі.
#
# `FileCreateSchema` містить всі необхідні поля для створення запису метаданих.
# `FileUpdateSchema` дозволяє оновлювати деякі метадані.
#
# Розгорнуті зв'язки в `FileSchema` (uploader, group_context, status) додані з `ForwardRef`.
#
# Все виглядає узгоджено.
# `AuditDatesSchema` надає `id, created_at, updated_at`.
# `created_at` - час завантаження файлу.
# `updated_at` - при зміні метаданих.
#
# `file_category_code` важливий для розрізнення призначення файлів (аватар, іконка групи, додаток до завдання тощо).
# `metadata` (JSONB/Dict) для зберігання специфічних для типу файлу даних (наприклад, розміри зображення).
#
# Все виглядає добре.
# Важливо, що API для завантаження файлів буде окремим, і після успішного
# завантаження файлу в сховище, буде створюватися запис `FileModel` за допомогою `FileCreateSchema`.
# API для отримання інформації про файл буде повертати `FileSchema` (включаючи `file_url`).
# API для видалення файлу має видаляти і файл зі сховища, і запис `FileModel`.
# (Або позначати `is_deleted=True` та планувати фізичне видалення).
# Поки що припускаємо "м'яке" видалення через `is_deleted` з `BaseModel` (якщо воно там є)
# або спеціальний статус. `FileModel` успадковує від `BaseModel`, яка не має `is_deleted`.
# Якщо потрібне "м'яке" видалення для файлів, `FileModel` має успадковувати від `BaseMainModel`
# або мати власні поля `deleted_at`, `is_deleted`.
# Поки що залишаю як є (успадкування від `BaseModel`).
# Видалення файлів - це фізичне видалення запису `FileModel` та файлу зі сховища.
# Або ж, якщо потрібне "м'яке" видалення, треба змінити базовий клас або додати поля.
#
# Поточна `BaseModel` має лише `id, created_at, updated_at`.
# `FileModel` не має `is_deleted`. Якщо потрібно, це треба додати.
# Для узгодження з іншими "основними" сутностями, можливо, `FileModel` теж варто було б
# успадкувати від `BaseMainModel`, якщо файли можуть мати "назву" (окрім original_filename),
# "опис", "статус", "приналежність до групи" (вже є group_context_id), "м'яке видалення".
# Поки що залишаю `FileModel` на `BaseModel` для простоти, припускаючи, що
# `original_filename` - це назва, а `file_category_code` та `metadata` дають достатньо опису.
# "М'яке" видалення для файлів може бути реалізоване через зміну `is_public=False`
# та/або переміщення в "кошик" у сховищі, а не через поле в БД.
# Або через статус.
# Залишаю як є.

FileSchema.model_rebuild()
FileCreateSchema.model_rebuild()
FileUpdateSchema.model_rebuild()
