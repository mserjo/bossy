# backend/app/src/services/dictionaries/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет сервісів для роботи з довідниками.

Кожен сервіс тут відповідає за бізнес-логіку, пов'язану з конкретним
типом довідника (статуси, ролі, типи груп тощо).
"""

from .base_dict_service import BaseDictionaryService
from .status_service import StatusService, status_service
from .user_role_service import UserRoleService, user_role_service
from .group_type_service import GroupTypeService, group_type_service
from .task_type_service import TaskTypeService, task_type_service
from .bonus_type_service import BonusTypeService, bonus_type_service
from .integration_type_service import IntegrationTypeService, integration_type_service # Змінено з IntegrationService

__all__ = [
    "BaseDictionaryService",
    "StatusService",
    "status_service",
    "UserRoleService",
    "user_role_service",
    "GroupTypeService",
    "group_type_service",
    "TaskTypeService",
    "task_type_service",
    "BonusTypeService",
    "bonus_type_service",
    "IntegrationTypeService", # Змінено з IntegrationService
    "integration_type_service", # Змінено з integration_service
]

from backend.app.src.config.logging import logger
logger.debug("Пакет 'services.dictionaries' ініціалізовано.")
