# backend/app/src/repositories/base.py
"""
Базовий репозиторій для CRUD операцій з моделями SQLAlchemy.

Цей модуль визначає узагальнений клас `BaseRepository`, який надає
стандартні методи для створення, читання, оновлення та видалення (CRUD)
записів у базі даних за допомогою SQLAlchemy. Він призначений для успадкування
конкретними репозиторіями, що працюють зі специфічними моделями.
"""

from typing import List, Optional, Type, Any, Tuple, Dict, Union, Generic
from datetime import datetime  # Потрібно для soft_delete, якщо встановлювати datetime.now(timezone.utc)

from sqlalchemy import select, func, update as sqlalchemy_update, delete as sqlalchemy_delete, Column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.decl_api import DeclarativeMeta  # Для перевірки типу моделі або атрибутів
from pydantic import BaseModel  # Для перевірки типу схеми в update

# Абсолютний імпорт TypeVars з core.base
from backend.app.src.core.base import ModelType, CreateSchemaType, UpdateSchemaType
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

# from backend.app.src.config.logging import get_logger # Якщо потрібне логування

# logger = get_logger(__name__)

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Узагальнений базовий клас репозиторію для CRUD операцій.

    Параметризується типами моделі SQLAlchemy (`ModelType`), схеми створення (`CreateSchemaType`)
    та схеми оновлення (`UpdateSchemaType`).

    Атрибути:
        model (Type[ModelType]): Клас моделі SQLAlchemy, з якою працює репозиторій.
        db_session (AsyncSession): Асинхронна сесія SQLAlchemy для взаємодії з БД.
    """

    def __init__(self, db_session: AsyncSession, model: Type[ModelType]):
        """
        Ініціалізує репозиторій з сесією БД та моделлю.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
            model (Type[ModelType]): Клас моделі SQLAlchemy.
        """
        self.db_session = db_session
        self.model = model

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """
        Створює новий запис у базі даних.

        Args:
            obj_in (CreateSchemaType): Pydantic схема з даними для створення.

        Returns:
            ModelType: Створений екземпляр моделі SQLAlchemy.
        """
        # Створюємо екземпляр моделі з даних схеми
        # Pydantic v2 model_dump() повертає dict
        db_obj = self.model(**obj_in.model_dump())
        self.db_session.add(db_obj)
        await self.db_session.commit()
        await self.db_session.refresh(db_obj)
        # logger.info(f"Створено запис: {db_obj}")
        return db_obj

    async def get(self, record_id: Any) -> Optional[ModelType]:
        """
        Отримує один запис за його первинним ключем (зазвичай 'id').

        Args:
            record_id (Any): Значення первинного ключа для пошуку.

        Returns:
            Optional[ModelType]: Екземпляр моделі, якщо знайдено, інакше None.
        """
        # Припускаємо, що первинний ключ називається 'id'
        stmt = select(self.model).where(self.model.id == record_id)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(
            self,
            *,
            skip: int = 0,
            limit: int = 100,
            filters: Optional[List[Any]] = None,  # Список фільтрів SQLAlchemy (наприклад, [User.is_active == True])
            order_by: Optional[List[Any]] = None  # Список полів для сортування (наприклад, [User.email.asc()])
    ) -> Tuple[List[ModelType], int]:
        """
        Отримує список записів з пагінацією, фільтрацією та сортуванням.

        Args:
            skip (int): Кількість записів, яку потрібно пропустити (для пагінації).
            limit (int): Максимальна кількість записів для повернення.
            filters (Optional[List[Any]]): Список виразів фільтрації SQLAlchemy.
            order_by (Optional[List[Any]]): Список виразів сортування SQLAlchemy.

        Returns:
            Tuple[List[ModelType], int]: Кортеж зі списком знайдених записів та їх загальною кількістю (до пагінації).
        """
        count_stmt = select(func.count()).select_from(self.model)
        stmt = select(self.model)

        if filters is not None and len(filters) > 0:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        total = (await self.db_session.execute(count_stmt)).scalar_one()

        if order_by is not None and len(order_by) > 0:
            stmt = stmt.order_by(*order_by)

        stmt = stmt.offset(skip).limit(limit)

        items_result = await self.db_session.execute(stmt)
        items = list(items_result.scalars().all())  # Перетворюємо результат на список

        return items, total

    async def update(
            self,
            *,
            db_obj: ModelType,  # Екземпляр моделі SQLAlchemy для оновлення
            obj_in: Union[UpdateSchemaType, Dict[str, Any]]  # Дані для оновлення (схема Pydantic або dict)
    ) -> ModelType:
        """
        Оновлює існуючий запис у базі даних.

        Args:
            db_obj (ModelType): Екземпляр моделі SQLAlchemy, який потрібно оновити.
            obj_in (Union[UpdateSchemaType, Dict[str, Any]]): Pydantic схема або словник
                                                              з даними для оновлення.

        Returns:
            ModelType: Оновлений екземпляр моделі SQLAlchemy.
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:  # Pydantic модель
            update_data = obj_in.model_dump(exclude_unset=True)  # exclude_unset=True для часткових оновлень (PATCH)

        for field, value in update_data.items():
            if hasattr(db_obj, field):  # Перевіряємо, чи існує такий атрибут у моделі
                setattr(db_obj, field, value)
            # else:
            # logger.warning(f"Спроба оновити неіснуюче поле '{field}' для моделі {self.model.__name__}")

        self.db_session.add(db_obj)
        await self.db_session.commit()
        await self.db_session.refresh(db_obj)
        # logger.info(f"Оновлено запис: {db_obj}")
        return db_obj

    async def delete(self, record_id: Any) -> Optional[ModelType]:
        """
        Видаляє запис із бази даних за його первинним ключем.
        Це "жорстке" видалення.

        Args:
            record_id (Any): Значення первинного ключа запису для видалення.

        Returns:
            Optional[ModelType]: Видалений екземпляр моделі, або None, якщо запис не знайдено.
        """
        db_obj = await self.get(record_id)
        if db_obj is None:
            # logger.warning(f"Спроба видалити неіснуючий запис ID {record_id} з {self.model.__name__}")
            return None

        await self.db_session.delete(db_obj)
        await self.db_session.commit()
        # logger.info(f"Видалено запис: {db_obj}")
        return db_obj

    async def soft_delete(self, db_obj: ModelType) -> Optional[ModelType]:
        """
        Виконує "м'яке" видалення запису, встановлюючи поле `deleted_at`.
        Потребує наявності поля `deleted_at` у моделі (зазвичай через `SoftDeleteMixin`).

        Args:
            db_obj (ModelType): Екземпляр моделі SQLAlchemy для м'якого видалення.

        Returns:
            Optional[ModelType]: Екземпляр моделі з встановленим `deleted_at`, або None, якщо операція неможлива.

        Raises:
            NotImplementedError: Якщо модель не підтримує м'яке видалення (немає поля `deleted_at`).
        """
        if not hasattr(db_obj, "deleted_at"):
            # logger.error(f"Модель {self.model.__name__} не підтримує м'яке видалення (відсутнє поле 'deleted_at').")
            raise NotImplementedError(f"Модель {self.model.__name__} не підтримує м'яке видалення.")

        # Встановлюємо поточний час UTC для deleted_at
        # Використання func.now() тут може бути проблематичним, оскільки це серверне значення БД,
        # а ми хочемо оновити поле Python об'єкта перед комітом.
        # Краще використовувати datetime.now(timezone.utc)
        from datetime import timezone  # Локальний імпорт, щоб уникнути циклічності, якщо utils імпортує щось звідси
        setattr(db_obj, "deleted_at", datetime.now(timezone.utc))

        self.db_session.add(db_obj)
        await self.db_session.commit()
        await self.db_session.refresh(db_obj)
        # logger.info(f"М'яко видалено запис: {db_obj}")
        return db_obj

    async def count(self, filters: Optional[List[Any]] = None) -> int:
        """
        Підраховує кількість записів, що відповідають заданим фільтрам.

        Args:
            filters (Optional[List[Any]]): Список виразів фільтрації SQLAlchemy.

        Returns:
            int: Загальна кількість знайдених записів.
        """
        stmt = select(func.count(self.model.id if hasattr(self.model, 'id') else '*')).select_from(
            self.model)  # Рахуємо по id, якщо є
        if filters is not None and len(filters) > 0:
            stmt = stmt.where(*filters)

        total = (await self.db_session.execute(stmt)).scalar_one()
        return total


