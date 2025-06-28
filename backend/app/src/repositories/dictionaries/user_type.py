# backend/app/src/repositories/dictionaries/user_type.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `UserTypeModel`.
Надає методи для взаємодії з таблицею типів користувачів в базі даних.
"""

from backend.app.src.models.dictionaries.user_type import UserTypeModel
from backend.app.src.schemas.dictionaries.user_type import UserTypeCreateSchema, UserTypeUpdateSchema # Припускаємо, що такі схеми існують
from backend.app.src.repositories.dictionaries.base_dict import BaseDictionaryRepository

class UserTypeRepository(BaseDictionaryRepository[UserTypeModel, UserTypeCreateSchema, UserTypeUpdateSchema]):
    """
    Репозиторій для роботи з моделлю типів користувачів.
    Успадковує всі базові CRUD-операції та специфічні для довідників методи
    від `BaseDictionaryRepository`.
    """
    pass

user_type_repository = UserTypeRepository(UserTypeModel)

# TODO: Створити схеми UserTypeCreateSchema та UserTypeUpdateSchema в пакеті schemas.dictionaries.
# TODO: Додати специфічні методи, якщо потрібно (наприклад, отримання типу за замовчуванням).
#
# Базова структура готова.
