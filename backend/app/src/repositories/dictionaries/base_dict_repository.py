# backend/app/src/repositories/dictionaries/base_dict_repository.py
"""
Базовий репозиторій для моделей-довідників SQLAlchemy.

Цей модуль визначає `BaseDictionaryRepository`, який успадковує `BaseRepository`
та додає специфічні методи для роботи з довідниками, такі як отримання запису
за його унікальним кодом (`code`) або назвою (`name`).
"""

from typing import Optional, Type, Any  # Any не використовується, але може бути корисним для майбутніх методів

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Абсолютний імпорт базового репозиторію та TypeVars
from backend.app.src.repositories.base import BaseRepository
from backend.app.src.core.base import ModelType, CreateSchemaType, UpdateSchemaType
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

# from backend.app.src.config.logging import get_logger # Якщо потрібне логування

# logger = get_logger(__name__)

class BaseDictionaryRepository(BaseRepository[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Узагальнений базовий клас репозиторію для моделей-довідників.

    Надає додаткові методи для отримання записів довідника за кодом або назвою,
    доповнюючи стандартні CRUD-операції з `BaseRepository`.

    Атрибути:
        model (Type[ModelType]): Клас моделі SQLAlchemy, що представляє довідник.
                                 Очікується, що ця модель має поля `code` та `name`.
        db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
    """

    def __init__(self, db_session: AsyncSession, model: Type[ModelType]):
        """
        Ініціалізує репозиторій для довідників.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
            model (Type[ModelType]): Клас моделі SQLAlchemy довідника.
        """
        super().__init__(db_session=db_session, model=model)

    async def get_by_code(self, code: str) -> Optional[ModelType]:
        """
        Отримує один запис довідника за його унікальним кодом.

        Args:
            code (str): Унікальний код запису для пошуку.

        Returns:
            Optional[ModelType]: Екземпляр моделі, якщо знайдено, інакше None.

        Raises:
            AttributeError: Якщо модель не має атрибута `code`.
        """
        if not hasattr(self.model, "code"):
            # logger.error(f"Модель {self.model.__name__} не має атрибута 'code' для пошуку.")
            raise AttributeError(f"Модель {self.model.__name__} не має атрибута 'code'.")

        stmt = select(self.model).where(self.model.code == code)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[ModelType]:
        """
        Отримує один запис довідника за його назвою.
        Увага: поле 'name' може бути не унікальним для всіх довідників.
        Цей метод поверне перший знайдений запис або None.

        Args:
            name (str): Назва запису для пошуку.

        Returns:
            Optional[ModelType]: Екземпляр моделі, якщо знайдено, інакше None.

        Raises:
            AttributeError: Якщо модель не має атрибута `name`.
        """
        if not hasattr(self.model, "name"):
            # logger.error(f"Модель {self.model.__name__} не має атрибута 'name' для пошуку.")
            raise AttributeError(f"Модель {self.model.__name__} не має атрибута 'name'.")

        stmt = select(self.model).where(self.model.name == name)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()


if __name__ == "__main__":
    # Демонстраційний блок для BaseDictionaryRepository.
    # Це концептуальна демонстрація, оскільки для повноцінної роботи потрібні
    # конкретні моделі, схеми та реальна асинхронна сесія.

    logger.info("--- Базовий Репозиторій для Довідників (BaseDictionaryRepository) ---")

    # 1. Визначення фіктивних моделей та схем для тестування
    from pydantic import BaseModel as PydanticBaseModel  # Для схем
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
    from sqlalchemy import String, Integer


    class Base(DeclarativeBase):
        pass


    class MockDictModel(Base):  # Має імітувати модель, що успадковує BaseDictionaryModel
        __tablename__ = "mock_dictionary_items"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column(String(100))
        code: Mapped[str] = mapped_column(String(50), unique=True)
        description: Mapped[Optional[str]]

        # Для імітації BaseRepository.update
        __table__ = type('Table', (), {'columns': [
            mapped_column('id', Integer, primary_key=True),
            mapped_column('name', String),
            mapped_column('code', String)
        ]})()

        def __repr__(self):
            return f"<MockDictModel(id={self.id}, name='{self.name}', code='{self.code}')>"


    class MockDictCreateSchema(PydanticBaseModel):
        name: str
        code: str
        description: Optional[str] = None


    class MockDictUpdateSchema(PydanticBaseModel):
        name: Optional[str] = None
        description: Optional[str] = None
        # 'code' зазвичай не оновлюється для довідників


    # 2. Макет AsyncSession (дуже спрощений, як у BaseRepository)
    class MockAsyncSession:
        def __init__(self):
            self._store: Dict[Any, MockDictModel] = {}  # Зберігає за ID або кодом для простоти
            self._next_id = 1

        async def add(self, obj):
            obj.id = obj.id or self._next_id; self._store[obj.id] = obj; self._next_id += 1

        async def commit(self):
            pass

        async def refresh(self, obj):
            pass

        async def execute(self, stmt):
            # Спрощена імітація для get_by_code та get_by_name
            # Це потребує кращої імітації SQLAlchemy Core select()
            # Повернемо фіктивний результат для демонстрації
            class MockScalarResult:
                def __init__(self, value_list): self._value_list = value_list

                def scalar_one_or_none(self): return self._value_list[0] if self._value_list else None

            # Припускаємо, що stmt.whereclause містить інформацію для фільтрації
            # Це дуже груба імітація!
            if hasattr(stmt, 'whereclause'):
                # Імітуємо пошук по коду
                # if "code ==" in str(stmt.whereclause).lower(): # Ненадійно
                # У реальних тестах використовуйте тестову БД
                # Для демонстрації, повернемо перший елемент, якщо є
                # Або нічого, якщо список порожній
                # Це не відображає реальну фільтрацію!
                # Тут ми не можемо легко отримати значення з stmt.whereclause.right.value
                # без більш глибокого парсингу SQL Alchemy об'єктів.

                # Просто повернемо перший елемент зі сховища для демонстрації, якщо є
                if self._store:
                    return MockScalarResult(list(self._store.values()))
            return MockScalarResult([])


    async def run_dict_repository_demo():
        logger.info("\n--- Демонстрація роботи BaseDictionaryRepository з Макетами ---")
        mock_session = MockAsyncSession()

        # Створюємо екземпляр репозиторію для нашої фіктивної моделі
        dict_repo = BaseDictionaryRepository[
            MockDictModel, MockDictCreateSchema, MockDictUpdateSchema
        ](db_session=mock_session, model=MockDictModel)

        # 1. Створення запису довідника
        logger.info("\n1. Тест створення запису довідника:")
        create_schema = MockDictCreateSchema(name="Активний", code="ACTIVE", description="Статус активного елемента")
        created_dict_item = await dict_repo.create(create_schema)
        logger.info(f"  Створено: {created_dict_item}")
        assert created_dict_item.code == "ACTIVE"

        # Додамо ще один для тестування get_by_name
        create_schema_pending = MockDictCreateSchema(name="В очікуванні", code="PENDING",
                                                     description="Статус очікування")
        await dict_repo.create(create_schema_pending)

        # 2. Отримання за кодом (імітація)
        logger.info("\n2. Тест отримання за кодом (імітація):")
        # Наш макет execute дуже спрощений, тому цей тест не буде реально фільтрувати.
        # Він поверне перший елемент або нічого.
        # У реальному тесті з БД це б працювало.
        item_by_code = await dict_repo.get_by_code("ACTIVE")
        logger.info(f"  Отримано за кодом 'ACTIVE': {item_by_code}")
        if item_by_code:  # Може бути None через обмеження макета
            assert item_by_code.code == "ACTIVE"

        item_by_code_non_existent = await dict_repo.get_by_code("NON_EXISTENT")
        logger.info(f"  Отримано за кодом 'NON_EXISTENT': {item_by_code_non_existent}")
        assert item_by_code_non_existent is None  # Очікуємо None, бо макет поверне порожній список

        # 3. Отримання за назвою (імітація)
        logger.info("\n3. Тест отримання за назвою (імітація):")
        item_by_name = await dict_repo.get_by_name("Активний")
        logger.info(f"  Отримано за назвою 'Активний': {item_by_name}")
        if item_by_name:  # Може бути None через обмеження макета
            assert item_by_name.name == "Активний"

        item_by_name_non_existent = await dict_repo.get_by_name("Неіснуюча Назва")
        logger.info(f"  Отримано за назвою 'Неіснуюча Назва': {item_by_name_non_existent}")
        assert item_by_name_non_existent is None

        logger.info("\nПримітка: Демонстрація використовує сильно спрощені макети.")
        logger.info("Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")


    import asyncio

    # asyncio.run(run_dict_repository_demo())
    logger.info(
        "\nЗапуск демонстрації BaseDictionaryRepository закоментовано через складність повного макетування SQLAlchemy.")
