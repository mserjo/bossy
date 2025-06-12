# backend/app/src/core/base.py
# -*- coding: utf-8 -*-
"""Базові типи для ядра додатку.

Цей модуль визначає загальні змінні типи (`TypeVar`), які призначені
для використання при побудові узагальнених (Generic) базових класів.
Ці типи допомагають забезпечити строгу типізацію для сервісів,
репозиторіїв та інших компонентів, що оперують моделями даних
SQLAlchemy (представленими через схеми Pydantic) та схемами Pydantic
для створення та оновлення даних.

Визначені TypeVars:
- `ModelType`: Представляє тип схеми Pydantic, що використовується для
               відображення даних моделі SQLAlchemy (зазвичай для відповіді API).
- `CreateSchemaType`: Представляє тип схеми Pydantic, що використовується
                      для створення нових екземплярів моделі в базі даних.
- `UpdateSchemaType`: Представляє тип схеми Pydantic, що використовується
                      для оновлення існуючих екземплярів моделі в базі даних.

Використання цих `TypeVar` дозволяє створювати гнучкі та типізовані
інтерфейси для базових класів, що зменшує дублювання коду, покращує
читабельність та підтримку кодової бази завдяки статичній перевірці типів.
"""

from typing import TypeVar

from pydantic import BaseModel

# ModelType: Очікується, що це буде схема Pydantic, яка відображає модель SQLAlchemy.
# Наприклад, якщо є модель SQLAlchemy `User`, то `ModelType` може бути `UserSchema` (Pydantic модель).
# Цей тип часто використовується як тип повернення для операцій читання даних.
ModelType = TypeVar("ModelType", bound=BaseModel)

# CreateSchemaType: Очікується, що це буде схема Pydantic, призначена для валідації даних
# при створенні нового об'єкта в базі даних (наприклад, `UserCreateSchema`).
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)

# UpdateSchemaType: Очікується, що це буде схема Pydantic, призначена для валідації даних
# при оновленні існуючого об'єкта в базі даних (наприклад, `UserUpdateSchema`).
# Зазвичай містить опціональні поля.
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

# Коментар щодо попереднього вмісту файлу (якщо актуально для історії змін):
# Раніше цей файл міг містити базові класи, такі як `BaseCoreComponent` або `ObjectConfigurator`.
# Однак, вони були видалені або перенесені для спрощення структури ядра, оскільки:
# - `BaseCoreComponent` міг бути надто абстрактним і не надавати значної конкретної користі,
#   а специфічна логіка краще реалізується у відповідних базових класах сервісів/репозиторіїв.
# - `ObjectConfigurator` (якщо такий був) міг дублювати функціональність Pydantic,
#   який вже надає потужні механізми для ініціалізації, валідації та оновлення моделей
#   з словників (наприклад, `model_validate()`, `model_construct()`, `model_copy(update=...)`).

# Приклад використання цих TypeVars можна знайти в реалізації узагальнених
# базових класів для CRUD операцій, наприклад, у файлах типу
# `backend/app/src/repositories/base_repository.py` або
# `backend/app/src/services/base_service.py` (якщо такі класи будуть створені).
#
# Наприклад, базовий сервіс міг би виглядати так:
#
# from typing import Generic, Optional, Any
# from sqlalchemy.ext.asyncio import AsyncSession
#
# class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
#     # ... реалізація методів ...
#     async def get(self, db: AsyncSession, item_id: Any) -> Optional[ModelType]:
#         # логіка отримання об'єкта
#         pass
#
#     async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
#         # логіка створення об'єкта
#         pass
#
#     async def update(
#         self, db: AsyncSession, *, db_obj: ModelType, obj_in: UpdateSchemaType
#     ) -> ModelType:
#         # логіка оновлення об'єкта
#         pass
#
# Цей модуль не містить активного коду, що виконується, а лише визначення типів.
# Тому логування тут не потрібне.
