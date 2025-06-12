# backend/app/src/services/dictionaries/__init__.py
"""
Ініціалізаційний файл для модуля сервісів, що працюють з довідниками.

Цей модуль реекспортує базовий клас сервісу для довідників (`BaseDictionaryService`)
та конкретні реалізації сервісів для кожного типу довідника.
"""

from backend.app.src.config import logger

# Явний імпорт сервісів для кращої читабельності та статичного аналізу
from backend.app.src.services.dictionaries.base_dict import BaseDictionaryService
from backend.app.src.services.dictionaries.statuses import StatusService
from backend.app.src.services.dictionaries.user_roles import UserRoleService
from backend.app.src.services.dictionaries.user_types import UserTypeService
from backend.app.src.services.dictionaries.group_types import GroupTypeService
from backend.app.src.services.dictionaries.task_types import TaskTypeService
from backend.app.src.services.dictionaries.bonus_types import BonusTypeService
from backend.app.src.services.dictionaries.calendars import CalendarProviderService
from backend.app.src.services.dictionaries.messengers import MessengerPlatformService

__all__ = [
    "BaseDictionaryService",
    "StatusService",
    "UserRoleService",
    "UserTypeService",
    "GroupTypeService",
    "TaskTypeService",
    "BonusTypeService",
    "CalendarProviderService",
    "MessengerPlatformService",
]

logger.info(f"Сервіси довідників експортують: {__all__}")
