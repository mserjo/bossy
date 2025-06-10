# backend/app/src/repositories/__init__.py
"""
Пакет репозиторіїв для програми Kudos.

Цей пакет є кореневим для всіх репозиторіїв, що відповідають за доступ до даних
та взаємодію з базою даних для різних моделей (сутностей) програми.
Він експортує базовий репозиторій та підпакети, які містять репозиторії
для конкретних предметних областей.

Кожен репозиторій інкапсулює логіку запитів до бази даних для відповідної моделі,
абстрагуючи деталі взаємодії з SQLAlchemy від сервісного шару.
"""

# Експорт базового репозиторію для можливого успадкування поза цим пакетом (малоймовірно, але можливо)
from .base import BaseRepository

# Експорт підпакетів, що містять специфічні репозиторії
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
    "BaseRepository",
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

# Приклад того, як можна було б експортувати конкретні репозиторії напряму,
# якби не використовувалася структура підпакетів для репозиторіїв:
# from .auth.user_repository import UserRepository
# from .dictionaries.status_repository import StatusRepository
# __all__.extend(["UserRepository", "StatusRepository"])
# Але поточна структура з експортом підпакетів є більш організованою.
