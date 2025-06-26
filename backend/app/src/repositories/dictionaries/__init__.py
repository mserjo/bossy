# backend/app/src/repositories/dictionaries/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет репозиторіїв для довідників.

Цей пакет містить класи репозиторіїв для роботи з моделями-довідниками,
такими як статуси, ролі, типи груп тощо.
"""

from .base_dict import BaseDictionaryRepository
from .status import StatusRepository
from .user_role import UserRoleRepository
from .group_type import GroupTypeRepository
from .task_type import TaskTypeRepository
from .bonus_type import BonusTypeRepository
from .integration import IntegrationRepository

__all__ = [
    "BaseDictionaryRepository",
    "StatusRepository",
    "UserRoleRepository",
    "GroupTypeRepository",
    "TaskTypeRepository",
    "BonusTypeRepository",
    "IntegrationRepository",
]

from backend.app.src.config.logging import logger
logger.debug("Пакет 'repositories.dictionaries' ініціалізовано.")
