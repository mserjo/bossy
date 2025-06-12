# backend/app/src/schemas/dictionaries/__init__.py
# -*- coding: utf-8 -*-
"""Pydantic схеми для довідників.

Цей пакет містить схеми Pydantic, що відповідають моделям-довідникам
і використовуються для валідації даних запитів та формування відповідей API,
пов'язаних з різними довідниками системи (наприклад, статуси, типи користувачів, ролі).

Кожен підмодуль зазвичай визначає набір схем для конкретного довідника:
- `XxxBaseSchema` (якщо є спільні поля для створення/оновлення, крім базових з `DictionaryBaseSchema`)
- `XxxCreateSchema` (для створення нового запису довідника)
- `XxxUpdateSchema` (для оновлення існуючого запису довідника)
- `XxxResponseSchema` (для представлення запису довідника у відповідях API)

Також експортуються базові схеми для довідників з `base_dict.py`.
"""

# Імпорт централізованого логера
from backend.app.src.config import logger

# Імпорт базових схем для довідників
from backend.app.src.schemas.dictionaries.base_dict import (
    DictionaryBaseSchema,
    DictionaryCreateSchema,
    DictionaryUpdateSchema,
    DictionaryResponseSchema
)

# Імпорт схем для конкретних довідників
# Припускаємо, що кожен файл визначає XxxCreateSchema, XxxUpdateSchema, XxxResponseSchema
from backend.app.src.schemas.dictionaries.statuses import (
    StatusCreateSchema, StatusUpdateSchema, StatusResponseSchema
)
from backend.app.src.schemas.dictionaries.user_roles import (
    UserRoleCreateSchema, UserRoleUpdateSchema, UserRoleResponseSchema
)
from backend.app.src.schemas.dictionaries.user_types import (
    UserTypeCreateSchema, UserTypeUpdateSchema, UserTypeResponseSchema
)
from backend.app.src.schemas.dictionaries.group_types import (
    GroupTypeCreateSchema, GroupTypeUpdateSchema, GroupTypeResponseSchema
)
from backend.app.src.schemas.dictionaries.task_types import (
    TaskTypeCreateSchema, TaskTypeUpdateSchema, TaskTypeResponseSchema
)
from backend.app.src.schemas.dictionaries.bonus_types import (
    BonusTypeCreateSchema, BonusTypeUpdateSchema, BonusTypeResponseSchema
)
from backend.app.src.schemas.dictionaries.calendars import (
    CalendarProviderCreateSchema, CalendarProviderUpdateSchema, CalendarProviderResponseSchema
)
from backend.app.src.schemas.dictionaries.messengers import (
    MessengerPlatformCreateSchema, MessengerPlatformUpdateSchema, MessengerPlatformResponseSchema
)


__all__ = [
    # Базові схеми довідників
    "DictionaryBaseSchema",
    "DictionaryCreateSchema",
    "DictionaryUpdateSchema",
    "DictionaryResponseSchema",
    # Схеми для Статусів
    "StatusCreateSchema",
    "StatusUpdateSchema",
    "StatusResponseSchema",
    # Схеми для Ролей Користувачів
    "UserRoleCreateSchema",
    "UserRoleUpdateSchema",
    "UserRoleResponseSchema",
    # Схеми для Типів Користувачів
    "UserTypeCreateSchema",
    "UserTypeUpdateSchema",
    "UserTypeResponseSchema",
    # Схеми для Типів Груп
    "GroupTypeCreateSchema",
    "GroupTypeUpdateSchema",
    "GroupTypeResponseSchema",
    # Схеми для Типів Завдань
    "TaskTypeCreateSchema",
    "TaskTypeUpdateSchema",
    "TaskTypeResponseSchema",
    # Схеми для Типів Бонусів
    "BonusTypeCreateSchema",
    "BonusTypeUpdateSchema",
    "BonusTypeResponseSchema",
    # Схеми для Провайдерів Календарів
    "CalendarProviderCreateSchema",
    "CalendarProviderUpdateSchema",
    "CalendarProviderResponseSchema",
    # Схеми для Платформ Месенджерів
    "MessengerPlatformCreateSchema",
    "MessengerPlatformUpdateSchema",
    "MessengerPlatformResponseSchema",
]

logger.debug("Ініціалізація пакету схем Pydantic `dictionaries`...")
