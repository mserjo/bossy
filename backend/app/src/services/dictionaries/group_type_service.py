# backend/app/src/services/dictionaries/group_type_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс для управління довідником типів груп (`GroupTypeModel`).
"""

from backend.app.src.models.dictionaries.group_type import GroupTypeModel
from backend.app.src.repositories.dictionaries.group_type import GroupTypeRepository, group_type_repository
from backend.app.src.schemas.dictionaries.group_type import GroupTypeCreateSchema, GroupTypeUpdateSchema
from backend.app.src.services.dictionaries.base_dict_service import BaseDictionaryService

class GroupTypeService(BaseDictionaryService[GroupTypeModel, GroupTypeRepository, GroupTypeCreateSchema, GroupTypeUpdateSchema]):
    """
    Сервіс для управління довідником типів груп.
    Успадковує базову CRUD-логіку для довідників.
    """
    # TODO: Додати специфічну бізнес-логіку для типів груп, якщо потрібно.
    # Наприклад, перевірка, чи можна змінити тип групи, якщо існують групи цього типу.
    pass

group_type_service = GroupTypeService(group_type_repository)

# Все виглядає добре для базового сервісу типів груп.
