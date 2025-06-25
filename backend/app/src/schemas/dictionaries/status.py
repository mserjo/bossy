# backend/app/src/schemas/dictionaries/status.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `StatusModel`.
Схеми використовуються для валідації даних при створенні, оновленні
та відображенні статусів.
"""

from pydantic import Field
from typing import Optional, List
import uuid

from backend.app.src.schemas.dictionaries.base_dict import BaseDictSchema, BaseDictCreateSchema, BaseDictUpdateSchema

# --- Схема для відображення статусу (для читання) ---
class StatusSchema(BaseDictSchema):
    """
    Схема для представлення статусу. Успадковує всі поля від BaseDictSchema.
    """
    # Якщо StatusModel має специфічні поля, вони додаються тут.
    # Наприклад, якщо було б поле `color`:
    # color: Optional[str] = Field(None, description="Колір, що асоціюється зі статусом (наприклад, у форматі #RRGGBB)")
    # Наразі StatusModel не має додаткових полів, окрім успадкованих.
    pass

# --- Схема для створення нового статусу ---
class StatusCreateSchema(BaseDictCreateSchema):
    """
    Схема для створення нового статусу. Успадковує поля від BaseDictCreateSchema.
    """
    # Тут можна додати специфічні поля або валідатори для створення статусу,
    # якщо вони відрізняються від базових для довідників.
    # Наприклад, якщо `code` для статусів має особливий формат.
    # Але базовий валідатор `code_alphanumeric_underscore` вже є.

    # Якщо StatusModel мав би поле `color`, воно б додавалося сюди:
    # color: Optional[str] = Field(None, pattern=r"^#(?:[0-9a-fA-F]{3}){1,2}$", description="Колір статусу (#RRGGBB)")
    pass

# --- Схема для оновлення існуючого статусу ---
class StatusUpdateSchema(BaseDictUpdateSchema):
    """
    Схема для оновлення існуючого статусу. Успадковує поля від BaseDictUpdateSchema.
    """
    # Тут можна додати специфічні поля або валідатори для оновлення статусу.
    # Наприклад, якщо деякі поля статусів не можна змінювати після створення.

    # Якщо StatusModel мав би поле `color`:
    # color: Optional[str] = Field(None, pattern=r"^#(?:[0-9a-fA-F]{3}){1,2}$", description="Новий колір статусу (#RRGGBB)")
    pass

# --- Схема для фільтрації списку статусів (якщо потрібно) ---
# class StatusFilterSchema(BaseSchema):
#     name_contains: Optional[str] = None
#     code_equals: Optional[str] = None
#     is_active: Optional[bool] = None # Потребуватиме перетворення в state_id або фільтрації за is_deleted

# TODO: Переконатися, що всі необхідні поля з StatusModel відображені в StatusSchema.
# StatusModel успадковує від BaseDictModel, який успадковує від BaseMainModel.
# BaseDictSchema успадковує від BaseMainSchema і додає `code`.
# Отже, StatusSchema повинна мати:
# id, name, description, code, state_id, group_id, created_at, updated_at, deleted_at, is_deleted, notes.
# Це все вже є в BaseDictSchema.

# TODO: Додати приклади використання цих схем у коментарях або документації,
# коли будуть створюватися ендпоінти API.

# Назви схем:
# - `StatusSchema`: для відповіді API (читання одного або списку).
# - `StatusCreateSchema`: для тіла запиту при створенні.
# - `StatusUpdateSchema`: для тіла запиту при оновленні.
# Це стандартний підхід.
# `group_id` в `BaseDictSchema` є `Optional[uuid.UUID]`. Для глобальних статусів він буде `None`.
# Якщо статуси можуть бути специфічними для груп, то `group_id` буде встановлено.
# `state_id` в `BaseDictSchema` - це статус самого запису довідника "статус" (наприклад, чи активний цей тип статусу для використання).
# Це може здатися мета-рівнем, але дозволяє деактивувати певні типи статусів без їх видалення.
# Якщо це зайве, `state_id` можна прибрати з базових схем довідників або зробити завжди `None`.
# Поки що залишаю як є, це дає гнучкість.
# Для `StatusCreateSchema` та `StatusUpdateSchema` поля `name` та `code` є ключовими.
# `description`, `state_id`, `notes` - опціональні або можуть мати значення за замовчуванням.
# `is_deleted` в `StatusUpdateSchema` для "м'якого" видалення.
# Все виглядає узгоджено.
