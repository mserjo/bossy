# backend/app/src/repositories/base.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає базовий клас `BaseRepository`, який надає
стандартні CRUD (Create, Read, Update, Delete) операції для моделей SQLAlchemy.
Всі інші специфічні репозиторії успадковуватимуть цей клас.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder # Для конвертації Pydantic моделей в dict
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy import select, delete, update, func # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.sql.expression import Executable # type: ignore # Для type hint в _apply_filters

from backend.app.src.models.base import BaseModel as SQLAlchemyBaseModel # Базова модель SQLAlchemy
from backend.app.src.schemas.base import PaginatedResponse # Схема для пагінованої відповіді

# Типові змінні для дженеріків
ModelType = TypeVar("ModelType", bound=SQLAlchemyBaseModel) # Тип моделі SQLAlchemy
CreateSchemaType = TypeVar("CreateSchemaType", bound=PydanticBaseModel) # Тип Pydantic схеми для створення
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=PydanticBaseModel) # Тип Pydantic схеми для оновлення
SchemaType = TypeVar("SchemaType", bound=PydanticBaseModel) # Загальний тип Pydantic схеми

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Базовий клас репозиторію з CRUD операціями.

    Методи:
        create: Створює новий запис в БД.
        get: Отримує один запис за ID.
        get_multi: Отримує список записів з можливістю фільтрації та сортування (без пагінації).
        get_paginated: Отримує список записів з пагінацією, фільтрацією та сортуванням.
        update: Оновлює існуючий запис в БД.
        delete: Видаляє запис з БД ("тверде" видалення).
        soft_delete: "М'яко" видаляє запис (якщо модель підтримує).
    """
    def __init__(self, model: Type[ModelType]):
        """
        Конструктор базового репозиторію.

        :param model: Клас моделі SQLAlchemy, з якою працюватиме репозиторій.
        """
        self.model = model
        # Ініціалізуємо логер для конкретного репозиторію
        from backend.app.src.config.logging import logger
        self.logger = logger.bind(repository=self.model.__name__)


    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Створює новий запис в базі даних.

        :param db: Асинхронна сесія бази даних.
        :param obj_in: Pydantic схема з даними для створення.
        :return: Створений об'єкт моделі SQLAlchemy.
        """
        from sqlalchemy.exc import IntegrityError # Імпорт для обробки помилок цілісності
        from backend.app.src.core.exceptions import ConflictException, DatabaseErrorException

        obj_in_data = jsonable_encoder(obj_in, exclude_unset=True)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        try:
            await db.commit()
            await db.refresh(db_obj)
            self.logger.info(f"Створено новий запис {self.model.__name__} з ID {db_obj.id}")
            return db_obj
        except IntegrityError as e:
            await db.rollback()
            self.logger.warning(f"Помилка цілісності при створенні {self.model.__name__}: {obj_in_data}. Деталі: {e}")
            # TODO: Потрібно аналізувати `e.orig` для визначення конкретного порушення (наприклад, unique constraint)
            # та повертати більш специфічний ConflictException або інший відповідний виняток.
            # Наприклад, якщо e.orig містить "violates unique constraint".
            # Поки що загальний ConflictException.
            raise ConflictException(detail_key="error_conflict_resource", resource_name=self.model.__name__)
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Помилка створення {self.model.__name__}: {obj_in_data}. Деталі: {e}", exc_info=True)
            raise DatabaseErrorException(f"Помилка створення {self.model.__name__} в БД.")


    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        Отримує один запис за його ідентифікатором.

        :param db: Асинхронна сесія бази даних.
        :param id: Ідентифікатор запису.
        :return: Об'єкт моделі SQLAlchemy або None, якщо запис не знайдено.
        """
        try:
            statement = select(self.model).where(self.model.id == id)
            result = await db.execute(statement)
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Помилка отримання {self.model.__name__} за ID {id}: {e}", exc_info=True)
            from backend.app.src.core.exceptions import DatabaseErrorException # Локальний імпорт
            raise DatabaseErrorException(f"Помилка отримання {self.model.__name__} з БД.")

    async def _apply_filters(self, stmt: Executable, filters: Optional[Dict[str, Any]]) -> Executable: # type: ignore
        """
        Застосовує фільтри до запиту SQLAlchemy.
        Приватний допоміжний метод.
        """
        if filters:
            for field, value in filters.items():
                if not hasattr(self.model, field):
                    self.logger.warning(f"Спроба фільтрувати за неіснуючим полем '{field}' в моделі {self.model.__name__}")
                    continue

                column_attr = getattr(self.model, field)
                if isinstance(value, list): # Оператор 'in'
                    stmt = stmt.where(column_attr.in_(value))
                elif value is None: # Оператор 'is null'
                    stmt = stmt.where(column_attr.is_(None))
                # TODO: Додати інші оператори: like, gt, lt, gte, lte, not_in, not_equal, etc.
                # Приклад для like (пошук за частиною рядка):
                # elif isinstance(value, str) and field.endswith("__icontains"): # Умовний суфікс для оператора
                #    actual_field_name = field.removesuffix("__icontains")
                #    if hasattr(self.model, actual_field_name):
                #        stmt = stmt.where(getattr(self.model, actual_field_name).ilike(f"%{value}%"))
                else: # Рівність
                    stmt = stmt.where(column_attr == value)
        return stmt

    async def _apply_order_by(self, stmt: Executable, order_by: Optional[List[str]]) -> Executable: # type: ignore
        """
        Застосовує сортування до запиту SQLAlchemy.
        Приватний допоміжний метод.
        """
        if order_by:
            for field_name_with_direction in order_by:
                direction = "asc"
                field_name = field_name_with_direction
                if field_name_with_direction.startswith("-"):
                    direction = "desc"
                    field_name = field_name_with_direction[1:]

                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    if direction == "desc":
                        stmt = stmt.order_by(field.desc())
                    else:
                        stmt = stmt.order_by(field.asc())
        return stmt

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None
    ) -> List[ModelType]:
        """
        Отримує список записів з можливістю пропуску, обмеження, фільтрації та сортування.

        :param db: Асинхронна сесія бази даних.
        :param skip: Кількість записів, яку потрібно пропустити.
        :param limit: Максимальна кількість записів для повернення.
        :param filters: Словник фільтрів (поле: значення).
        :param order_by: Список полів для сортування (наприклад, ["name", "-created_at"]).
        :return: Список об'єктів моделі SQLAlchemy.
        """
        try:
            statement = select(self.model)
            statement = await self._apply_filters(statement, filters)
            statement = await self._apply_order_by(statement, order_by)
            statement = statement.offset(skip).limit(limit)

            result = await db.execute(statement)
            return result.scalars().all() # type: ignore
        except Exception as e:
            self.logger.error(f"Помилка отримання списку {self.model.__name__}: {filters=}, {order_by=}. Деталі: {e}", exc_info=True)
            from backend.app.src.core.exceptions import DatabaseErrorException # Локальний імпорт
            raise DatabaseErrorException(f"Помилка отримання списку {self.model.__name__} з БД.")


    async def get_paginated(
        self, db: AsyncSession, *, page: int = 1, size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None
    ) -> PaginatedResponse[ModelType]:
        """
        Отримує список записів з пагінацією, фільтрацією та сортуванням.

        :param db: Асинхронна сесія бази даних.
        :param page: Номер сторінки (починаючи з 1).
        :param size: Розмір сторінки (кількість елементів).
        :param filters: Словник фільтрів.
        :param order_by: Список полів для сортування.
        :return: Об'єкт PaginatedResponse.
        """
        if page < 1: page = 1
        if size < 1: size = 1

        # Запит для отримання загальної кількості елементів (з урахуванням фільтрів)
        count_statement = select(func.count()).select_from(self.model)
        count_statement = await self._apply_filters(count_statement, filters)
        total_items_result = await db.execute(count_statement)
        total_items = total_items_result.scalar_one()

        # Розрахунок пагінації
        total_pages = (total_items + size - 1) // size if total_items > 0 else 0
        if page > total_pages and total_pages > 0: page = total_pages # Не виходити за межі
        skip = (page - 1) * size

        items: List[ModelType] = []
        if total_items > 0 : # Робимо запит на елементи, тільки якщо вони є
            # Запит для отримання елементів поточної сторінки
            items_statement = select(self.model)
            items_statement = await self._apply_filters(items_statement, filters)
            items_statement = await self._apply_order_by(items_statement, order_by)
            items_statement = items_statement.offset(skip).limit(size)

            items_result = await db.execute(items_statement)
            items = items_result.scalars().all() # type: ignore

        return PaginatedResponse(
            total=total_items,
            page=page,
            size=size,
            pages=total_pages,
            items=items
        )

    async def update(
        self, db: AsyncSession, *, db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Оновлює існуючий запис в базі даних.

        :param db: Асинхронна сесія бази даних.
        :param db_obj: Об'єкт моделі SQLAlchemy, який потрібно оновити.
        :param obj_in: Pydantic схема або словник з даними для оновлення.
        :return: Оновлений об'єкт моделі SQLAlchemy.
        """
        # Конвертуємо Pydantic схему в словник (якщо це схема)
        if isinstance(obj_in, PydanticBaseModel):
            # exclude_unset=True - оновлювати лише передані поля
            update_data = obj_in.model_dump(exclude_unset=True)
        else:
            update_data = obj_in

        # Оновлюємо атрибути об'єкта моделі
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
            else:
                self.logger.warning(f"Спроба оновити неіснуюче поле '{field}' в моделі {self.model.__name__}")

        db.add(db_obj)
        try:
            await db.commit()
            await db.refresh(db_obj)
            self.logger.info(f"Оновлено запис {self.model.__name__} з ID {db_obj.id}")
            return db_obj
        except Exception as e: # TODO: Обробляти IntegrityError та інші специфічні помилки
            await db.rollback()
            self.logger.error(f"Помилка оновлення {self.model.__name__} (ID: {db_obj.id}): {update_data}. Деталі: {e}", exc_info=True)
            from backend.app.src.core.exceptions import DatabaseErrorException # Локальний імпорт
            raise DatabaseErrorException(f"Помилка оновлення {self.model.__name__} в БД.")


    async def delete(self, db: AsyncSession, *, id: Any) -> Optional[ModelType]:
        """
        Видаляє запис з бази даних ("тверде" видалення).

        :param db: Асинхронна сесія бази даних.
        :param id: Ідентифікатор запису для видалення.
        :return: Видалений об'єкт моделі SQLAlchemy або None, якщо запис не знайдено.
        """
        db_obj = await self.get(db, id)
        if db_obj:
            try:
                await db.delete(db_obj)
                await db.commit()
                self.logger.info(f"Видалено запис {self.model.__name__} з ID {id}")
                return db_obj
            except Exception as e: # TODO: Обробляти помилки, пов'язані з ForeignKey constraints
                await db.rollback()
                self.logger.error(f"Помилка видалення {self.model.__name__} (ID: {id}): {e}", exc_info=True)
                from backend.app.src.core.exceptions import DatabaseErrorException # Локальний імпорт
                raise DatabaseErrorException(f"Помилка видалення {self.model.__name__} з БД.")
        self.logger.warning(f"Спроба видалити неіснуючий запис {self.model.__name__} з ID {id}")
        return None

    async def soft_delete(self, db: AsyncSession, *, db_obj: ModelType, current_user_id: Optional[Any] = None) -> Optional[ModelType]:
        """
        Виконує "м'яке" видалення запису, якщо модель це підтримує.
        Встановлює поля `is_deleted = True` та `deleted_at = current_time`.
        Також встановлює `updated_by_user_id`, якщо поле існує та `current_user_id` передано.

        :param db: Асинхронна сесія бази даних.
        :param db_obj: Об'єкт моделі SQLAlchemy для "м'якого" видалення.
        :param current_user_id: ID користувача, що виконує дію (для updated_by_user_id).
        :return: Оновлений об'єкт моделі або None, якщо модель не підтримує "м'яке" видалення.
        """
        if not hasattr(db_obj, "is_deleted") or not hasattr(db_obj, "deleted_at"):
            self.logger.warning(f"Модель {self.model.__name__} не підтримує 'м'яке' видалення.")
            return None

        from datetime import datetime, timezone # Імпорт для deleted_at
        setattr(db_obj, "is_deleted", True)
        setattr(db_obj, "deleted_at", datetime.now(timezone.utc)) # Використовуємо UTC

        if current_user_id and hasattr(db_obj, "updated_by_user_id"):
            setattr(db_obj, "updated_by_user_id", current_user_id)

        # updated_at має оновлюватися автоматично через onupdate=func.now() в BaseModel, якщо визначено.
        # Якщо ні, то: if hasattr(db_obj, "updated_at"): setattr(db_obj, "updated_at", datetime.now(timezone.utc))


        db.add(db_obj)
        try:
            await db.commit()
            await db.refresh(db_obj)
            self.logger.info(f"'М'яко' видалено запис {self.model.__name__} з ID {db_obj.id}")
            return db_obj
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Помилка 'м'якого' видалення {self.model.__name__} (ID: {db_obj.id}): {e}", exc_info=True)
            from backend.app.src.core.exceptions import DatabaseErrorException # Локальний імпорт
            raise DatabaseErrorException(f"Помилка 'м'якого' видалення {self.model.__name__} в БД.")


    async def restore(self, db: AsyncSession, *, db_obj: ModelType) -> Optional[ModelType]:
        """
        Відновлює "м'яко" видалений запис, якщо модель це підтримує.
        Встановлює поля `is_deleted = False` та `deleted_at = None`.

        :param db: Асинхронна сесія бази даних.
        :param db_obj: Об'єкт моделі SQLAlchemy для відновлення.
        :return: Оновлений об'єкт моделі або None.
        """
        if not hasattr(db_obj, "is_deleted") or not hasattr(db_obj, "deleted_at"):
            return None

        setattr(db_obj, "is_deleted", False)
        setattr(db_obj, "deleted_at", None)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

