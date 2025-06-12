# backend/app/src/schemas/files/__init__.py
# -*- coding: utf-8 -*-
"""Pydantic схеми для сутностей, пов'язаних з файлами.

Цей пакет містить схеми Pydantic, що використовуються для валідації
даних запитів та формування відповідей API, які стосуються:
- Записів про файли в системі (`FileRecord...Schema` з `file.py`).
- Аватарів користувачів (`UserAvatar...Schema` з `avatar.py`).
- Процесу завантаження файлів, включаючи генерацію pre-signed URLs
  (`PresignedUrl...Schema`, `FileUploadResponseSchema` з `upload.py`).

Моделі з цього пакету експортуються для використання в сервісному шарі,
API ендпоінтах та інших частинах додатку, що реалізують логіку роботи з файлами.
"""

# Імпорт централізованого логера
from backend.app.src.config import logger

# Схеми, пов'язані з Записами Файлів
from backend.app.src.schemas.files.file import (
    FileRecordBaseSchema,
    FileRecordCreateSchema,
    FileRecordUpdateSchema, # Додаємо схему оновлення
    FileRecordResponseSchema
)

# Схеми, пов'язані з Аватарами Користувачів
from backend.app.src.schemas.files.avatar import (
    UserAvatarBaseSchema,
    UserAvatarCreateSchema,
    # UserAvatarUpdateSchema, # Зазвичай не оновлюється, а створюється новий і деактивується старий
    UserAvatarResponseSchema
)

# Схеми, пов'язані з Процесом Завантаження Файлів (згідно з завданням)
from backend.app.src.schemas.files.upload import (
    PresignedUrlRequestSchema,  # Змінено з FileUploadInitiateRequestSchema
    PresignedUrlResponseSchema, # Змінено з PresignedUploadURLResponse
    # FileUploadCompleteRequestSchema, # Якщо потрібна, буде визначена в upload.py
    FileUploadResponseSchema    # Змінено з FileUploadResponse
)

__all__ = [
    # FileRecord schemas
    "FileRecordBaseSchema",
    "FileRecordCreateSchema",
    "FileRecordUpdateSchema",
    "FileRecordResponseSchema",
    # UserAvatar schemas
    "UserAvatarBaseSchema",
    "UserAvatarCreateSchema",
    # "UserAvatarUpdateSchema",
    "UserAvatarResponseSchema",
    # FileUpload process schemas
    "PresignedUrlRequestSchema",
    "PresignedUrlResponseSchema",
    # "FileUploadCompleteRequestSchema", # Розкоментувати, якщо буде визначено
    "FileUploadResponseSchema",
]

logger.debug("Ініціалізація пакету схем Pydantic `files`...")
