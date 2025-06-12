# backend/app/src/repositories/dictionaries/__init__.py
"""
Репозиторії для моделей-довідників програми Kudos.

Цей пакет містить класи репозиторіїв для кожної моделі-довідника.
Кожен репозиторій успадковує `BaseDictionaryRepository` та надає
спеціалізований інтерфейс для роботи з конкретним типом довідника.

Експортує базовий репозиторій для довідників та всі специфічні репозиторії.
"""

from backend.app.src.repositories.dictionaries.base_dict_repository import BaseDictionaryRepository
from backend.app.src.repositories.dictionaries.status_repository import StatusRepository
from backend.app.src.repositories.dictionaries.user_role_repository import UserRoleRepository
from backend.app.src.repositories.dictionaries.user_type_repository import UserTypeRepository
from backend.app.src.repositories.dictionaries.group_type_repository import GroupTypeRepository
from backend.app.src.repositories.dictionaries.task_type_repository import TaskTypeRepository
from backend.app.src.repositories.dictionaries.bonus_type_repository import BonusTypeRepository
from backend.app.src.repositories.dictionaries.calendar_provider_repository import CalendarProviderRepository
from backend.app.src.repositories.dictionaries.messenger_platform_repository import MessengerPlatformRepository

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
