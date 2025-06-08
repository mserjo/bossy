# backend/app/src/repositories/dictionaries/task_type_repository.py

"""
Repository for TaskType dictionary entries.
"""

import logging

from backend.app.src.models.dictionaries.task_types import TaskType
from backend.app.src.schemas.dictionaries.task_types import TaskTypeCreate, TaskTypeUpdate
from backend.app.src.repositories.dictionaries.base_dict_repository import BaseDictionaryRepository

logger = logging.getLogger(__name__)

class TaskTypeRepository(BaseDictionaryRepository[TaskType, TaskTypeCreate, TaskTypeUpdate]):
    """
    Repository for managing TaskType dictionary records.
    Inherits common dictionary operations from BaseDictionaryRepository.
    """
    def __init__(self):
        super().__init__(TaskType)

    # Add any TaskType-specific methods here if needed.
