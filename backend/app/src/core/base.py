# backend/app/src/core/base.py
# -*- coding: utf-8 -*-
"""
Цей модуль призначений для визначення базових класів для сервісів та репозиторіїв.
Ці базові класи можуть містити спільну логіку CRUD операцій,
роботи з сесією бази даних, обробки помилок тощо,
що дозволяє уникнути дублювання коду в конкретних реалізаціях сервісів та репозиторіїв.

На даному етапі створюються заглушки для цих класів, оскільки їх повна
реалізація залежатиме від конкретних моделей, схем та загальної архітектури
доступу до даних, яка буде обрана (наприклад, чистий Repository Pattern,
або сервіси, що напряму працюють з ORM).
"""

from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy import select, update, delete, func # type: ignore
from sqlalchemy.sql.expression import literal_column # type: ignore
from typing import TypeVar, Generic, Type, List, Optional, Any, Dict, Union
import uuid

# Імпорт базової моделі SQLAlchemy (для типізації)
from backend.app.src.models.base import BaseModel as SQLABaseModel # Перейменовуємо, щоб уникнути конфлікту з Pydantic BaseModel
# Імпорт базової схеми Pydantic (для типізації)
from backend.app.src.schemas.base import BaseSchema as PydanticBaseSchema
from backend.app.src.core.exceptions import NotFoundException, DatabaseErrorException

# --- Типізація для генериків ---
# ModelType: Тип моделі SQLAlchemy (наприклад, UserModel, GroupModel)
ModelType = TypeVar('ModelType', bound=SQLABaseModel)
# CreateSchemaType: Тип Pydantic схеми для створення (наприклад, UserCreateSchema)
CreateSchemaType = TypeVar('CreateSchemaType', bound=PydanticBaseSchema)
# UpdateSchemaType: Тип Pydantic схеми для оновлення (наприклад, UserUpdateSchema)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=PydanticBaseSchema)
# SchemaType: Тип Pydantic схеми для читання/відповіді (наприклад, UserSchema)
SchemaType = TypeVar('SchemaType', bound=PydanticBaseSchema)


