# backend/app/src/repositories/dictionaries/group_type.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `GroupTypeModel`.
Надає методи для взаємодії з таблицею типів груп в базі даних.
"""

from backend.app.src.models.dictionaries.group_type import GroupTypeModel
from backend.app.src.schemas.dictionaries.group_type import GroupTypeCreateSchema, GroupTypeUpdateSchema
from backend.app.src.repositories.dictionaries.base_dict import BaseDictionaryRepository

class GroupTypeRepository(BaseDictionaryRepository[GroupTypeModel, GroupTypeCreateSchema, GroupTypeUpdateSchema]):
    """
    Репозиторій для роботи з моделлю типів груп.
    Успадковує всі базові CRUD-операції та специфічні для довідників методи
    від `BaseDictionaryRepository`.
    """
    pass

group_type_repository = GroupTypeRepository(GroupTypeModel)

# TODO: Додати специфічні методи, якщо потрібно.
#
# Все виглядає добре.
