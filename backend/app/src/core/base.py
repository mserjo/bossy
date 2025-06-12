# backend/app/src/core/base.py
# -*- coding: utf-8 -*-
"""
Базові елементи ядра програми Kudos.

Цей модуль визначає загальні типи (TypeVars), які використовуються для побудови
узагальнених базових класів для сервісів, репозиторіїв та інших компонентів,
що працюють з моделями даних Pydantic.

Визначені TypeVars:
- `ModelType`: Представляє тип моделі SQLAlchemy, що відображається Pydantic моделлю (зазвичай для відповіді).
- `CreateSchemaType`: Представляє тип Pydantic схеми, що використовується для створення нових записів.
- `UpdateSchemaType`: Представляє тип Pydantic схеми, що використовується для оновлення існуючих записів.

Ці типи дозволяють створювати гнучкі та типізовані базові класи, зменшуючи дублювання коду
та покращуючи підтримку кодової бази.
"""

from typing import TypeVar
from pydantic import BaseModel

# Загальні TypeVariable (змінні типи) для моделей Pydantic.
# Вони призначені для використання в узагальнених (Generic) базових класах,
# таких як базові сервіси або репозиторії, для забезпечення типізації
# моделей SQLAlchemy (які представлені Pydantic моделями для API) та схем Pydantic.

# ModelType: Очікується, що це буде Pydantic модель, яка представляє дані з бази даних (наприклад, User).
# Часто використовується як тип повернення для операцій читання.
ModelType = TypeVar("ModelType", bound=BaseModel)

# CreateSchemaType: Очікується, що це буде Pydantic схема, яка використовується для створення
# нового екземпляра моделі (наприклад, UserCreate).
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)

# UpdateSchemaType: Очікується, що це буде Pydantic схема, яка використовується для оновлення
# існуючого екземпляра моделі (наприклад, UserUpdate).
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

# Раніше тут були класи BaseCoreComponent та ObjectConfigurator.
# BaseCoreComponent був видалений через надмірну загальність та відсутність конкретної користі
# для базових класів сервісів/репозиторіїв, які краще розміщувати у відповідних пакетах.
# ObjectConfigurator був видалений, оскільки Pydantic моделі мають власні потужні механізми
# для ініціалізації та оновлення з диктів (`model_validate`, `model_construct`, `model_copy(update=...)`).

# Приклад використання цих TypeVars можна знайти в базових класах для CRUD операцій,
# наприклад, у `backend/app/src/repositories/base.py` або `backend/app/src/services/base.py` (якщо такі будуть створені).
# class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
#     async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
#         ...
#     async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
#         ...
#     async def update(self, db: AsyncSession, *, db_obj: ModelType, obj_in: UpdateSchemaType) -> ModelType:
#         ...