# --- Базовий клас для репозиторіїв (Repository Pattern) ---
class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Базовий клас для репозиторіїв, що реалізує CRUD операції.
    Працює з асинхронною сесією SQLAlchemy.

    Атрибути:
        _model (Type[ModelType]): Клас моделі SQLAlchemy, з яким працює репозиторій.
    """
    def __init__(self, model: Type[ModelType]):
        """
        Ініціалізатор репозиторію.
        :param model: Клас моделі SQLAlchemy.
        """
        self._model = model

    async def get_by_id(self, db: AsyncSession, item_id: uuid.UUID) -> Optional[ModelType]:
        """Отримує запис за ID."""
        try:
            query = select(self._model).where(self._model.id == item_id)
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            # TODO: Логування помилки
            # logger.error(f"Помилка отримання {self._model.__name__} за ID {item_id}: {e}")
            raise DatabaseErrorException(f"Помилка отримання {self._model.__name__} з БД.")

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100,
        filters: Optional[Dict[str, Any]] = None, # Приклад: {"name": "Test", "is_active": True}
        order_by: Optional[List[str]] = None # Приклад: ["name_asc", "created_at_desc"]
    ) -> List[ModelType]:
        """Отримує список записів з можливістю фільтрації та сортування."""
        try:
            query = select(self._model)

            # TODO: Реалізувати логіку фільтрації на основі `filters`
            if filters:
                for field, value in filters.items():
                    if hasattr(self._model, field):
                        query = query.where(getattr(self._model, field) == value)

            # TODO: Реалізувати логіку сортування на основі `order_by`
            if order_by:
                for ob_field_direction in order_by:
                    direction = "desc" if ob_field_direction.endswith("_desc") else "asc"
                    field_name = ob_field_direction.removesuffix("_desc").removesuffix("_asc")
                    if hasattr(self._model, field_name):
                        column = getattr(self._model, field_name)
                        query = query.order_by(column.desc() if direction == "desc" else column.asc())

            query = query.offset(skip).limit(limit)
            result = await db.execute(query)
            return list(result.scalars().all()) # Перетворюємо результат в список
        except Exception as e:
            # logger.error(f"Помилка отримання списку {self._model.__name__}: {e}")
            raise DatabaseErrorException(f"Помилка отримання списку {self._model.__name__} з БД.")

    async def get_count(
        self, db: AsyncSession, *,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Отримує загальну кількість записів з можливістю фільтрації."""
        try:
            query = select(func.count(literal_column("*"))).select_from(self._model) # Використовуємо func.count()

            if filters:
                for field, value in filters.items():
                    if hasattr(self._model, field):
                        query = query.where(getattr(self._model, field) == value)

            result = await db.execute(query)
            count = result.scalar_one()
            return count if count is not None else 0
        except Exception as e:
            # logger.error(f"Помилка отримання кількості {self._model.__name__}: {e}")
            raise DatabaseErrorException(f"Помилка отримання кількості {self._model.__name__} з БД.")


    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """Створює новий запис."""
        try:
            # obj_in_data = obj_in.model_dump() # Pydantic v2, отримуємо словник з схеми
            # SQLAlchemy моделі очікують словник або атрибути.
            # Якщо схема має поля, яких немає в моделі, їх треба відфільтрувати.
            # Або передавати лише ті поля, які є в моделі.
            # Pydantic v2: obj_in.model_dump(exclude_unset=True) - для часткових оновлень

            # Простий варіант: передаємо весь словник, SQLAlchemy візьме потрібні поля.
            db_obj = self._model(**obj_in.model_dump())
            db.add(db_obj)
            await db.flush() # Потрібен flush, щоб отримати ID та інші автогенеровані поля перед commit
            await db.refresh(db_obj) # Оновлюємо об'єкт з БД
            return db_obj
        except Exception as e: # TODO: Обробляти конкретні помилки БД (наприклад, IntegrityError)
            # logger.error(f"Помилка створення {self._model.__name__}: {e}")
            await db.rollback() # Відкочуємо транзакцію при помилці
            raise DatabaseErrorException(f"Помилка створення {self._model.__name__} в БД.")

    async def update(
        self, db: AsyncSession, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Оновлює існуючий запис."""
        try:
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                # Pydantic v2: exclude_unset=True - оновлюємо лише передані поля
                update_data = obj_in.model_dump(exclude_unset=True)

            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)

            db.add(db_obj) # Додаємо об'єкт до сесії (якщо він був від'єднаний або для відстеження змін)
            await db.flush()
            await db.refresh(db_obj)
            return db_obj
        except Exception as e:
            # logger.error(f"Помилка оновлення {self._model.__name__} (ID: {db_obj.id}): {e}")
            await db.rollback()
            raise DatabaseErrorException(f"Помилка оновлення {self._model.__name__} в БД.")

    async def delete(self, db: AsyncSession, *, item_id: uuid.UUID) -> Optional[ModelType]:
        """Видаляє запис за ID."""
        try:
            obj = await self.get_by_id(db, item_id)
            if obj:
                await db.delete(obj)
                await db.flush()
                return obj
            return None # Або кидати NotFoundException, якщо об'єкт не знайдено
        except Exception as e:
            # logger.error(f"Помилка видалення {self._model.__name__} (ID: {item_id}): {e}")
            await db.rollback()
            raise DatabaseErrorException(f"Помилка видалення {self._model.__name__} з БД.")

    # TODO: Додати метод для "м'якого" видалення, якщо модель підтримує (має is_deleted, deleted_at).
    # async def soft_delete(self, db: AsyncSession, *, item_id: uuid.UUID) -> Optional[ModelType]:
    #     obj = await self.get_by_id(db, item_id)
    #     if obj:
    #         if hasattr(obj, 'is_deleted') and hasattr(obj, 'deleted_at'):
    #             obj.is_deleted = True
    #             obj.deleted_at = datetime.utcnow() # Або func.now()
    #             db.add(obj)
    #             await db.flush()
    #             await db.refresh(obj)
    #             return obj
    #         else:
    #             # Модель не підтримує м'яке видалення
    async def soft_delete(self, db: AsyncSession, *, item_id: uuid.UUID, current_user_id: Optional[uuid.UUID] = None) -> Optional[ModelType]:
        """
        Виконує "м'яке" видалення запису за ID.
        Встановлює is_deleted = True та deleted_at = current_time.
        Також встановлює updated_by_user_id, якщо передано.
        """
        obj = await self.get_by_id(db, item_id)
        if obj:
            if not hasattr(obj, 'is_deleted') or not hasattr(obj, 'deleted_at'):
                raise NotImplementedError(f"Модель {self._model.__name__} не підтримує 'м'яке' видалення (відсутні поля is_deleted/deleted_at).")

            obj.is_deleted = True # type: ignore
            obj.deleted_at = datetime.utcnow().replace(tzinfo=timezone.utc) # type: ignore

            if current_user_id and hasattr(obj, 'updated_by_user_id'):
                obj.updated_by_user_id = current_user_id # type: ignore
            elif hasattr(obj, 'updated_by_user_id'): # Якщо поле є, але юзер не переданий, можна встановити None або не чіпати
                obj.updated_by_user_id = None # type: ignore

            # updated_at оновиться автоматично через onupdate=func.now() в BaseModel

            db.add(obj)
            await db.flush()
            await db.refresh(obj)
            return obj
        return None


# --- Базовий клас для сервісів ---
class BaseService:
    """
    Базовий клас для сервісів.
    Сервіси інкапсулюють бізнес-логіку та взаємодіють з репозиторіями.
    """
    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізатор сервісу.
        :param db_session: Асинхронна сесія SQLAlchemy.
        """
        self.db_session = db_session
        # Тут також можуть ініціалізуватися репозиторії, якщо сервіс їх використовує.
        # Наприклад, якщо сервіс завжди працює з певним репозиторієм:
        # self.repository = self._get_repository() # Приватний метод, що повертає екземпляр репозиторію

    # def _get_repository(self) -> BaseRepository:
    #     # Цей метод має бути перевизначений у класах-наслідниках,
    #     # щоб повертати конкретний екземпляр репозиторію.
    #     raise NotImplementedError("Метод _get_repository має бути реалізований у класі-насліднику сервісу.")

    # Сервіси будуть мати методи, що реалізують конкретні бізнес-операції.
    # Вони можуть використовувати один або декілька репозиторіїв.
    # Приклад:
    # async def get_item_by_id_as_schema(self, item_id: uuid.UUID, schema: Type[SchemaType]) -> Optional[SchemaType]:
    #     item_orm = await self.repository.get_by_id(self.db_session, item_id)
    #     if item_orm:
    #         return schema.model_validate(item_orm)
    #     return None

    async def _commit_session(self):
        """Допоміжний метод для коміту поточної сесії."""
        try:
            await self.db_session.commit()
        except Exception as e:
            await self.db_session.rollback()
            # logger.error(f"Помилка під час коміту сесії: {e}", exc_info=True)
            raise DatabaseErrorException(f"Помилка під час коміту сесії: {e}")

    # TODO: Визначити, чи потрібні тут якісь спільні методи для всіх сервісів.
    # Наприклад, _commit_session може бути корисним.
    # Або декоратор @manage_transaction для методів сервісу.
    pass


# TODO: Переконатися, що `BaseRepository` коректно працює з асинхронними операціями
# та SQLAlchemy 2.0. Використання `await db.execute(...)`, `result.scalar_one_or_none()`,
# `result.scalars().all()` є правильним для асинхронного ORM.
# `db.add()`, `db.flush()`, `db.refresh()`, `db.delete()` також мають асинхронні аналоги
# або працюють в асинхронному контексті. `flush` та `refresh` важливі для отримання
# актуальних даних з БД після створення/оновлення.
#
# `BaseRepository.create` та `BaseRepository.update` використовують `obj_in.model_dump()`
# для отримання словника з Pydantic схеми, що є правильним для Pydantic v2.
# `exclude_unset=True` в `update` важливо для часткових оновлень (PATCH).
#
# Логіка фільтрації та сортування в `get_multi` та `get_count` є базовою
# і може потребувати розширення для складніших запитів (наприклад, JOIN, підзапити).
#
# `BaseService` поки що є простою заглушкою. Його наповнення залежатиме від
# потреб конкретних сервісів.
#
# Цей файл `base.py` в `core` відповідає структурі `structure-claude-v3.md`.
#
# Все виглядає як хороший початок для базових класів репозиторіїв та сервісів.
# `DatabaseErrorException` використовується для обгортання помилок БД.
# `NotFoundException` може кидатися, якщо об'єкт не знайдено (хоча `get_by_id` повертає `Optional`).
#
# `literal_column("*")` в `get_count` - це спосіб отримати `COUNT(*)` в SQLAlchemy.
# `select_from(self._model)` потрібен, якщо `select()` не має звідки вибирати (як у випадку з `func.count`).
#
# Все готово.
