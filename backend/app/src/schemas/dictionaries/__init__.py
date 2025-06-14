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
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Імпорт базових схем для довідників
from backend.app.src.schemas.dictionaries.base_dict import (
    DictionaryBaseResponseSchema as DictionaryResponseSchema, # Renamed and aliased
    DictionaryCreateSchema,
    DictionaryUpdateSchema
    # DictionaryBaseSchema is now DictionaryBaseResponseSchema
)

# Імпорт схем для конкретних довідників
from backend.app.src.schemas.dictionaries.statuses import (
    StatusCreateSchema, StatusUpdateSchema, StatusResponseSchema
)
from backend.app.src.schemas.dictionaries.user_roles import (
    UserRoleCreateSchema, UserRoleUpdateSchema, UserRoleResponseSchema # UserRoleSchema renamed to UserRoleResponseSchema
)
from backend.app.src.schemas.dictionaries.user_types import (
    UserTypeCreateSchema, UserTypeUpdateSchema, UserTypeResponseSchema
)
from backend.app.src.schemas.dictionaries.group_types import (
    GroupTypeCreateSchema, GroupTypeUpdateSchema, GroupTypeResponseSchema # GroupTypeSchema renamed to GroupTypeResponseSchema
)
from backend.app.src.schemas.dictionaries.task_types import (
    TaskTypeCreateSchema, TaskTypeUpdateSchema, TaskTypeResponseSchema
)
from backend.app.src.schemas.dictionaries.bonus_types import (
    BonusTypeCreateSchema, BonusTypeUpdateSchema, BonusTypeResponseSchema # BonusTypeSchema renamed to BonusTypeResponseSchema
)
from backend.app.src.schemas.dictionaries.calendars import (
    CalendarProviderCreateSchema, CalendarProviderUpdateSchema, CalendarProviderResponseSchema
)
from backend.app.src.schemas.dictionaries.messengers import (
    MessengerPlatformCreateSchema, MessengerPlatformUpdateSchema, MessengerPlatformResponseSchema # MessengerPlatformSchema renamed to MessengerPlatformResponseSchema
)


__all__ = [
    # Базові схеми довідників
    "DictionaryCreateSchema",
    "DictionaryUpdateSchema",
    "DictionaryResponseSchema", # This is the alias for DictionaryBaseResponseSchema
    # Схеми для Статусів
    "StatusCreateSchema",
    "StatusUpdateSchema",
    "StatusResponseSchema",
    # Схеми для Ролей Користувачів
    "UserRoleCreateSchema",
    "UserRoleUpdateSchema",
    "UserRoleResponseSchema", # UserRoleSchema renamed
    # Схеми для Типів Користувачів
    "UserTypeCreateSchema",
    "UserTypeUpdateSchema",
    "UserTypeResponseSchema",
    # Схеми для Типів Груп
    "GroupTypeCreateSchema",
    "GroupTypeUpdateSchema",
    "GroupTypeResponseSchema", # GroupTypeSchema renamed
    # Схеми для Типів Завдань
    "TaskTypeCreateSchema",
    "TaskTypeUpdateSchema",
    "TaskTypeResponseSchema",
    # Схеми для Типів Бонусів
    "BonusTypeCreateSchema",
    "BonusTypeUpdateSchema",
    "BonusTypeResponseSchema", # BonusTypeSchema renamed
    # Схеми для Провайдерів Календарів
    "CalendarProviderCreateSchema",
    "CalendarProviderUpdateSchema",
    "CalendarProviderResponseSchema",
    # Схеми для Платформ Месенджерів
    "MessengerPlatformCreateSchema",
    "MessengerPlatformUpdateSchema",
    "MessengerPlatformResponseSchema", # MessengerPlatformSchema renamed
]

logger.debug("Ініціалізація пакету схем Pydantic `dictionaries`...")
