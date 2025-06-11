# backend/app/src/schemas/__init__.py
"""
Pydantic схеми для програми Kudos.

Цей пакет є кореневим для всіх схем Pydantic, що використовуються в додатку.
Він експортує основні базові схеми та підпакети, які містять схеми
для конкретних предметних областей (модулів) програми.

Структура схем зазвичай включає:
- Базові схеми (`...BaseSchema`) для спільних полів.
- Схеми для створення записів (`...CreateSchema`).
- Схеми для оновлення записів (`...UpdateSchema`).
- Схеми для представлення даних у відповідях API (`...Schema`).
- Деталізовані схеми для відповідей API, що включають пов'язані об'єкти (`...DetailSchema`).

Використання Pydantic забезпечує валідацію даних, серіалізацію та автоматичну
генерацію документації OpenAPI для API.
"""

# Експорт основних базових схем для прямого доступу
from .base import (
    BaseSchema,
    IDSchemaMixin,
    TimestampedSchemaMixin,
    SoftDeleteSchemaMixin,
    BaseMainSchema,
    MsgResponse,
    DataResponse,
    PaginatedResponse,
    T as GenericTypeVar  # Експорт TypeVar T, перейменованого для уникнення конфліктів
)

# Експорт підпакетів, що містять специфічні схеми
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
    # Базові схеми та міксини
    "BaseSchema",
    "IDSchemaMixin",
    "TimestampedSchemaMixin",
    "SoftDeleteSchemaMixin",
    "BaseMainSchema",
    # Узагальнені відповіді
    "MsgResponse",
    "DataResponse",
    "PaginatedResponse",
    "GenericTypeVar", # Раніше T
    # Підпакети зі схемами
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
