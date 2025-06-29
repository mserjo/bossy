# backend/app/src/schemas/base.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає базові Pydantic схеми, які слугуватимуть основою
для інших схем даних у проекті. Це допомагає уникнути дублювання коду
та забезпечити консистентність схем.
"""

from pydantic import BaseModel as PydanticBaseModel, ConfigDict, Field
from typing import Optional, TypeVar, Generic
from datetime import datetime
import uuid

# Загальний тип для даних відповіді пагінації
DataType = TypeVar('DataType')

class BaseSchema(PydanticBaseModel):
    """
    Базова Pydantic схема з налаштуваннями за замовчуванням.
    Всі інші схеми повинні успадковувати цей клас.
    """
    # ConfigDict для Pydantic v2 (замість class Config в v1)
    # from_attributes = True (замість orm_mode = True) дозволяє схемі
    # завантажувати дані з атрибутів ORM об'єкта.
    model_config = ConfigDict(
        from_attributes=True,  # Дозволяє створювати схему з ORM моделі
        populate_by_name=True, # Дозволяє використовувати аліаси полів при ініціалізації
        # extra='ignore',      # Ігнорувати зайві поля при валідації (за замовчуванням 'ignore' в v2)
                               # Можна змінити на 'forbid', якщо потрібно строгіше
    )

    # TODO: Розглянути додавання глобальних валідаторів або конфігурацій,
    # якщо вони будуть потрібні для всіх схем (наприклад, кастомна серіалізація дат).

class IdentifiedSchema(BaseSchema):
    """
    Схема для сутностей, що мають унікальний ідентифікатор `id`.
    """
    id: uuid.UUID = Field(..., description="Унікальний ідентифікатор сутності (UUID)")

class TimestampedSchema(BaseSchema):
    """
    Схема для сутностей, що мають позначки часу `created_at` та `updated_at`.
    """
    created_at: datetime = Field(..., description="Дата та час створення запису")
    updated_at: datetime = Field(..., description="Дата та час останнього оновлення запису")

class AuditDatesSchema(TimestampedSchema):
    """
    Розширена схема з позначками часу, що включає `id`.
    Часто використовується для схем відповіді API (xxxSchema).
    """
    id: uuid.UUID = Field(..., description="Унікальний ідентифікатор сутності (UUID)")

class BaseMainSchema(AuditDatesSchema):
    """
    Базова схема для основних сутностей, що успадковують BaseMainModel.
    Включає `id`, `name`, `description`, `state_id`, `group_id`, `deleted_at`, `is_deleted`, `notes`,
    а також `created_at` та `updated_at` з AuditDatesSchema.
    """
    name: str = Field(..., min_length=1, max_length=255, description="Назва сутності")
    description: Optional[str] = Field(None, description="Детальний опис сутності")

    state_id: Optional[uuid.UUID] = Field(None, description="Ідентифікатор статусу сутності")
    group_id: Optional[uuid.UUID] = Field(None, description="Ідентифікатор групи, до якої належить сутність")

    deleted_at: Optional[datetime] = Field(None, description="Дата та час \"м'якого\" видалення запису")
    is_deleted: bool = Field(default=False, description="Прапорець, чи запис видалено (\"м'яке\" видалення)")
    notes: Optional[str] = Field(None, description="Додаткові нотатки або коментарі до сутності")

    # TODO: Додати поля для зв'язків (наприклад, `state: Optional[StatusSchema]`),
    # коли відповідні схеми будуть створені. Це робиться через `model_rebuild()`
    # або визначаючи поля з Optional[ForwardRef('OtherSchema')].
    # state: Optional["StatusSchema"] = None # Приклад, потребує ForwardRef та model_rebuild
    # group: Optional["GroupSchema"] = None # Приклад

class PaginatedResponse(BaseSchema, Generic[DataType]):
    """
    Узагальнена схема для пагінованих відповідей API.
    """
    total: int = Field(..., description="Загальна кількість елементів")
    page: int = Field(..., ge=1, description="Номер поточної сторінки (починаючи з 1)")
    size: int = Field(..., ge=1, description="Кількість елементів на сторінці")
    pages: int = Field(..., ge=0, description="Загальна кількість сторінок")
    items: list[DataType] = Field(..., description="Список елементів на поточній сторінці")
    # next_page: Optional[int] = Field(None, description="Номер наступної сторінки, якщо є")
    # prev_page: Optional[int] = Field(None, description="Номер попередньої сторінки, якщо є")

    model_config = ConfigDict(
        from_attributes=True, # Успадковано, але для ясності
        arbitrary_types_allowed=True # Дозволяє використовувати типи, які Pydantic не знає за замовчуванням
    )

class MessageResponse(BaseSchema):
    """
    Схема для стандартної відповіді з повідомленням.
    """
    message: str = Field(..., description="Повідомлення відповіді")

class DetailResponse(MessageResponse):
    """
    Схема для відповіді з повідомленням та деталями.
    """
    detail: Optional[str] = Field(None, description="Додаткові деталі")

# TODO: Додати базові схеми для Create та Update операцій, якщо будуть спільні патерни.
# Наприклад, BaseCreateSchema, BaseUpdateSchema.
# Зазвичай схеми для створення/оновлення визначаються для кожної сутності окремо,
# оскільки набір полів та їх опціональність відрізняються.

# TODO: Розглянути використання `alias_generator` в `ConfigDict` для автоматичного
# перетворення snake_case в camelCase для ключів JSON, якщо API має таку конвенцію.
# model_config = ConfigDict(
#     alias_generator=lambda field_name: field_name.lower().replace("_", ""), # простий camelCase
#     populate_by_name=True, # Дозволяє використовувати і аліаси, і оригінальні імена полів
# )
# Або використовувати `pydantic-camel` для більш гнучкого налаштування.
# Поки що залишаємо snake_case, що є типовим для Python/FastAPI.

# TODO: Додати документацію щодо використання Pydantic v2 `ConfigDict` замість `class Config`.
# `from_attributes=True` замість `orm_mode = True`.
# `Field(..., description="...")` для додавання описів полів, які використовуються в OpenAPI документації.
# Використання `Optional[Type]` або `Type | None` для опціональних полів.
# `default=...` або `default_factory=...` для значень за замовчуванням.
# Валідатори (`@validator`, `@root_validator` в v1; `@field_validator`, `@model_validator` в v2)
# будуть додаватися в конкретних схемах за потреби.
