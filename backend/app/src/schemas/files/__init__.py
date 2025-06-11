# backend/app/src/schemas/files/__init__.py
"""
Pydantic схеми для сутностей, пов'язаних з "Файлами".

Цей пакет містить схеми Pydantic, що використовуються для валідації
даних запитів та формування відповідей API, які стосуються файлів,
їх метаданих, аватарів користувачів та процесу завантаження файлів
в програмі Kudos.
"""

# Схеми, пов'язані з Записами Файлів
from .file import (
    FileRecordBaseSchema,
    FileRecordCreateSchema,
    FileRecordSchema
)

# Схеми, пов'язані з Аватарами Користувачів
from .avatar import (
    UserAvatarBaseSchema,
    UserAvatarCreateSchema,
    UserAvatarSchema
)

# Схеми, пов'язані з Процесом Завантаження Файлів
from .upload import (
    FileUploadInitiateRequestSchema,
    PresignedUploadURLResponse,
    FileUploadCompleteRequestSchema,
    FileUploadResponse
)

__all__ = [
    # FileRecord schemas
    "FileRecordBaseSchema",
    "FileRecordCreateSchema",
    "FileRecordSchema",
    # UserAvatar schemas
    "UserAvatarBaseSchema",
    "UserAvatarCreateSchema",
    "UserAvatarSchema",
    # FileUpload process schemas
    "FileUploadInitiateRequestSchema",
    "PresignedUploadURLResponse",
    "FileUploadCompleteRequestSchema",
    "FileUploadResponse",
]
