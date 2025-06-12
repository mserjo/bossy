# backend/app/src/models/__init__.py
# -*- coding: utf-8 -*-
"""Пакет моделей SQLAlchemy для додатку.

Цей пакет є центральним сховищем для всіх моделей даних, що використовуються
в додатку та відображаються на таблиці бази даних за допомогою SQLAlchemy.
Він організований наступним чином:

- **`base.py`**: Містить базовий декларативний клас `Base` (від `declarative_base()`)
  та загальні базові моделі (`BaseModel`, `BaseMainModel`), від яких успадковуються
  всі інші моделі даних. Це забезпечує наявність спільних полів, таких як `id`,
  `created_at`, `updated_at`.
- **`mixins.py`**: Визначає класи-домішки (mixins) для додавання спільної
  функціональності або набору полів до різних моделей (наприклад, `TimestampMixin`,
  `SoftDeleteMixin`).
- **Підпакети для предметних областей**: Для кращої організації, моделі,
  що належать до конкретних функціональних блоків, розміщуються у відповідних
  підпакетах. Наприклад:
    - `auth/`: Моделі, пов'язані з автентифікацією та користувачами (User, Role, Permission).
    - `bonuses/`: Моделі для бонусної системи (BonusRule, UserBonus, BonusTransaction).
    - `dictionaries/`: Моделі-довідники (Status, Priority, Category).
    - `files/`: Моделі для управління файлами (FileRecord, Avatar).
    - `gamification/`: Моделі для елементів гейміфікації (Level, Badge, Achievement).
    - `groups/`: Моделі для груп, членства та пов'язаних сутностей.
    - `notifications/`: Моделі для системи сповіщень.
    - `system/`: Моделі для системних налаштувань та моніторингу.
    - `tasks/`: Моделі для завдань, їх призначень та виконань.

Цей файл `__init__.py` також ре-експортує ключові базові класи та робить
доступними підпакети моделей для зручного імпорту в інших частинах програми.
Наприклад, `from backend.app.src.models import Base, User` (якщо User ре-експортовано тут або в __init__ підпакету auth).
"""

# Імпорт централізованого логера
from backend.app.src.config import logger

# Імпорт та експорт базових класів моделей для легкого доступу з будь-якої точки програми.
# Використовуємо абсолютні імпорти для ясності та надійності.
from backend.app.src.models.base import Base, BaseModel, BaseMainModel
from backend.app.src.models import mixins # Імпортуємо модуль mixins

# Імпорт підпакетів моделей. Це робить їх доступними як атрибути пакету `models`.
# Наприклад, після `from backend.app.src import models` можна буде звернутися до `models.auth.User`.
from backend.app.src.models import auth
from backend.app.src.models import bonuses
from backend.app.src.models import dictionaries
from backend.app.src.models import files
from backend.app.src.models import gamification
from backend.app.src.models import groups
from backend.app.src.models import notifications
from backend.app.src.models import system
from backend.app.src.models import tasks

# Визначаємо, які символи будуть експортовані при використанні `from backend.app.src.models import *`.
# Рекомендується використовувати явні імпорти, але `__all__` контролює "зірочковий" імпорт.
__all__ = [
    # Базові класи
    "Base",
    "BaseModel",
    "BaseMainModel",
    # Модуль міксинів
    "mixins",
    # Підпакети моделей
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

logger.debug("Ініціалізація пакету `models`...")

# Примітка: Конкретні моделі сутностей (наприклад, User, Group, Task)
# зазвичай імпортуються та ре-експортуються з відповідних `__init__.py` файлів
# у їхніх підпакетах (наприклад, `backend/app/src/models/auth/__init__.py`
# може містити `from .user_model import User` та `__all__ = ["User"]`).
# Це дозволяє імпортувати моделі як `from backend.app.src.models.auth import User`.
