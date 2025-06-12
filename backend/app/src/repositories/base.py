# -*- coding: utf-8 -*-
# backend/app/src/repositories/base.py
"""
Базовий репозиторій (`BaseRepository`).

Цей модуль визначає узагальнений (Generic) клас `BaseRepository`, який надає
стандартний набір CRUD (Create, Read, Update, Delete) операцій та деякі
додаткові методи для взаємодії з базою даних через SQLAlchemy.
Він призначений для успадкування конкретними репозиторіями, які працюють
з певними моделями даних.

Клас параметризований трьома типами:
- `ModelType`: Тип моделі SQLAlchemy (успадкований від `SQLAlchemyBaseModel`).
- `CreateSchemaType`: Тип схеми Pydantic для створення записів (успадкований від `PydanticBaseModel`).
- `UpdateSchemaType`: Тип схеми Pydantic для оновлення записів (успадкований від `PydanticBaseModel`).

Основні методи:
- `get`: Отримання одного запису за ідентифікатором.
- `get_multi`: Отримання списку записів з можливістю фільтрації, сортування та пагінації.
- `create`: Створення нового запису.
- `update`: Оновлення існуючого запису.
- `remove`: Видалення запису (жорстке видалення).
- `count`: Підрахунок кількості записів з можливістю фільтрації.

Використовує асинхронні операції SQLAlchemy 2.0 та централізований логер.
"""

from typing import Type, TypeVar, Generic, Optional, List, Any, Dict
from uuid import UUID # Хоча UUID не використовується прямо тут, він може бути ID

from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy import select, update as sqlalchemy_update, delete as sqlalchemy_delete, func, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
# Для TypeVar bound, ми посилаємося на метаклас, який мають усі моделі SQLAlchemy
from sqlalchemy.orm import DeclarativeMeta as SQLAlchemyModelDeclarativeMeta

from backend.app.src.config import logger

