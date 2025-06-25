# backend/app/src/schemas/dictionaries/user_role.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `UserRoleModel`.
Схеми використовуються для валідації даних при створенні, оновленні
та відображенні ролей користувачів.
"""

from pydantic import Field
from typing import Optional, List
import uuid

from backend.app.src.schemas.dictionaries.base_dict import BaseDictSchema, BaseDictCreateSchema, BaseDictUpdateSchema

# --- Схема для відображення ролі користувача (для читання) ---
class UserRoleSchema(BaseDictSchema):
    """
    Схема для представлення ролі користувача. Успадковує всі поля від BaseDictSchema.
    """
    # UserRoleModel наразі не має додаткових специфічних полів,
    # окрім успадкованих від BaseDictModel (який включає `code`).
    # Якщо б були, наприклад, поле `permissions: List[str]`, воно б додавалося тут.
    # permissions: Optional[List[str]] = Field(None, description="Список дозволів, пов'язаних з цією роллю")
    pass

# --- Схема для створення нової ролі користувача ---
class UserRoleCreateSchema(BaseDictCreateSchema):
    """
    Схема для створення нової ролі користувача. Успадковує поля від BaseDictCreateSchema.
    """
    # `name` та `code` є обов'язковими (визначено в BaseDictCreateSchema).
    # `description`, `state_id`, `notes` - опціональні.
    #
    # Якщо б були специфічні поля для створення UserRole, наприклад, `permissions`:
    # permissions: Optional[List[str]] = Field(None, description="Список дозволів для нової ролі")

    # Приклад: Перевизначення поля `code` з особливим патерном для ролей, якщо потрібно.
    # code: str = Field(..., pattern=r"^[a-z_]+(_[a-z_]+)*$", description="Код ролі (лише маленькі літери та підкреслення)")
    # Але базовий валідатор `code_alphanumeric_underscore` вже є і перетворює на нижній регістр.
    pass

# --- Схема для оновлення існуючої ролі користувача ---
class UserRoleUpdateSchema(BaseDictUpdateSchema):
    """
    Схема для оновлення існуючої ролі користувача. Успадковує поля від BaseDictUpdateSchema.
    """
    # Всі поля опціональні.
    # Можна додати специфічні поля для оновлення, якщо є.
    # permissions: Optional[List[str]] = Field(None, description="Новий список дозволів для ролі")
    pass

# TODO: Переконатися, що схеми відповідають моделі `UserRoleModel`.
# `UserRoleModel` успадковує від `BaseDictModel`.
# `UserRoleSchema` успадковує від `BaseDictSchema`.
# Поля `id, name, description, code, state_id, group_id, created_at, updated_at, deleted_at, is_deleted, notes`
# коректно представлені в `UserRoleSchema` через успадкування.
# `group_id` для ролей користувачів, ймовірно, завжди буде `None`, оскільки ролі
# (superadmin, group_admin, group_user) є глобальними або визначаються в контексті групи,
# але сам тип ролі – глобальний довідник.
#
# Поле `permissions` (список дозволів) є потенційним розширенням,
# але наразі не реалізоване в `UserRoleModel`. Якщо воно буде додано до моделі,
# відповідні зміни потрібно буде внести і в схеми.
# Поки що схеми відповідають поточній структурі `UserRoleModel`.
# Валідація `code` успадкована з `BaseDictCreateSchema` / `BaseDictUpdateSchema`.
# Все виглядає узгоджено.