# Блок для демонстрації та базового тестування (потребує значних макетів)
if __name__ == "__main__":
    # Цей блок потребує значної кількості макетів для SQLAlchemy AsyncSession, моделей та схем,
    # тому повноцінне тестування тут складне. Краще тестувати через інтеграційні тести.
    # Нижче наведено дуже спрощену концептуальну демонстрацію.

    logger.info("--- Демонстрація Базового Репозиторію (BaseRepository) ---")


    # 1. Визначення фіктивних моделей та схем для тестування
    class MockSQLAlchemyModel(DeclarativeMeta):  # Не зовсім коректно, але для імітації
        __tablename__ = "mock_items"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str]
        value: Mapped[Optional[int]]

        # Імітація колонок для __repr__ та update
        __table__ = type('Table', (), {
            'columns': [Column('id', Integer, primary_key=True), Column('name', String), Column('value', Integer)]})()

        def __init__(self, **kwargs):  # Простий init для приймання kwargs
            for k, v in kwargs.items():
                setattr(self, k, v)

        def __repr__(self):
            return f"<MockSQLAlchemyModel(id={self.id}, name='{self.name}', value={self.value})>"


    class MockCreateSchema(BaseModel):
        name: str
        value: Optional[int] = None


    class MockUpdateSchema(BaseModel):
        name: Optional[str] = None
        value: Optional[int] = None


    # 2. Макет AsyncSession (дуже спрощений)
    class MockAsyncSession:
        def __init__(self):
            self._store: Dict[int, MockSQLAlchemyModel] = {}
            self._next_id = 1
            self.flushed_objects = []  # Для імітації add/delete/commit

        async def add(self, obj):
            # logger.debug(f"MockSession: Додавання об'єкта {obj}")
            if not hasattr(obj, 'id') or obj.id is None:  # Імітація автоінкремента
                obj.id = self._next_id
                self._next_id += 1
            self._store[obj.id] = obj
            self.flushed_objects.append(obj)

        async def commit(self):
            # logger.debug(f"MockSession: Коміт {len(self.flushed_objects)} об'єктів.")
            # Тут можна було б імітувати реальний запис, але для refresh достатньо очистити список
            self.flushed_objects = []
            pass

        async def refresh(self, obj):
            # logger.debug(f"MockSession: Оновлення об'єкта {obj}")
            # В реальності це завантажує стан з БД. Тут просто передаємо далі.
            pass

        async def delete(self, obj):
            # logger.debug(f"MockSession: Видалення об'єкта {obj}")
            if obj.id in self._store:
                del self._store[obj.id]
            self.flushed_objects.append(obj)  # Для імітації, хоча об'єкт вже видалено

        async def execute(self, stmt):
            # Дуже спрощена імітація execute для get, get_multi, count
            # logger.debug(f"MockSession: Виконання запиту {stmt}")
            # Це потребує парсингу stmt, що виходить за рамки простого макета.
            # Для get:
            if hasattr(stmt, 'whereclause') and stmt.whereclause is not None:
                # Імітуємо пошук по id для get
                # Це дуже грубе припущення про структуру stmt.whereclause
                # У реальному тесті використовуйте тестову БД або більш складний макет SQLAlchemy.
                try:
                    # Приклад для stmt = select(self.model).where(self.model.id == record_id)
                    # whereclause.right.value буде record_id
                    target_id = stmt.whereclause.right.value
                    found_obj = self._store.get(target_id)

                    class MockScalarResult:
                        def __init__(self, value): self._value = value

                        def scalar_one_or_none(self): return self._value

                        def scalar_one(self): return self._value if self._value is not None else (_ for _ in ()).throw(
                            Exception("No row was found for one()"))  # Імітація помилки

                        def scalars(self): return self  # Для .scalars().all()

                        def all(self): return [self._value] if self._value else []

                    return MockScalarResult(found_obj)
                except Exception:  # Якщо структура stmt інша
                    pass

            # Для get_multi (items) та count
            # Повернемо всі об'єкти для get_multi, якщо немає фільтрів
            # або порожній список / 0 для count, якщоstmt не для get(id)

            # Імітація для select(func.count())
            if any(isinstance(col, func.count) for col in stmt.selected_columns):
                class MockScalarCountResult:
                    def __init__(self, count_val): self._count_val = count_val

                    def scalar_one(self): return self._count_val

                return MockScalarCountResult(len(self._store))

            # Імітація для select(model)
            class MockScalarAllResult:
                def __init__(self, items_list): self._items_list = items_list

                def scalars(self): return self  # Для .scalars().all()

                def all(self): return self._items_list

            # Дуже спрощено, без фільтрів та сортування
            return MockScalarAllResult(list(self._store.values()))


    async def run_repository_demo():
        logger.info("\n--- Демонстрація роботи BaseRepository з Макетами ---")
        mock_session = MockAsyncSession()
        repo = BaseRepository[MockSQLAlchemyModel, MockCreateSchema, MockUpdateSchema](
            db_session=mock_session, model=MockSQLAlchemyModel
        )

        # 1. Створення
        logger.info("1. Тест створення:")
        create_schema = MockCreateSchema(name="Тестовий Запис 1", value=100)
        created_obj = await repo.create(create_schema)
        logger.info(f"  Створено: {created_obj}")
        assert created_obj.id == 1
        assert created_obj.name == "Тестовий Запис 1"

        create_schema_2 = MockCreateSchema(name="Тестовий Запис 2", value=200)
        created_obj_2 = await repo.create(create_schema_2)
        logger.info(f"  Створено: {created_obj_2}")
        assert created_obj_2.id == 2

        # 2. Отримання одного запису
        logger.info("\n2. Тест отримання одного запису:")
        retrieved_obj = await repo.get(1)
        logger.info(f"  Отримано (ID 1): {retrieved_obj}")
        assert retrieved_obj is not None
        assert retrieved_obj.id == 1
        assert retrieved_obj.name == "Тестовий Запис 1"

        retrieved_obj_none = await repo.get(99)  # Неіснуючий ID
        logger.info(f"  Отримано (ID 99): {retrieved_obj_none}")
        assert retrieved_obj_none is None

        # 3. Отримання кількох записів (спрощено, без фільтрів/сортування в макеті)
        logger.info("\n3. Тест отримання кількох записів (спрощено):")
        items, total = await repo.get_multi(limit=10)
        logger.info(f"  Отримано {len(items)} з {total} записів.")
        assert total == 2
        assert len(items) == 2

        # 4. Оновлення
        logger.info("\n4. Тест оновлення:")
        update_schema = MockUpdateSchema(name="Оновлений Запис 1", value=150)
        if retrieved_obj:
            updated_obj = await repo.update(db_obj=retrieved_obj, obj_in=update_schema)
            logger.info(f"  Оновлено: {updated_obj}")
            assert updated_obj.name == "Оновлений Запис 1"
            assert updated_obj.value == 150

        # 5. Підрахунок
        logger.info("\n5. Тест підрахунку:")
        count = await repo.count()
        logger.info(f"  Загальна кількість записів: {count}")
        assert count == 2  # Залишилося 2 записи

        # 6. "М'яке" видалення (якщо модель підтримує)
        logger.info("\n6. Тест м'якого видалення:")
        # Наша MockSQLAlchemyModel не має поля deleted_at, тому очікуємо помилку
        if created_obj_2:
            try:
                await repo.soft_delete(db_obj=created_obj_2)
            except NotImplementedError as e:
                logger.info(f"  Очікувана помилка для soft_delete: {e}")
            except Exception as e:
                logger.error(f"  Неочікувана помилка для soft_delete: {e}")

        # Додамо поле deleted_at до MockSQLAlchemyModel для тесту
        setattr(MockSQLAlchemyModel, 'deleted_at', None)  # Імітація поля
        # Імітуємо, що колонка існує в __mapper__ для __repr__ (якщо __repr__ це перевіряє)
        MockSQLAlchemyModel.__table__.columns.append(Column('deleted_at', type_=datetime, nullable=True))

        if created_obj_2:
            # Потрібно оновити екземпляр, щоб він мав атрибут (або перезавантажити з "БД")
            created_obj_2.deleted_at = None
            soft_deleted_obj = await repo.soft_delete(db_obj=created_obj_2)
            logger.info(f"  М'яко видалено: {soft_deleted_obj}")
            assert soft_deleted_obj.deleted_at is not None
            # Перевірка, що запис все ще в "БД" (для макета)
            assert created_obj_2.id in mock_session._store

            # 7. "Жорстке" видалення
        logger.info("\n7. Тест жорсткого видалення:")
        deleted_obj = await repo.delete(1)
        logger.info(f"  Видалено (ID 1): {deleted_obj}")
        assert deleted_obj is not None
        assert deleted_obj.id == 1
        assert 1 not in mock_session._store  # Перевірка, що запис видалено з макету сховища

        retrieved_after_delete = await repo.get(1)
        logger.info(f"  Спроба отримати видалений (ID 1): {retrieved_after_delete}")
        assert retrieved_after_delete is None

        count_after_delete = await repo.count()
        logger.info(f"  Загальна кількість записів після видалення: {count_after_delete}")
        assert count_after_delete == 1  # Один м'яко видалений, один жорстко


    import asyncio

    # Для запуску демонстрації потрібен event loop.
    # У реальному застосунку FastAPI це обробляє.
    # logger = get_logger(__name__) # Переміщено наверх для використання в run_repository_demo
    # asyncio.run(run_repository_demo())
    logger.info("\nЗапуск демонстрації BaseRepository закоментовано через складність повного макетування SQLAlchemy.")
    logger.info("Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