# Визначення узагальнених типів для моделей та схем
# ModelType прив'язаний до метакласу SQLAlchemy моделей. Це означає, що ModelType
# буде типом класу моделі (наприклад, User), а не екземпляром моделі.
ModelType = TypeVar("ModelType", bound=SQLAlchemyModelDeclarativeMeta)
CreateSchemaType = TypeVar("CreateSchemaType", bound=PydanticBaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=PydanticBaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Узагальнений базовий репозиторій для CRUD операцій.
    """

    def __init__(self, model: Type[ModelType]):
        """
        Ініціалізація репозиторію.

        :param model: Клас моделі SQLAlchemy, з якою працюватиме репозиторій.
                      `Type[ModelType]` означає, що `model` є самим класом, а не екземпляром.
        """
        self.model: Type[ModelType] = model
        logger.debug(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get(self, session: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        Отримує один запис за його ідентифікатором.

        :param session: Асинхронна сесія SQLAlchemy.
        :param id: Ідентифікатор запису (може бути UUID, int тощо).
        :return: Об'єкт моделі або None, якщо запис не знайдено.
        """
        logger.debug(f"Отримання запису типу '{self.model.__name__}' за ID: {id}")
        # Оскільки self.model - це клас, доступ до атрибутів (наприклад, self.model.id) є коректним.
        stmt = select(self.model).where(self.model.id == id)
        try:
            result = await session.execute(stmt)
            return result.scalar_one_or_none() # Повертає екземпляр ModelType або None
        except Exception as e:
            logger.error(f"Помилка при отриманні запису '{self.model.__name__}' за ID {id}: {e}", exc_info=True)
            # Розглянути можливість підняття специфічного виключення або повернення None
            # залежно від стратегії обробки помилок. Наразі повертаємо None.
            return None


    async def get_multi(
        self,
        session: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc"
    ) -> List[ModelType]: # Повертає список екземплярів ModelType
        """
        Отримує список записів з можливістю фільтрації, сортування та пагінації.

        :param session: Асинхронна сесія SQLAlchemy.
        :param skip: Кількість записів, які потрібно пропустити (для пагінації).
        :param limit: Максимальна кількість записів для повернення (для пагінації).
        :param filters: Словник фільтрів, де ключ - назва поля, значення - значення для фільтрації.
                        Підтримуються оператори '__gt', '__lt', '__gte', '__lte', '__ne', '__in', '__like'.
        :param sort_by: Поле, за яким потрібно сортувати.
        :param sort_order: Напрямок сортування ("asc" або "desc").
        :return: Список об'єктів моделі.
        """
        logger.debug(
            f"Отримання списку записів типу '{self.model.__name__}' з параметрами: "
            f"skip={skip}, limit={limit}, filters={filters}, sort_by={sort_by}, sort_order={sort_order}"
        )
        stmt = select(self.model)

        if filters:
            for field, value in filters.items():
                # Поле може містити оператор, наприклад, "age__gt"
                field_name = field.split("__")[0]
                column = getattr(self.model, field_name, None)
                if column:
                    if "__gt" in field:
                        stmt = stmt.where(column > value)
                    elif "__lt" in field:
                        stmt = stmt.where(column < value)
                    elif "__gte" in field:
                        stmt = stmt.where(column >= value)
                    elif "__lte" in field:
                        stmt = stmt.where(column <= value)
                    elif "__ne" in field:
                        stmt = stmt.where(column != value)
                    elif "__in" in field: # value має бути списком або кортежем
                        stmt = stmt.where(column.in_(value))
                    elif "__like" in field: # value має бути рядком
                        stmt = stmt.where(column.ilike(f"%{value}%")) # ilike для нечутливого до регістру пошуку
                    else: # Точне співпадіння
                        stmt = stmt.where(column == value)
                else:
                    logger.warning(f"Поле '{field_name}' для фільтрації не знайдено в моделі '{self.model.__name__}'.")


        if sort_by:
            column_to_sort = getattr(self.model, sort_by, None)
            if column_to_sort:
                if sort_order.lower() == "desc":
                    stmt = stmt.order_by(desc(column_to_sort))
                else:
                    stmt = stmt.order_by(asc(column_to_sort))
            else:
                logger.warning(f"Поле '{sort_by}' для сортування не знайдено в моделі '{self.model.__name__}'.")

        stmt = stmt.offset(skip).limit(limit)

        try:
            result = await session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Помилка при отриманні списку записів '{self.model.__name__}': {e}", exc_info=True)
            return []

    async def create(self, session: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType: # Повертає екземпляр ModelType
        """
        Створює новий запис у базі даних.

        :param session: Асинхронна сесія SQLAlchemy.
        :param obj_in: Об'єкт схеми Pydantic з даними для створення.
        :return: Створений об'єкт моделі.
        """
        logger.debug(f"Створення нового запису типу '{self.model.__name__}' з даними: {obj_in}")
        # `self.model` - це клас моделі, `**obj_in.model_dump()` розпаковує дані зі схеми
        # для конструктора моделі. Це створює екземпляр ModelType.
        db_obj = self.model(**obj_in.model_dump())

        try:
            # Використовуємо `begin_nested` якщо транзакція вже активна (наприклад, з сервісного рівня),
            # інакше починаємо нову транзакцію.
            async with session.begin_nested() if session.in_transaction() else session.begin():
                session.add(db_obj)
                # flush потрібен, щоб отримати ID (якщо він генерується базою даних, наприклад, SERIAL)
                # або для перевірки обмежень (constraints) до фактичного commit.
                await session.flush()
                # refresh оновлює `db_obj` даними з бази даних (наприклад, default значеннями, тригерами).
                await session.refresh(db_obj)
            # `commit` відбувається автоматично при виході з блоку `async with`, якщо не було помилок.
            # `rollback` відбувається автоматично, якщо всередині блоку виникло виключення.
            logger.info(f"Запис типу '{self.model.__name__}' з ID {getattr(db_obj, 'id', 'N/A')} успішно створено.")
            return db_obj
        except Exception as e:
            logger.error(f"Помилка при створенні запису '{self.model.__name__}': {e}", exc_info=True)
            # TODO: Підняти специфічне виключення програми (наприклад, DatabaseCreateError)
            raise

    async def update(
        self,
        session: AsyncSession,
        *,
        db_obj: ModelType, # `db_obj` є екземпляром ModelType
        obj_in: UpdateSchemaType | Dict[str, Any]
    ) -> ModelType: # Повертає екземпляр ModelType
        """
        Оновлює існуючий запис у базі даних.

        :param session: Асинхронна сесія SQLAlchemy.
        :param db_obj: Об'єкт моделі (екземпляр), який потрібно оновити.
        :param obj_in: Об'єкт схеми Pydantic або словник з даними для оновлення.
                       Використовується `exclude_unset=True` для Pydantic схем,
                       щоб оновлювати тільки передані поля.
        :return: Оновлений об'єкт моделі.
        """
        logger.debug(f"Оновлення запису типу '{self.model.__name__}' з ID {getattr(db_obj, 'id', 'N/A')}")
        if isinstance(obj_in, PydanticBaseModel):
            # `exclude_unset=True` важливо, щоб не перезаписувати поля значеннями None,
            # якщо вони не були явно передані в схемі оновлення.
            update_data = obj_in.model_dump(exclude_unset=True)
        else:
            update_data = obj_in # Якщо це словник, використовуємо його як є.

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
            else:
                logger.warning(
                    f"Спроба оновити неіснуюче поле '{field}' для моделі '{self.model.__name__}'."
                )

        try:
            async with session.begin_nested() if session.in_transaction() else session.begin():
                session.add(db_obj) # Додає об'єкт до сесії, якщо він ще не там, або відмічає його як "dirty"
                await session.flush()
                await session.refresh(db_obj)
            logger.info(f"Запис типу '{self.model.__name__}' з ID {getattr(db_obj, 'id', 'N/A')} успішно оновлено.")
            return db_obj
        except Exception as e:
            logger.error(
                f"Помилка при оновленні запису '{self.model.__name__}' з ID {getattr(db_obj, 'id', 'N/A')}: {e}",
                exc_info=True
            )
            # TODO: Підняти специфічне виключення програми (наприклад, DatabaseUpdateError)
            raise

    async def remove(self, session: AsyncSession, *, id: Any) -> Optional[ModelType]: # Повертає екземпляр ModelType або None
        """
        Видаляє запис із бази даних (жорстке видалення).

        :param session: Асинхронна сесія SQLAlchemy.
        :param id: Ідентифікатор запису, який потрібно видалити.
        :return: Видалений об'єкт моделі або None, якщо запис не знайдено.
        """
        logger.debug(f"Видалення запису типу '{self.model.__name__}' за ID: {id}")
        # TODO: Розглянути можливість перевірки наявності `is_deleted` атрибуту
        #       і виконання м'якого видалення, якщо це передбачено моделлю.
        #       Для цього може знадобитися передавати `db_obj` замість `id` або мати окремий метод.

        try:
            async with session.begin_nested() if session.in_transaction() else session.begin():
                # Спочатку отримуємо об'єкт, щоб повернути його після видалення (якщо потрібно)
                # і щоб переконатися, що він існує.
                # `self.get` використовує ту саму сесію, але не починає нову транзакцію, якщо вже є.
                obj_to_delete = await self.get(session, id)
                if obj_to_delete:
                    await session.delete(obj_to_delete)
                    # `flush` тут не обов'язковий, оскільки `commit` (через with-блок) все зробить.
                    # await session.flush()
                    logger.info(f"Запис типу '{self.model.__name__}' з ID {id} успішно видалено (жорстке видалення).")
                    return obj_to_delete
                else:
                    logger.warning(f"Запис типу '{self.model.__name__}' з ID {id} не знайдено для видалення.")
                    return None
        except Exception as e:
            logger.error(f"Помилка при видаленні запису '{self.model.__name__}' з ID {id}: {e}", exc_info=True)
            # TODO: Підняти специфічне виключення програми (наприклад, DatabaseDeleteError)
            raise


    async def count(
        self,
        session: AsyncSession,
        *,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Підраховує кількість записів, що відповідають заданим фільтрам.

        :param session: Асинхронна сесія SQLAlchemy.
        :param filters: Словник фільтрів (аналогічно до get_multi).
        :return: Кількість записів.
        """
        logger.debug(f"Підрахунок записів типу '{self.model.__name__}' з фільтрами: {filters}")
        # Використовуємо `func.count(self.model.id)` для підрахунку за первинним ключем,
        # що зазвичай є ефективним.
        stmt = select(func.count(self.model.id)).select_from(self.model)

        if filters: # Логіка фільтрації аналогічна до get_multi
            for field, value in filters.items():
                field_name = field.split("__")[0]
                column = getattr(self.model, field_name, None)
                if column:
                    if "__gt" in field:
                        stmt = stmt.where(column > value)
                    elif "__lt" in field:
                        stmt = stmt.where(column < value)
                    elif "__gte" in field:
                        stmt = stmt.where(column >= value)
                    elif "__lte" in field:
                        stmt = stmt.where(column <= value)
                    elif "__ne" in field:
                        stmt = stmt.where(column != value)
                    elif "__in" in field:
                        stmt = stmt.where(column.in_(value))
                    elif "__like" in field:
                        stmt = stmt.where(column.ilike(f"%{value}%"))
                    else:
                        stmt = stmt.where(column == value)
                else:
                    logger.warning(f"Поле '{field_name}' для фільтрації (count) не знайдено в моделі '{self.model.__name__}'.")
        try:
            result = await session.execute(stmt)
            count_value = result.scalar_one() # `scalar_one` очікує один рядок, одне значення.
            logger.debug(f"Загальна кількість записів типу '{self.model.__name__}': {count_value}")
            return count_value
        except Exception as e:
            logger.error(f"Помилка при підрахунку записів '{self.model.__name__}': {e}", exc_info=True)
            # TODO: Повернути 0 чи підняти виключення? Наразі 0 для уникнення падіння.
            return 0

    # --- TODOs та Замітки для подальшого покращення ---

    # TODO: [Error Handling] Замість загального `except Exception`, ловити більш специфічні помилки
    #       SQLAlchemy (наприклад, `IntegrityError` від `sqlalchemy.exc`) та відповідно реагувати
    #       або піднімати кастомні виключення програми (наприклад, `DuplicateEntryError`, `DataTooLongError`).

    # TODO: [Filtering] Розширити можливості фільтрації:
    #       - Підтримка OR умов (наприклад, через спеціальний синтаксис у `filters` або окремий параметр).
    #       - Фільтрація за полями пов'язаних моделей (потребуватиме `join` або `selectinload` і потім фільтрацію в Python,
    #         або більш складні конструкції `where` з `Relationship.Comparator.any()` або `has()`).
    #         Приклад: `filters={"user__name__like": "John"}`.

    # TODO: [Sorting] Дозволити сортування за кількома полями.
    #       Наприклад, `sort_by: Optional[Union[str, List[Tuple[str, str]]]]`,
    #       де `List[Tuple[str, str]]` містить пари (назва_поля, напрямок_сортування).

    # TODO: [Soft Delete] Реалізувати або інтегрувати механізм м'якого видалення.
    #       Якщо модель має атрибути типу `is_deleted` та `deleted_at`, метод `remove`
    #       міг би автоматично виконувати м'яке видалення. Або додати окремий метод `soft_remove`.
    #       Можливо, додати параметр `hard_delete: bool = False` до методу `remove`.

    # TODO: [Bulk Operations] Розглянути додавання методів для пакетного створення (`bulk_create`),
    #       оновлення (`bulk_update`), та видалення (`bulk_delete`), якщо це часто потрібно.
    #       Це може бути значно ефективніше для великої кількості записів.
    #       Наприклад: `async def bulk_create(self, session: AsyncSession, *, objs_in: List[CreateSchemaType]) -> List[ModelType]: ...`

    # TODO: [Type Hinting for ModelType] Поточне `ModelType = TypeVar("ModelType", bound=SQLAlchemyModelDeclarativeMeta)`
    #       є коректним для передачі *класу* моделі. Екземпляри моделі будуть типу `ModelType`.
    #       Переконатися, що це узгоджується зі статичним аналізатором (mypy).
    #       `SQLAlchemyModelDeclarativeMeta` - це метаклас `declarative_base()`.
    #       Альтернативою для SQLAlchemy 2.0+ могло б бути використання `TypeVar("ModelType", bound=DeclarativeBase)`
    #       якщо всі моделі успадковуються від спільного `DeclarativeBase`.
    #       Або `TypeVar("ModelType", bound=Any)` якщо не вдається знайти спільний базовий тип,
    #       але це менш безпечно з точки зору типів. Поточний варіант є прийнятним.

    # TODO: [Pydantic V1/V2] Код використовує `model_dump()` та `model_dump(exclude_unset=True)`,
    #       що є синтаксисом Pydantic V2. Якщо проект може використовувати Pydantic V1,
    #       потрібна буде сумісність (наприклад, через `obj_in.dict()`).

    # TODO: [Specific Getters] Можливо, додати типові специфічні гетери, якщо вони часто потрібні,
    #       наприклад, `get_by_field(session: AsyncSession, field_name: str, field_value: Any) -> Optional[ModelType]: ...`
    #       або `get_all_by_ids(session: AsyncSession, ids: List[Any]) -> List[ModelType]: ...`.

    # TODO: [Exists Check] Додати простий метод `exists(session: AsyncSession, id: Any) -> bool:`
    #       який був би оптимізований для перевірки існування (не витягуючи весь об'єкт).
    #       `select(self.model.id).where(self.model.id == id)` і перевірка `scalar_one_or_none() is not None`.

    # TODO: [Logging Context] Для кращого відстеження, можна додати більше контексту до логів,
    #       наприклад, ім'я користувача або ID запиту, якщо вони доступні.
    #       Це зазвичай робиться через middleware та передачу контексту.

pass # Кінець класу BaseRepository

# Кінець файлу backend/app/src/repositories/base.py
