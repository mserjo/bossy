# backend/app/src/services/dictionaries/base_dict.py
# import logging # Замінено на централізований логер
from typing import TypeVar, Generic, List, Optional, Type, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel

from backend.app.src.services.base import BaseService  # Повний шлях
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings  # Для доступу до конфігурацій (наприклад, DEBUG)

# Визначення генеричних типів для моделі та схем Pydantic
# ModelType має бути моделлю SQLAlchemy (наприклад, підкласом BaseDictionaryModel з id, code, name)
ModelType = TypeVar("ModelType")
SchemaCreateType = TypeVar("SchemaCreateType", bound=BaseModel)  # Схема для створення
SchemaUpdateType = TypeVar("SchemaUpdateType", bound=BaseModel)  # Схема для оновлення
SchemaResponseType = TypeVar("SchemaResponseType", bound=BaseModel)  # Схема для відповіді


class BaseDictionaryService(
    BaseService,
    Generic[ModelType, SchemaCreateType, SchemaUpdateType, SchemaResponseType]
):
    """
    Загальний базовий сервіс для моделей типу "довідник".
    Надає спільні CRUD-операції для моделей, які зазвичай мають поля
    'id' (UUID), 'code' (str, унікальний), 'name' (str, часто унікальний),
    та 'description' (Optional[str]).

    Передбачається, що ModelType має атрибути 'id', 'code', та 'name'.
    Схеми Pydantic повинні відповідати структурі ModelType.
    """

    def __init__(self, db_session: AsyncSession, model: Type[ModelType], response_schema: Type[SchemaResponseType]):
        """
        Ініціалізує BaseDictionaryService.

        :param db_session: Асинхронна сесія бази даних SQLAlchemy.
        :param model: Клас моделі SQLAlchemy для цього довідника.
        :param response_schema: Схема Pydantic для відповідей.
        """
        super().__init__(db_session)
        self.model: Type[ModelType] = model
        self.response_schema: Type[SchemaResponseType] = response_schema
        self._model_name: str = self.model.__name__  # Для логування
        logger.info(f"BaseDictionaryService ініціалізовано для моделі: {self._model_name}")

    async def get_by_id(self, item_id: UUID) -> Optional[SchemaResponseType]:
        """Отримує елемент довідника за його ID."""
        logger.debug(f"Спроба отримання {self._model_name} за ID: {item_id}")
        # type: ignore через генеричний self.model, припускаємо наявність 'id'
        stmt = select(self.model).where(self.model.id == item_id)  # type: ignore
        item_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if item_db:
            logger.info(f"{self._model_name} з ID '{item_id}' знайдено.")
            return self.response_schema.model_validate(item_db)  # Pydantic v2
        logger.info(f"{self._model_name} з ID '{item_id}' не знайдено.")
        return None

    async def get_by_code(self, code: str) -> Optional[SchemaResponseType]:
        """Отримує елемент довідника за його унікальним кодом."""
        logger.debug(f"Спроба отримання {self._model_name} за кодом: {code}")
        if not hasattr(self.model, 'code'):
            logger.error(f"Модель {self._model_name} не має атрибута 'code'. Неможливо виконати get_by_code.")
            # TODO: Розглянути можливість кидання AttributeError або кастомної помилки.
            return None

        stmt = select(self.model).where(self.model.code == code)  # type: ignore
        item_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if item_db:
            logger.info(f"{self._model_name} з кодом '{code}' знайдено.")
            return self.response_schema.model_validate(item_db)  # Pydantic v2
        logger.info(f"{self._model_name} з кодом '{code}' не знайдено.")
        return None

    async def get_all(self, skip: int = 0, limit: int = 100,
                      # TODO: Додати можливість передачі параметрів сортування (sort_by, sort_order)
                      ) -> List[SchemaResponseType]:
        """Отримує всі елементи для цього типу довідника, з пагінацією."""
        logger.debug(f"Спроба отримання всіх елементів {self._model_name} з skip={skip}, limit={limit}")

        # Сортування за замовчуванням: 'name', якщо є, інакше 'code', інакше 'id'
        if hasattr(self.model, 'name'):
            order_by_attr = self.model.name  # type: ignore
        elif hasattr(self.model, 'code'):
            order_by_attr = self.model.code  # type: ignore
        else:
            order_by_attr = self.model.id  # type: ignore

        stmt = select(self.model).order_by(order_by_attr).offset(skip).limit(limit)
        items_db = (await self.db_session.execute(stmt)).scalars().all()

        response_list = [self.response_schema.model_validate(item) for item in items_db]  # Pydantic v2
        logger.info(f"Отримано {len(response_list)} елементів {self._model_name}.")
        return response_list

    async def create(self, data: SchemaCreateType, **kwargs: Any) -> SchemaResponseType:
        """
        Створює новий елемент довідника.
        Перевіряє унікальність 'code' та 'name', якщо вони є в схемі створення.
        Додаткові атрибути можуть бути передані через kwargs (наприклад, created_by_user_id).
        """
        logger.debug(f"Спроба створення нового {self._model_name} з даними: {data}, додатково: {kwargs}")

        # Перевірка унікальності 'code'
        if hasattr(self.model, 'code') and hasattr(data, 'code'):
            # type: ignore через динамічний доступ до атрибута 'code'
            if await self.get_by_code(data.code):  # type: ignore
                msg = f"{self._model_name} з кодом '{data.code}' вже існує."  # i18n
                logger.warning(msg)
                raise ValueError(msg)

        # TODO: Розглянути можливість зробити перевірку унікальності 'name' конфігурованою (не всі довідники вимагають унікальне ім'я).
        # Перевірка унікальності 'name'
        if hasattr(self.model, 'name') and hasattr(data, 'name'):
            stmt_name = select(self.model.id).where(self.model.name == data.name)  # type: ignore
            if (await self.db_session.execute(stmt_name)).scalar_one_or_none():
                msg = f"{self._model_name} з ім'ям '{data.name}' вже існує."  # i18n
                logger.warning(msg)
                raise ValueError(msg)

        # Pydantic v2: .model_dump() замість .dict()
        new_item_db = self.model(**data.model_dump(), **kwargs)

        self.db_session.add(new_item_db)
        try:
            await self.commit()
            await self.db_session.refresh(new_item_db)
        except IntegrityError as e:  # Обробка помилок цілісності на рівні БД
            await self.rollback()
            logger.error(f"Помилка цілісності при створенні {self._model_name}: {e}", exc_info=settings.DEBUG)
            # Можна перевірити деталі помилки e.orig, щоб надати більш конкретне повідомлення
            raise ValueError(
                f"Не вдалося створити {self._model_name} через конфлікт даних. Перевірте унікальність полів.")  # i18n

        logger.info(f"{self._model_name} успішно створено з ID: {new_item_db.id}")  # type: ignore
        return self.response_schema.model_validate(new_item_db)  # Pydantic v2

    async def update(self, item_id: UUID, data: SchemaUpdateType, **kwargs: Any) -> Optional[SchemaResponseType]:
        """
        Оновлює існуючий елемент довідника за його ID.
        Перевіряє унікальність, якщо 'code' або 'name' змінюються.
        Додаткові атрибути для оновлення моделі (наприклад, updated_by_user_id) передаються через kwargs.
        """
        logger.debug(f"Спроба оновлення {self._model_name} з ID: {item_id}, дані: {data}, додатково: {kwargs}")

        item_db = (await self.db_session.execute(
            select(self.model).where(self.model.id == item_id)  # type: ignore
        )).scalar_one_or_none()

        if not item_db:
            logger.warning(f"{self._model_name} з ID '{item_id}' не знайдено для оновлення.")
            return None

        update_data = data.model_dump(exclude_unset=True)  # Pydantic v2

        # Перевірка унікальності 'code', якщо він змінюється
        if 'code' in update_data and hasattr(self.model, 'code') and update_data['code'] != getattr(item_db, 'code'):
            existing_by_code = await self.get_by_code(update_data['code'])
            if existing_by_code and existing_by_code.id != item_id:  # type: ignore
                msg = f"Інший {self._model_name} з кодом '{update_data['code']}' вже існує."  # i18n
                logger.warning(msg)
                raise ValueError(msg)

        # Перевірка унікальності 'name', якщо він змінюється
        if 'name' in update_data and hasattr(self.model, 'name') and update_data['name'] != getattr(item_db, 'name'):
            stmt_name = select(self.model.id).where(self.model.name == update_data['name'],
                                                    self.model.id != item_id)  # type: ignore
            if (await self.db_session.execute(stmt_name)).scalar_one_or_none():
                msg = f"Інший {self._model_name} з ім'ям '{update_data['name']}' вже існує."  # i18n
                logger.warning(msg)
                raise ValueError(msg)

        for field, value in update_data.items():
            setattr(item_db, field, value)
        for field, value in kwargs.items():  # Застосування додаткових полів з kwargs
            setattr(item_db, field, value)

        # Явно встановлюємо `updated_at`, якщо модель має такий атрибут
        if hasattr(item_db, 'updated_at'):
            setattr(item_db, 'updated_at', datetime.now(timezone.utc))

        self.db_session.add(item_db)
        try:
            await self.commit()
            await self.db_session.refresh(item_db)
        except IntegrityError as e:  # Обробка помилок цілісності на рівні БД
            await self.rollback()
            logger.error(f"Помилка цілісності при оновленні {self._model_name} ID '{item_id}': {e}",
                         exc_info=settings.DEBUG)
            raise ValueError(
                f"Не вдалося оновити {self._model_name} через конфлікт даних. Перевірте унікальність полів.")  # i18n

        logger.info(f"{self._model_name} з ID '{item_id}' успішно оновлено.")
        return self.response_schema.model_validate(item_db)  # Pydantic v2

    async def delete(self, item_id: UUID) -> bool:
        """
        Видаляє елемент довідника за його ID (жорстке видалення).
        """
        logger.debug(f"Спроба видалення {self._model_name} з ID: {item_id}")
        item_db = (await self.db_session.execute(
            select(self.model).where(self.model.id == item_id)  # type: ignore
        )).scalar_one_or_none()

        if not item_db:
            logger.warning(f"{self._model_name} з ID '{item_id}' не знайдено для видалення.")
            return False

        try:
            await self.db_session.delete(item_db)
            await self.commit()
            logger.info(
                f"{self._model_name} з ID '{item_id}' (Код: {getattr(item_db, 'code', 'N/A')}) успішно видалено.")
            return True
        except IntegrityError as e:
            await self.rollback()
            item_code = getattr(item_db, 'code', item_id)
            logger.error(
                f"Помилка цілісності при видаленні {self._model_name} '{item_code}': {e}. Можливо, елемент використовується.",
                exc_info=settings.DEBUG)
            # TODO: Розглянути можливість кидання кастомної помилки `CannotDeleteInUseError` замість повернення False.
            # Наприклад: raise CannotDeleteInUseError(f"{self._model_name} '{item_code}' використовується і не може бути видалений.") # i18n
            return False
        except Exception as e:  # Інші непередбачені помилки
            await self.rollback()
            logger.error(f"Неочікувана помилка при видаленні {self._model_name} ID '{item_id}': {e}",
                         exc_info=settings.DEBUG)
            raise  # Перекидаємо помилку далі, оскільки вона не оброблена специфічно


logger.info("BaseDictionaryService (базовий сервіс довідників) успішно визначено.")