# TODO: Додати обробку помилок бази даних (наприклад, IntegrityError при створенні/оновленні)
#       та логування на рівні базового репозиторію або в конкретних реалізаціях.
# TODO: Для `_apply_filters` та `_apply_order_by` розглянути більш складні та гнучкі механізми
#       фільтрації (оператори like, in, gt, lt, etc.) та сортування за кількома полями.
#       Можна використовувати спеціальні схеми для фільтрів або передавати їх у структурованому вигляді.
# TODO: Переконатися, що `jsonable_encoder` використовується коректно, особливо з `exclude_unset=True`.
#       Це важливо, щоб не перезаписувати поля значеннями за замовчуванням при оновленні.
# TODO: Розглянути можливість додавання методу `count` для отримання кількості записів
#       з урахуванням фільтрів. (Частково реалізовано в `get_paginated`).
# TODO: Для методу `update`, якщо `db_obj` не передається, а передається `id`,
#       то метод має спочатку отримати `db_obj` за `id`. Поточна реалізація вимагає `db_obj`.
#       Це нормально, оскільки сервіс зазвичай спочатку отримує об'єкт, а потім оновлює.
# TODO: Типізація `Executable` з `sqlalchemy.sql.expression` може бути не зовсім точною
#       для всіх типів `statement`. Можна використовувати `Select` з `sqlalchemy.sql.selectable`.
#       Або залишити `Any` чи більш загальний тип, якщо будуть проблеми з Mypy.
#       Поки що `Executable` має працювати. (Змінено на Executable з type: ignore)
#
# Все виглядає як хороший універсальний базовий репозиторій.
# Він використовує асинхронність, дженеріки для типів та основні CRUD операції.
# Пагінація реалізована з використанням `PaginatedResponse` схеми.
# "М'яке" видалення також передбачено.
