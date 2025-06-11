# backend/app/src/schemas/dictionaries/__init__.py
"""
Pydantic схеми для довідників програми Kudos.

Цей пакет містить схеми Pydantic, що відповідають моделям-довідникам
і використовуються для валідації даних запитів та формування відповідей API,
пов'язаних з довідниками.

Кожен модуль у цьому пакеті зазвичай визначає набір схем (для читання,
створення, оновлення) для конкретного довідника.
"""

from .base_dict import BaseDictionarySchema, DictionaryCreateSchema, DictionaryUpdateSchema
from .statuses import StatusSchema, StatusCreateSchema, StatusUpdateSchema
from .user_roles import UserRoleSchema, UserRoleCreateSchema, UserRoleUpdateSchema
from .user_types import UserTypeSchema, UserTypeCreateSchema, UserTypeUpdateSchema
from .group_types import GroupTypeSchema, GroupTypeCreateSchema, GroupTypeUpdateSchema
from .task_types import TaskTypeSchema, TaskTypeCreateSchema, TaskTypeUpdateSchema
from .bonus_types import BonusTypeSchema, BonusTypeCreateSchema, BonusTypeUpdateSchema
from .calendars import CalendarProviderSchema, CalendarProviderCreateSchema, CalendarProviderUpdateSchema
from .messengers import MessengerPlatformSchema, MessengerPlatformCreateSchema, MessengerPlatformUpdateSchema

__all__ = [
    # Базові схеми довідників
    "BaseDictionarySchema",
    "DictionaryCreateSchema",
    "DictionaryUpdateSchema",
    # Схеми для Статусів
    "StatusSchema",
    "StatusCreateSchema",
    "StatusUpdateSchema",
    # Схеми для Ролей Користувачів
    "UserRoleSchema",
    "UserRoleCreateSchema",
    "UserRoleUpdateSchema",
    # Схеми для Типів Користувачів
    "UserTypeSchema",
    "UserTypeCreateSchema",
    "UserTypeUpdateSchema",
    # Схеми для Типів Груп
    "GroupTypeSchema",
    "GroupTypeCreateSchema",
    "GroupTypeUpdateSchema",
    # Схеми для Типів Завдань
    "TaskTypeSchema",
    "TaskTypeCreateSchema",
    "TaskTypeUpdateSchema",
    # Схеми для Типів Бонусів
    "BonusTypeSchema",
    "BonusTypeCreateSchema",
    "BonusTypeUpdateSchema",
    # Схеми для Постачальників Календарів
    "CalendarProviderSchema",
    "CalendarProviderCreateSchema",
    "CalendarProviderUpdateSchema",
    # Схеми для Платформ Месенджерів
    "MessengerPlatformSchema",
    "MessengerPlatformCreateSchema",
    "MessengerPlatformUpdateSchema",
]
