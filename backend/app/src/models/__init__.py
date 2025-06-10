# backend/app/src/models/__init__.py
"""
Пакет моделей SQLAlchemy для програми Kudos.

Цей пакет містить:
- Базові класи для всіх моделей SQLAlchemy (`Base`, `BaseMainModel`) у модулі `base.py`.
- Міксини для додавання спільної функціональності до моделей (`mixins.py`).
- Підпакети для моделей конкретних предметних областей:
    - `auth`: Моделі, пов'язані з автентифікацією та користувачами.
    - `bonuses`: Моделі для бонусної системи (правила, рахунки, транзакції, нагороди).
    - `dictionaries`: Моделі-довідники.
    - `files`: Моделі для роботи з файлами (записи файлів, аватари).
    - `gamification`: Моделі для елементів гейміфікації (рівні, бейджі, досягнення, рейтинги).
    - `groups`: Моделі для груп, членства, налаштувань груп та запрошень.
    - `notifications`: Моделі для сповіщень та їх шаблонів.
    - `system`: Моделі для системних налаштувань, моніторингу та стану здоров'я.
    - `tasks`: Моделі для завдань, призначень, виконань та відгуків.

Експортує основні базові класи та всі підпакети моделей для зручного доступу.
"""

# Імпорт та експорт базових класів моделей для легкого доступу
from .base import Base, BaseMainModel
from . import mixins # Хоча міксини зазвичай не імпортуються напряму, а використовуються в успадкуванні

# Імпорт та експорт підпакетів моделей
from . import auth
from . import bonuses
from . import dictionaries
from . import files
from . import gamification
from . import groups
from . import notifications
from . import system
from . import tasks

__all__ = [
    "Base",
    "BaseMainModel",
    "mixins", # Експорт модуля міксинів, якщо потрібно (зазвичай ні)
    "auth",
    "bonuses",
    "dictionaries",
    "files",
    "gamification",
    "groups",
    "notifications",
    "system",
    "tasks",
]

# Примітка: Конкретні моделі сутностей (наприклад, User, Group, Task)
# експортуються з відповідних `__init__.py` файлів у їхніх підпакетах.
# Наприклад, `from backend.app.src.models.auth import User`.
