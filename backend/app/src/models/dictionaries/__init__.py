# backend/app/src/models/dictionaries/__init__.py
"""
Пакет моделей-довідників SQLAlchemy.

Цей пакет містить моделі для різних довідників, що використовуються в програмі Kudos.
Кожен модуль у цьому пакеті зазвичай визначає одну модель-довідник,
яка успадковує `BaseDictionaryModel`.

Моделі експортуються для зручного доступу з інших частин програми,
наприклад, при визначенні зв'язків або при роботі з Alembic міграціями.
"""

from .base_dict import BaseDictionaryModel
from .statuses import Status
from .user_roles import UserRole
from .user_types import UserType
from .group_types import GroupType
from .task_types import TaskType
from .bonus_types import BonusType
from .calendars import CalendarProvider
from .messengers import MessengerPlatform

__all__ = [
    "BaseDictionaryModel",
    "Status",
    "UserRole",
    "UserType",
    "GroupType",
    "TaskType",
    "BonusType",
    "CalendarProvider",
    "MessengerPlatform",
]

# Також можна додати логіку для автоматичного збору всіх моделей,
# що успадковують BaseDictionaryModel, якщо кількість довідників значно зросте.
# Наприклад, за допомогою обходу модулів або реєстрації класів.
# Але для поточної кількості явний імпорт та __all__ є достатньо керованими.
