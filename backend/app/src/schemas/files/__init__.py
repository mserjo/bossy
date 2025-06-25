# backend/app/src/schemas/files/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету схем, пов'язаних з файлами (`files`).

Цей файл робить доступними основні схеми файлів для імпорту з пакету
`backend.app.src.schemas.files`.

Приклад імпорту:
from backend.app.src.schemas.files import FileSchema, AvatarSchema

Також цей файл може використовуватися для визначення змінної `__all__`,
яка контролює, що саме експортується при використанні `from . import *`.
"""

# Імпорт конкретних схем, пов'язаних з файлами
from backend.app.src.schemas.files.file import (
    FileSchema,
    FileCreateSchema,
    FileUpdateSchema,
)
from backend.app.src.schemas.files.avatar import (
    AvatarSchema,
    AvatarCreateSchema,
    AvatarUpdateSchema,
)

# Визначення змінної `__all__` для контролю публічного API пакету.
__all__ = [
    # File Schemas
    "FileSchema",
    "FileCreateSchema",
    "FileUpdateSchema",

    # Avatar Schemas
    "AvatarSchema",
    "AvatarCreateSchema",
    "AvatarUpdateSchema",
]

# Виклик model_rebuild для схем, що використовують ForwardRef.
# from typing import ForwardRef, List, Optional, Union, Any, Dict # Потрібні імпорти для контексту
# import uuid
# from datetime import datetime, timedelta
# from pydantic import BaseModel as PydanticBaseModel, HttpUrl

# schemas_to_rebuild = [
#     FileSchema,
#     AvatarSchema,
# ]

# for schema in schemas_to_rebuild:
#     try:
#         # schema.model_rebuild(force=True) # Pydantic v2
#         pass # Pydantic v2 зазвичай справляється
#     except Exception as e:
#         print(f"Warning: Could not rebuild schema {schema.__name__}: {e}")

# Поки що залишаю без явних викликів `model_rebuild`.
# Головне, що всі схеми експортуються через `__all__`.

# Виклик model_rebuild для схем, що містять ForwardRef
FileSchema.model_rebuild()
AvatarSchema.model_rebuild()

# Все виглядає добре.
