# backend/app/src/repositories/dictionaries/__init__.py
"""
Репозиторії для моделей-довідників програми Kudos.

Цей пакет містить класи репозиторіїв для кожної моделі-довідника.
Кожен репозиторій успадковує `BaseDictionaryRepository` та надає
спеціалізований інтерфейс для роботи з конкретним типом довідника.

Експортує базовий репозиторій для довідників та всі специфічні репозиторії.
"""

from .base_dict_repository import BaseDictionaryRepository
from .status_repository import StatusRepository
from .user_role_repository import UserRoleRepository
from .user_type_repository import UserTypeRepository
from .group_type_repository import GroupTypeRepository
from .task_type_repository import TaskTypeRepository
from .bonus_type_repository import BonusTypeRepository
from .calendar_provider_repository import CalendarProviderRepository
from .messenger_platform_repository import MessengerPlatformRepository

__all__ = [
    "BaseDictionaryRepository",
    "StatusRepository",
    "UserRoleRepository",
    "UserTypeRepository",
    "GroupTypeRepository",
    "TaskTypeRepository",
    "BonusTypeRepository",
    "CalendarProviderRepository",
    "MessengerPlatformRepository",
]
