# backend/app/src/core/base.py
# -*- coding: utf-8 -*-
# # Модуль базових елементів ядра для програми Kudos (Virtus).
# #
# # Цей модуль визначає загальні змінні типи (`TypeVar`) для використання
# # при побудові узагальнених (Generic) базових класів, таких як базові
# # сервіси або репозиторії. Це дозволяє забезпечити типізацію для
# # моделей SQLAlchemy (представлених через Pydantic моделі для API)
# # та схем Pydantic, що використовуються для операцій створення та оновлення.
# #
# # Визначені TypeVars:
# # - `ModelType`: Тип Pydantic моделі, що представляє дані з БД.
# # - `CreateSchemaType`: Тип Pydantic схеми для створення записів.
# # - `UpdateSchemaType`: Тип Pydantic схеми для оновлення записів.

from typing import TypeVar
from pydantic import BaseModel # BaseModel використовується як обмеження (bound) для TypeVar

# Загальні TypeVariable (змінні типи) для моделей Pydantic.
# Вони призначені для використання в узагальнених (Generic) базових класах,
# таких як базові сервіси або репозиторії, для забезпечення типізації
# моделей SQLAlchemy (які можуть бути представлені Pydantic моделями для API відповідей)
# та схем Pydantic (для створення та оновлення даних).

# ModelType: Очікується, що це буде Pydantic модель, яка представляє дані,
#            що повертаються з бази даних (наприклад, `UserReadSchema` або `TaskSchema`).
#            Часто використовується як тип повернення для операцій читання (get, get_multi).
ModelType = TypeVar("ModelType", bound=BaseModel)

# CreateSchemaType: Очікується, що це буде Pydantic схема, яка використовується для створення
#                   нового екземпляра моделі (наприклад, `UserCreateSchema` або `TaskCreateSchema`).
#                   Зазвичай передається в методи `create`.
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)

# UpdateSchemaType: Очікується, що це буде Pydantic схема, яка використовується для оновлення
#                   існуючого екземпляра моделі (наприклад, `UserUpdateSchema` або `TaskUpdateSchema`).
#                   Зазвичай передається в методи `update`.
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

# --- Історична довідка щодо попередніх класів у цьому файлі ---
# Раніше в цьому файлі могли існувати класи, такі як `BaseCoreComponent` та `ObjectConfigurator`.
#
# `BaseCoreComponent` (якщо такий був) був видалений через надмірну загальність та відсутність
# конкретної практичної користі для базових класів сервісів чи репозиторіїв.
# Специфічні базові класи (наприклад, `BaseRepository`, `BaseService`) краще розміщувати
# у відповідних пакетах (`repositories/base.py`, `services/base.py`), де вони можуть
# мати більш конкретні залежності (наприклад, від `AsyncSession` для репозиторіїв).
#
# `ObjectConfigurator` (якщо такий був) був видалений, оскільки сучасні версії Pydantic
# (особливо Pydantic V2) надають потужні вбудовані механізми для ініціалізації,
# валідації та оновлення моделей з диктів або інших об'єктів (наприклад,
# `model_validate()`, `model_construct()`, `model_copy(update=...)`).
# Це робить окремий клас-конфігуратор зайвим.

# --- Приклад використання TypeVars у базовому сервісі ---
# Наведений нижче приклад (закоментований) ілюструє, як ці TypeVars можуть
# використовуватися для створення узагальненого базового класу для сервісів,
# що виконують CRUD-операції.
#
# from typing import Generic, Optional, Any
# from sqlalchemy.ext.asyncio import AsyncSession # Потрібна для роботи з БД
#
# class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
#     """
#     Узагальнений базовий клас для сервісів, що реалізують CRUD-операції.
#     """
#     # def __init__(self, model_cls: Type[ModelType]): # Модель SQLAlchemy може передаватися сюди
#     #     self.model_cls = model_cls
#
#     async def get(self, db: AsyncSession, item_id: Any) -> Optional[ModelType]:
#         # Логіка отримання одного запису з БД за ID
#         # Повертає екземпляр ModelType або None
#         raise NotImplementedError
#
#     async def get_multi(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
#         # Логіка отримання списку записів з БД з пагінацією
#         # Повертає список екземплярів ModelType
#         raise NotImplementedError
#
#     async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
#         # Логіка створення нового запису в БД на основі вхідної схеми CreateSchemaType
#         # Повертає створений екземпляр ModelType
#         raise NotImplementedError
#
#     async def update(
#         self, db: AsyncSession, *, db_obj: ModelType, obj_in: UpdateSchemaType
#     ) -> ModelType:
#         # Логіка оновлення існуючого запису `db_obj` (типу ModelType)
#         # даними зі схеми `obj_in` (типу UpdateSchemaType)
#         # Повертає оновлений екземпляр ModelType
#         raise NotImplementedError
#
#     async def remove(self, db: AsyncSession, *, item_id: Any) -> Optional[ModelType]:
#         # Логіка видалення запису з БД за ID
#         # Може повертати видалений екземпляр ModelType або None
#         raise NotImplementedError
#
# Подібні базові класи можуть бути створені для репозиторіїв в `backend/app/src/repositories/base.py`.
