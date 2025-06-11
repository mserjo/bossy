# backend/app/src/models/dictionaries/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет моделей-довідників SQLAlchemy.

Цей пакет містить моделі для різних довідників, що використовуються в програмі Kudos.
Кожен модуль у цьому пакеті зазвичай визначає одну модель-довідник,
яка успадковує `BaseDictionaryModel`.

Моделі експортуються для зручного доступу з інших частин програми,
наприклад, при визначенні зв'язків або при роботі з Alembic міграціями.
"""

from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel
from backend.app.src.models.dictionaries.statuses import Status
from backend.app.src.models.dictionaries.user_roles import UserRole
from backend.app.src.models.dictionaries.user_types import UserType
from backend.app.src.models.dictionaries.group_types import GroupType
from backend.app.src.models.dictionaries.task_types import TaskType
from backend.app.src.models.dictionaries.bonus_types import BonusType
from backend.app.src.models.dictionaries.calendars import CalendarProvider
from backend.app.src.models.dictionaries.messengers import MessengerPlatform

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
