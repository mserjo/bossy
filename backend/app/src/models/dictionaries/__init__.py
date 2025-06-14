# backend/app/src/models/dictionaries/__init__.py
# -*- coding: utf-8 -*-
"""Пакет моделей-довідників SQLAlchemy.

Цей пакет містить моделі для різних довідників (словників даних),
що використовуються в програмі. Кожен модуль у цьому пакеті зазвичай
визначає одну модель-довідник, яка успадковує базовий клас
`BaseDictionaryModel` з модуля `base_dict.py`.

Моделі-довідники представляють стандартизовані набори значень для певних
атрибутів інших сутностей (наприклад, статуси завдань, типи користувачів,
ролі користувачів тощо).

Всі моделі з цього пакету ре-експортуються для зручного доступу з інших
частин програми, наприклад, при визначенні зв'язків у моделях SQLAlchemy
або при роботі з міграціями Alembic.
"""

# Імпорт централізованого логера
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Імпорт базової моделі для довідників та всіх конкретних моделей-довідників.
from backend.app.src.models.dictionaries.base_dict import BaseDictionary
from backend.app.src.models.dictionaries.statuses import Status
from backend.app.src.models.dictionaries.user_roles import UserRole
from backend.app.src.models.dictionaries.user_types import UserType
from backend.app.src.models.dictionaries.group_types import GroupType
from backend.app.src.models.dictionaries.task_types import TaskType
from backend.app.src.models.dictionaries.bonus_types import BonusType
from backend.app.src.models.dictionaries.calendars import CalendarProvider
from backend.app.src.models.dictionaries.messengers import MessengerPlatform

# Визначаємо, які символи будуть експортовані при використанні `from backend.app.src.models.dictionaries import *`.
# Це допомагає контролювати публічний API пакету.
__all__ = [
    "BaseDictionary",
    "Status",
    "UserRole",
    "UserType",
    "GroupType",
    "TaskType",
    "BonusType",
    "CalendarProvider",
    "MessengerPlatform",
]

logger.debug("Ініціалізація пакету моделей `dictionaries`...")

# Коментар щодо можливого розширення:
# Також можна додати логіку для автоматичного збору всіх моделей,
# що успадковують BaseDictionaryModel, якщо кількість довідників значно зросте.
# Наприклад, за допомогою обходу модулів або реєстрації класів.
# Однак, для поточної кількості довідників явний імпорт та визначення `__all__`
# є достатньо керованим та прозорим підходом.
