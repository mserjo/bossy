# backend/app/src/schemas/__init__.py
# -*- coding: utf-8 -*-
"""Pydantic схеми для додатку.

Цей пакет є кореневим для всіх схем Pydantic, що використовуються в додатку.
Він ре-експортує ключові базові схеми з модуля `base.py` та надає доступ
до підпакетів, які містять схеми для конкретних предметних областей (модулів)
програми.

Підпакети зазвичай містять:
- Базові схеми для сутності (`EntityNameBaseSchema`).
- Схеми для створення записів (`EntityNameCreateSchema`).
- Схеми для оновлення записів (`EntityNameUpdateSchema`).
- Схеми для представлення даних у відповідях API (`EntityNameResponseSchema`).
- Деталізовані схеми для відповідей API, що включають пов'язані об'єкти (`EntityNameDetailResponseSchema`).

Використання Pydantic забезпечує валідацію даних на вході та виході API,
серіалізацію даних, а також автоматичну генерацію документації OpenAPI.
"""

# Експорт основних базових схем для прямого доступу.
# Назви відповідають тим, що будуть визначені в `base.py` згідно з завданням.
from backend.app.src.schemas.base import (
    BaseSchema,
    MsgResponse,
    IDSchemaMixin,
    TimestampedSchemaMixin,
    SoftDeleteSchemaMixin,
    # BaseMainResponseSchema,
    # BaseMainCreateSchema,
    # BaseMainUpdateSchema,
    PaginatedResponse,
    BaseMainSchema
    # GenericTypeVar # T буде визначено в PaginatedResponseSchema, немає потреби експортувати окремо
)

# Експорт підпакетів, що містять специфічні схеми для кожної предметної області.
# Це дозволяє імпортувати схеми як `from backend.app.src.schemas.auth import UserCreateSchema`.
from backend.app.src.schemas import auth
from backend.app.src.schemas import bonuses
from backend.app.src.schemas import dictionaries
from backend.app.src.schemas import files
from backend.app.src.schemas import gamification
from backend.app.src.schemas import groups
from backend.app.src.schemas import notifications
from backend.app.src.schemas import system
from backend.app.src.schemas import tasks
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Визначаємо, які символи будуть експортовані при використанні `from backend.app.src.schemas import *`.
# Включаємо базові схеми та підпакети.
__all__ = [
    # Базові схеми
    "BaseSchema",
    "MsgResponse",
    "IDSchemaMixin",
    "TimestampedSchemaMixin",
    "SoftDeleteSchemaMixin",
    "BaseMainSchema",
    # "BaseMainResponseSchema",
    # "BaseMainCreateSchema",
    # "BaseMainUpdateSchema",
    "PaginatedResponse",
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

logger.debug("Ініціалізація пакету схем Pydantic `schemas`...")
