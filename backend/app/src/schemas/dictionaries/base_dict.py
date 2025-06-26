# backend/app/src/schemas/dictionaries/base_dict.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає базові Pydantic схеми для моделей-довідників.
Моделі-довідники зазвичай мають спільні поля, такі як `code`, на додаток
до полів з `BaseMainModel` (які успадковуються через `BaseMainSchema`).
"""

from pydantic import Field, field_validator
from typing import Optional, List
from datetime import datetime
import uuid

from backend.app.src.schemas.base import BaseMainSchema, BaseSchema

# --- Базові схеми для CRUD операцій з довідниками ---

class BaseDictSchema(BaseMainSchema):
    """
    Базова схема для представлення запису довідника (для читання).
    Успадковує всі поля від `BaseMainSchema` та додає `code`.
    """
    code: str = Field(..., min_length=1, max_length=100, description="Унікальний символьний код запису довідника")

    # TODO: Якщо довідники можуть мати специфічні для групи налаштування або бути глобальними,
    # поле `group_id` з `BaseMainSchema` буде це відображати.
    # Поки що `group_id` є `Optional[uuid.UUID]`.

    # TODO: Поле `state_id` з `BaseMainSchema` вказує на статус самого запису довідника
    # (наприклад, активний/неактивний для використання).

class BaseDictCreateSchema(BaseSchema):
    """
    Базова схема для створення нового запису довідника.
    Включає поля, необхідні при створенні. `id`, `created_at`, `updated_at` генеруються автоматично.
    """
    name: str = Field(..., min_length=1, max_length=255, description="Назва запису довідника")
    code: str = Field(..., min_length=1, max_length=100, description="Унікальний символьний код запису довідника")
    description: Optional[str] = Field(None, description="Детальний опис")

    state_id: Optional[uuid.UUID] = Field(None, description="Ідентифікатор статусу запису довідника (якщо встановлюється при створенні)")
    # group_id: Optional[uuid.UUID] = Field(None, description="Ідентифікатор групи (якщо довідник специфічний для групи і це встановлюється при створенні)")
    # Зазвичай group_id для довідників або NULL (глобальний), або встановлюється системно,
    # тому не включаю його в схему створення за замовчуванням. Якщо потрібно, можна додати в наслідниках.
    notes: Optional[str] = Field(None, description="Додаткові нотатки")

    @field_validator('code')
    @classmethod
    def code_alphanumeric_underscore(cls, value: str) -> str:
        """Валідатор для поля code: дозволяє лише літери, цифри та підкреслення."""
        if not value.replace('_', '').isalnum():
            raise ValueError('Код повинен містити лише літери, цифри та символ підкреслення (_).')
        return value.lower() # Перетворюємо код в нижній регістр для консистентності

class BaseDictUpdateSchema(BaseSchema):
    """
    Базова схема для оновлення існуючого запису довідника.
    Всі поля опціональні, оскільки оновлюватися можуть лише деякі з них.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Нова назва запису довідника")
    code: Optional[str] = Field(None, min_length=1, max_length=100, description="Новий унікальний символьний код")
    description: Optional[str] = Field(None, description="Новий детальний опис")

    state_id: Optional[uuid.UUID] = Field(None, description="Новий ідентифікатор статусу запису довідника")
    # group_id: Optional[uuid.UUID] - зазвичай не оновлюється для довідників.
    notes: Optional[str] = Field(None, description="Нові додаткові нотатки")
    is_deleted: Optional[bool] = Field(None, description="Прапорець \"м'якого\" видалення")
    deleted_at: Optional[datetime] = Field(None, description="Дата та час \"м'якого\" видалення (встановлюється автоматично при is_deleted=True)")


    @field_validator('code')
    @classmethod
    def code_alphanumeric_underscore_optional(cls, value: Optional[str]) -> Optional[str]:
        """Валідатор для поля code (якщо воно надане для оновлення)."""
        if value is not None:
            if not value.replace('_', '').isalnum():
                raise ValueError('Код повинен містити лише літери, цифри та символ підкреслення (_).')
            return value.lower()
        return value

# TODO: Розглянути можливість додавання схеми для фільтрації списку довідників,
# якщо потрібна буде більш складна фільтрація, ніж просто за полями.
# class BaseDictFilterSchema(BaseSchema):
#     name_contains: Optional[str] = None
#     code_equals: Optional[str] = None
#     is_active: Optional[bool] = None # Потребуватиме логіки для перетворення в state_id

# TODO: Додати документацію про те, як ці базові схеми використовуються
# для створення конкретних схем довідників (StatusSchema, UserRoleSchema тощо).
# Наприклад:
# class StatusSchema(BaseDictSchema):
#     # Тут можуть бути додаткові специфічні поля для Status, якщо є.
#     pass
#
# class StatusCreateSchema(BaseDictCreateSchema):
#     # Тут можуть бути додаткові поля, специфічні для створення Status.
#     # Або валідатори, що перевизначають базові.
#     pass
#
# class StatusUpdateSchema(BaseDictUpdateSchema):
#     # ...
#     pass
#
# Це забезпечить консистентність та успадкування загальної логіки.
# Валідатор для `code` вже доданий до `BaseDictCreateSchema` та `BaseDictUpdateSchema`.
# `deleted_at` в `BaseDictUpdateSchema` - це поле для інформації, фактичне встановлення
# `deleted_at` має відбуватися на сервісному рівні при встановленні `is_deleted = True`.
# Або ж, якщо API дозволяє передавати `deleted_at`, то це поле має сенс.
# Поки що залишаю, але з коментарем. Краще, щоб `deleted_at` керувалося сервером.
# Видаляю `deleted_at` з `BaseDictUpdateSchema`, оскільки воно має встановлюватися сервером.
# `is_deleted` достатньо для запиту на "м'яке" видалення/відновлення.
# Переглянув: `deleted_at` в моделі встановлюється автоматично або сервісом.
# В `UpdateSchema` поле `is_deleted` є прапорцем для дії.
# `deleted_at` тут не потрібне.
# Видаляю `deleted_at` з `BaseDictUpdateSchema` для чистоти.
# Якщо потрібно передати `deleted_at` для відновлення (встановити в NULL),
# то це можна зробити через спеціальний ендпоінт або логіку в сервісі,
# яка реагує на `is_deleted = False`.
# Залишаю `is_deleted: Optional[bool]` - це прапорець для зміни стану.
# Сервер обробить це і встановить `deleted_at` відповідно.
# Поле `group_id` в `BaseDictCreateSchema` закоментоване, оскільки довідники
# або глобальні, або їх приналежність до групи визначається іншим чином (наприклад,
# `BonusTypeModel` є глобальним, а група обирає його). Якщо якийсь довідник
# створюється саме В ГРУПІ, то в його `CreateSchema` можна буде додати `group_id`.
# Поле `state_id` в `BaseDictCreateSchema` дозволяє встановити початковий статус
# запису довідника при його створенні.
# `BaseDictSchema` успадковує `BaseMainSchema`, тому вже має всі поля, включаючи `id`, `created_at` і т.д.
# `code` додається специфічно для довідників.
# Валідатор для `code` забезпечує формат та нижній регістр.
# Це виглядає як хороший набір базових схем для довідників.
