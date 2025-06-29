# backend/app/src/schemas/bonuses/reward.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `RewardModel`.
Схеми використовуються для валідації даних при створенні, оновленні
та відображенні нагород, доступних для "купівлі" за бонуси.
"""

from pydantic import Field, HttpUrl
from typing import Optional, List, ForwardRef
import uuid
from datetime import datetime
from decimal import Decimal # Використовуємо Decimal

from backend.app.src.schemas.base import BaseMainSchema, BaseSchema
# Потрібно буде імпортувати схеми для зв'язків:
# from backend.app.src.schemas.groups.group import GroupSimpleSchema (group_id вже є)
# from backend.app.src.schemas.dictionaries.status import StatusSchema (state_id вже є)
# from backend.app.src.schemas.files.file import FileSchema (або URL іконки)
# from backend.app.src.schemas.dictionaries.bonus_type import BonusTypeSchema

from typing import TYPE_CHECKING # Додано TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.src.schemas.dictionaries.bonus_type import BonusTypeSchema
    from backend.app.src.schemas.dictionaries.status import StatusSchema
    from backend.app.src.schemas.files.file import FileSchema

# BonusTypeSchema = ForwardRef('backend.app.src.schemas.dictionaries.bonus_type.BonusTypeSchema') # Перенесено
# FileSchema = ForwardRef('backend.app.src.schemas.files.file.FileSchema') # Або просто URL

# --- Схема для відображення інформації про нагороду (для читання) ---
class RewardSchema(BaseMainSchema):
    """
    Повна схема для представлення нагороди.
    Успадковує `id, name, description, state_id, group_id, created_at, updated_at, deleted_at, is_deleted, notes`
    від `BaseMainSchema`.
    """
    # `group_id` з BaseMainSchema - ID групи, де доступна нагорода.

    cost_points: Decimal = Field(..., description="Вартість нагороди в бонусних балах")
    bonus_type_code: str = Field(..., max_length=50, description="Код типу бонусів, в яких вимірюється вартість (з BonusTypeModel.code)")

    quantity_available: Optional[int] = Field(None, ge=0, description="Доступна кількість нагород (NULL - необмежено)")
    max_per_user: Optional[int] = Field(None, ge=1, description="Максимальна кількість, яку один користувач може отримати (NULL - без обмежень)")
    is_recurring_purchase: bool = Field(..., description="Чи можна купувати цю нагороду повторно")

    icon_file_id: Optional[uuid.UUID] = Field(None, description="ID файлу іконки нагороди")
    # icon_url: Optional[HttpUrl] = Field(None, description="URL іконки нагороди") # Може генеруватися

    # --- Розгорнуті зв'язки (приклад) ---
    # group: Optional[GroupSimpleSchema] = Field(None, description="Група, якій належить нагорода") # `group_id` вже є
    state: Optional['StatusSchema'] = Field(None, description="Статус нагороди") # Рядкове посилання
    icon: Optional['FileSchema'] = Field(None, description="Файл іконки нагороди") # Або `icon_url`, Рядкове посилання
    bonus_type: Optional['BonusTypeSchema'] = Field(None, description="Тип бонусу, в якому вказана вартість") # Рядкове посилання

    # Статистика покупок (обчислювані поля, додаються сервісом)
    total_purchased_count: Optional[int] = Field(None, description="Загальна кількість куплених екземплярів цієї нагороди")


# --- Схема для створення нової нагороди ---
class RewardCreateSchema(BaseSchema):
    """
    Схема для створення нової нагороди.
    """
    name: str = Field(..., min_length=1, max_length=255, description="Назва нагороди")
    description: Optional[str] = Field(None, description="Детальний опис нагороди")
    # group_id: uuid.UUID # З URL або контексту
    state_id: Optional[uuid.UUID] = Field(None, description="Початковий статус нагороди (наприклад, 'доступна')")

    cost_points: Decimal = Field(..., gt=Decimal(0), description="Вартість нагороди (має бути більше 0)")
    bonus_type_code: str = Field(..., max_length=50, description="Код типу бонусів для вартості (має відповідати типу бонусів групи)")

    quantity_available: Optional[int] = Field(None, ge=0, description="Доступна кількість (NULL - необмежено, 0 - недоступна)")
    max_per_user: Optional[int] = Field(None, ge=1, description="Макс. на користувача (NULL - без обмежень)")
    is_recurring_purchase: bool = Field(default=True, description="Чи можна купувати повторно (за замовчуванням True)")

    icon_file_id: Optional[uuid.UUID] = Field(None, description="ID файлу іконки")
    notes: Optional[str] = Field(None, description="Додаткові нотатки")


# --- Схема для оновлення існуючої нагороди ---
class RewardUpdateSchema(BaseSchema):
    """
    Схема для оновлення існуючої нагороди.
    Всі поля опціональні.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    state_id: Optional[uuid.UUID] = Field(None) # Зміна статусу (доступна/недоступна)

    cost_points: Optional[Decimal] = Field(None, gt=Decimal(0))
    # bonus_type_code: Optional[str] = Field(None, max_length=50) # Зміна типу валюти для нагороди - складно, зазвичай не робиться

    quantity_available: Optional[int] = Field(None, ge=0) # Дозволяємо NULL для зняття обмеження
    max_per_user: Optional[int] = Field(None, ge=1) # Дозволяємо NULL
    is_recurring_purchase: Optional[bool] = Field(None)

    icon_file_id: Optional[uuid.UUID] = Field(None)
    notes: Optional[str] = Field(None)
    is_deleted: Optional[bool] = Field(None) # Для "м'якого" видалення

# RewardSchema.model_rebuild() # Для ForwardRef

# TODO: Переконатися, що схеми відповідають моделі `RewardModel`.
# `RewardModel` успадковує від `BaseMainModel`.
# `RewardSchema` успадковує від `BaseMainSchema` і додає специфічні поля нагороди.
# Використання `Decimal` для `cost_points`.
#
# Поля: `cost_points`, `bonus_type_code`, `quantity_available`, `max_per_user`, `is_recurring_purchase`, `icon_file_id`.
# `bonus_type_code` вказує, в якій "валюті" вказана вартість. Це має бути узгоджено
# з `AccountModel.bonus_type_code` для рахунків користувачів у групі, де ця нагорода доступна.
#
# `RewardCreateSchema` та `RewardUpdateSchema` містять відповідні поля.
# `gt=Decimal(0)` для `cost_points` гарантує, що вартість позитивна.
# `ge=0` для `quantity_available`.
# `ge=1` для `max_per_user`.
#
# Розгорнуті зв'язки в `RewardSchema` (group, state, icon, bonus_type) додані з `ForwardRef` або закоментовані.
# `total_purchased_count` - приклад обчислюваного поля.
#
# `group_id` з `BaseMainSchema` для `RewardModel` має бути NOT NULL.
# `state_id` для статусу нагороди.
# `name`, `description`, `notes`, `deleted_at`, `is_deleted` успадковані.
# Все виглядає узгоджено.
#
# `icon_url` (закоментоване) - похідне поле, яке може генеруватися сервісом на основі `icon_file_id`.
# Зв'язок `bonus_type` з `BonusTypeSchema` дозволить отримати деталі про валюту вартості.
# Все виглядає добре.

RewardSchema.model_rebuild()
RewardCreateSchema.model_rebuild()
RewardUpdateSchema.model_rebuild()
