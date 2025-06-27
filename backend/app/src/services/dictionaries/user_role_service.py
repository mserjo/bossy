# backend/app/src/services/dictionaries/user_role_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс для управління довідником ролей користувачів (`UserRoleModel`).
"""

from backend.app.src.models.dictionaries.user_role import UserRoleModel
from backend.app.src.repositories.dictionaries.user_role import UserRoleRepository, user_role_repository
from backend.app.src.schemas.dictionaries.user_role import UserRoleCreateSchema, UserRoleUpdateSchema
from backend.app.src.services.dictionaries.base_dict_service import BaseDictionaryService

class UserRoleService(BaseDictionaryService[UserRoleModel, UserRoleRepository, UserRoleCreateSchema, UserRoleUpdateSchema]):
    """
    Сервіс для управління довідником ролей користувачів.
    Успадковує базову CRUD-логіку для довідників.
    """
    # TODO: Додати специфічну бізнес-логіку для ролей, якщо потрібно.
    # Наприклад, перевірка, чи можна видалити роль, якщо вона призначена користувачам.
    # Або отримання ролі за замовчуванням для нових користувачів групи.
    pass

user_role_service = UserRoleService(user_role_repository)

# Все виглядає добре для базового сервісу ролей.
