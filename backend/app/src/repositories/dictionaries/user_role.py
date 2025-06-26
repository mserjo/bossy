# backend/app/src/repositories/dictionaries/user_role.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `UserRoleModel`.
Надає методи для взаємодії з таблицею ролей користувачів в базі даних.
"""

from backend.app.src.models.dictionaries.user_role import UserRoleModel
from backend.app.src.schemas.dictionaries.user_role import UserRoleCreateSchema, UserRoleUpdateSchema
from backend.app.src.repositories.dictionaries.base_dict import BaseDictionaryRepository

class UserRoleRepository(BaseDictionaryRepository[UserRoleModel, UserRoleCreateSchema, UserRoleUpdateSchema]):
    """
    Репозиторій для роботи з моделлю ролей користувачів.
    Успадковує всі базові CRUD-операції та специфічні для довідників методи
    від `BaseDictionaryRepository`.
    """
    pass

user_role_repository = UserRoleRepository(UserRoleModel)

# TODO: Додати специфічні методи, якщо потрібно.
# Наприклад, отримання ролі за замовчуванням для нового користувача.
#
# Все виглядає добре.
