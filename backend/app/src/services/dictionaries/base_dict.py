# backend/app/src/services/dictionaries/base_dict.py
"""
Базовий сервіс для моделей-довідників.

Надає спільну логіку для CRUD операцій з довідниками, включаючи
кешування для оптимізації доступу до часто запитуваних даних.
"""
from typing import TypeVar, Generic, List, Optional, Type, Any, Dict
from uuid import UUID
from datetime import datetime, timezone # Додано timezone
import json # Для серіалізації в кеш

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select # Оновлено імпорт
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel

from backend.app.src.services.base import BaseService
from backend.app.src.repositories.dictionaries.base_dict_repository import BaseDictionaryRepository # Імпорт репозиторію
from backend.app.src.services.cache.base_cache import BaseCacheService # Імпорт сервісу кешування
from backend.app.src.config import logger # Використання спільного логера з конфігу
from backend.app.src.config import settings


# Визначення генеричних типів
DictModelType = TypeVar("DictModelType") # Модель SQLAlchemy для довідника
RepoType = TypeVar("RepoType", bound=BaseDictionaryRepository) # Тип репозиторію
SchemaCreateType = TypeVar("SchemaCreateType", bound=BaseModel)
SchemaUpdateType = TypeVar("SchemaUpdateType", bound=BaseModel)
SchemaResponseType = TypeVar("SchemaResponseType", bound=BaseModel)


class BaseDictionaryService(
    BaseService,
    Generic[DictModelType, RepoType, SchemaCreateType, SchemaUpdateType, SchemaResponseType]
):
    """
    Загальний базовий сервіс для моделей типу "довідник".
    Використовує переданий репозиторій для доступу до даних та сервіс кешування.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        repository: RepoType,
        cache_service: BaseCacheService,
        response_schema: Type[SchemaResponseType],
        # model: Type[DictModelType] # Модель тепер отримується з репозиторію
    ):
        super().__init__(db_session)
        self.repository: RepoType = repository
        self.cache_service: BaseCacheService = cache_service
        self.response_schema: Type[SchemaResponseType] = response_schema
        self._model_name: str = self.repository.model.__name__ # Отримуємо ім'я моделі з репозиторію
        self._cache_prefix = f"dict_item:{self._model_name}:"
        self._all_items_cache_key = f"all_dict_items:{self._model_name}"
        logger.info(
            f"BaseDictionaryService ініціалізовано для моделі: {self._model_name} "
            f"з репозиторієм {repository.__class__.__name__} та кешем {cache_service.__class__.__name__}"
        )

    def _generate_cache_key(self, identifier: Any) -> str:
        return f"{self._cache_prefix}{identifier}"

    async def get_by_id(self, item_id: UUID) -> Optional[SchemaResponseType]:
        cache_key = self._generate_cache_key(f"id:{item_id}")
        cached_item_str = await self.cache_service.get(cache_key)

        if cached_item_str:
            try:
                item_dict = json.loads(cached_item_str)
                logger.debug(f"{self._model_name} ID '{item_id}' знайдено в кеші.")
                return self.response_schema.model_validate(item_dict)
            except json.JSONDecodeError:
                logger.warning(f"Помилка десеріалізації кешу для {self._model_name} ID '{item_id}'. Запит до БД.")

        logger.debug(f"{self._model_name} ID '{item_id}' не знайдено в кеші. Запит до БД.")
        item_db = await self.repository.get_by_id(self.db_session, item_id) # Використовуємо репозиторій
        if item_db:
            response_item = self.response_schema.model_validate(item_db)
            try:
                await self.cache_service.set(cache_key, response_item.model_dump_json(), expire_seconds=settings.CACHE_EXPIRATION_DICTIONARIES)
            except Exception as e: # Обробка помилок серіалізації/запису в кеш
                logger.error(f"Помилка запису в кеш для {self._model_name} ID '{item_id}': {e}", exc_info=settings.DEBUG)
            return response_item
        return None

    async def get_by_code(self, code: str) -> Optional[SchemaResponseType]:
        cache_key = self._generate_cache_key(f"code:{code}")
        cached_item_str = await self.cache_service.get(cache_key)

        if cached_item_str:
            try:
                item_dict = json.loads(cached_item_str)
                logger.debug(f"{self._model_name} code '{code}' знайдено в кеші.")
                return self.response_schema.model_validate(item_dict)
            except json.JSONDecodeError:
                logger.warning(f"Помилка десеріалізації кешу для {self._model_name} code '{code}'. Запит до БД.")

        logger.debug(f"{self._model_name} code '{code}' не знайдено в кеші. Запит до БД.")
        item_db = await self.repository.get_by_code(self.db_session, code) # Використовуємо репозиторій
        if item_db:
            response_item = self.response_schema.model_validate(item_db)
            try:
                await self.cache_service.set(cache_key, response_item.model_dump_json(), expire_seconds=settings.CACHE_EXPIRATION_DICTIONARIES)
            except Exception as e:
                logger.error(f"Помилка запису в кеш для {self._model_name} code '{code}': {e}", exc_info=settings.DEBUG)
            return response_item
        return None

    async def get_all(self, skip: int = 0, limit: Optional[int] = None, # limit None для отримання всіх для кешу
                      sort_by: Optional[str] = None, sort_order: str = "asc"
                      ) -> List[SchemaResponseType]:
        # Кешування повного списку може бути складним, якщо він дуже великий.
        # Тут реалізовано простий варіант: кешуємо весь список, якщо limit не встановлено.
        # Для пагінованих запитів кеш не використовується, йде прямий запит до БД.

        if skip == 0 and limit is None: # Тільки якщо запитуємо весь список
            cached_list_str = await self.cache_service.get(self._all_items_cache_key)
            if cached_list_str:
                try:
                    items_list_dict = json.loads(cached_list_str)
                    logger.debug(f"Повний список {self._model_name} знайдено в кеші.")
                    return [self.response_schema.model_validate(item_dict) for item_dict in items_list_dict]
                except json.JSONDecodeError:
                    logger.warning(f"Помилка десеріалізації кешованого списку {self._model_name}. Запит до БД.")

        logger.debug(f"Запит до БД для списку {self._model_name}: skip={skip}, limit={limit}, sort_by={sort_by}, sort_order={sort_order}")

        # BaseDictionaryRepository не має get_all, BaseRepository має get_multi
        # Припускаємо, що BaseDictionaryRepository успадковує get_multi або має свій get_all.
        # Для універсальності, будемо використовувати get_multi з репозиторію, якщо він є.
        # Або, якщо репозиторій це BaseDictionaryRepository, він сам має get_all.
        # Поточний BaseDictionaryRepository не має get_all, але має get_multi від BaseRepository.

        # Сортування за замовчуванням, якщо не надано
        if not sort_by:
            if hasattr(self.repository.model, 'name'):
                sort_by = 'name'
            elif hasattr(self.repository.model, 'code'):
                sort_by = 'code'
            else:
                sort_by = 'id' # type: ignore

        filters_dict: Optional[Dict[str, Any]] = None # Для get_multi, якщо буде потрібно

        # Виклик get_multi з BaseRepository
        items_db = await self.repository.get_multi( # type: ignore
            session=self.db_session,
            skip=skip,
            limit=limit if limit is not None else 10000, # Великий ліміт, якщо None
            filters=filters_dict,
            sort_by=sort_by,
            sort_order=sort_order
        )

        response_list = [self.response_schema.model_validate(item) for item in items_db]

        if skip == 0 and limit is None and response_list: # Кешуємо, тільки якщо запитали весь список і він не порожній
            try:
                list_to_cache = [item.model_dump() for item in response_list] # Зберігаємо як dict
                await self.cache_service.set(self._all_items_cache_key, json.dumps(list_to_cache), expire_seconds=settings.CACHE_EXPIRATION_DICTIONARIES_LIST)
            except Exception as e:
                 logger.error(f"Помилка запису в кеш списку {self._model_name}: {e}", exc_info=settings.DEBUG)

        logger.info(f"Отримано {len(response_list)} елементів {self._model_name} з БД.")
        return response_list

    async def create(self, data: SchemaCreateType, **kwargs: Any) -> SchemaResponseType:
        logger.debug(f"Спроба створення нового {self._model_name} з даними: {data}, додатково: {kwargs}")

        # Унікальність `code` та `name` має перевірятися на рівні БД через constraints,
        # або в методі репозиторію `create`, якщо він перевантажений.
        # Тут ми довіряємо репозиторію або БД цю перевірку.

        try:
            # kwargs можуть містити, наприклад, created_by_user_id
            new_item_db = await self.repository.create(self.db_session, obj_in=data, **kwargs) # type: ignore

            # Інвалідація кешу для списку всіх елементів
            await self.cache_service.delete(self._all_items_cache_key)
            logger.debug(f"Кеш для списку '{self._all_items_cache_key}' інвалідовано після створення.")

            response_item = self.response_schema.model_validate(new_item_db)
            # Додавання нового елемента в кеш за ID та кодом
            cache_key_id = self._generate_cache_key(f"id:{new_item_db.id}") # type: ignore
            await self.cache_service.set(cache_key_id, response_item.model_dump_json(), expire_seconds=settings.CACHE_EXPIRATION_DICTIONARIES)
            if hasattr(new_item_db, 'code'):
                cache_key_code = self._generate_cache_key(f"code:{new_item_db.code}") # type: ignore
                await self.cache_service.set(cache_key_code, response_item.model_dump_json(), expire_seconds=settings.CACHE_EXPIRATION_DICTIONARIES)

            logger.info(f"{self._model_name} успішно створено з ID: {new_item_db.id}") # type: ignore
            return response_item
        except IntegrityError as e:
            await self.rollback() # Відкат через BaseService
            logger.error(f"Помилка цілісності при створенні {self._model_name}: {e}", exc_info=settings.DEBUG)
            # TODO: [Error Handling] Повертати більш специфічні помилки, можливо кастомні
            # Наприклад, аналізувати e.orig для визначення типу порушення (unique constraint)
            raise ValueError(f"Не вдалося створити {self._model_name}: конфлікт даних. Перевірте унікальність полів.") # i18n
        except Exception as e:
            await self.rollback()
            logger.error(f"Неочікувана помилка при створенні {self._model_name}: {e}", exc_info=settings.DEBUG)
            raise

    async def update(self, item_id: UUID, data: SchemaUpdateType, **kwargs: Any) -> Optional[SchemaResponseType]:
        logger.debug(f"Спроба оновлення {self._model_name} з ID: {item_id}, дані: {data}, додатково: {kwargs}")

        # Отримуємо об'єкт з БД через репозиторій
        item_db = await self.repository.get_by_id(self.db_session, item_id) # type: ignore
        if not item_db:
            logger.warning(f"{self._model_name} з ID '{item_id}' не знайдено для оновлення.")
            return None

        # Унікальність `code` та `name` (якщо змінюються) має перевірятися на рівні БД або репозиторію.
        # Сервіс може додати цю логіку, якщо репозиторій її не має.
        # Поточний BaseRepository.update оновить поля.

        try:
            # kwargs можуть містити, наприклад, updated_by_user_id
            updated_item_db = await self.repository.update(self.db_session, db_obj=item_db, obj_in=data, **kwargs) # type: ignore

            # Інвалідація кешів
            await self.cache_service.delete(self._all_items_cache_key)
            cache_key_id = self._generate_cache_key(f"id:{item_id}")
            await self.cache_service.delete(cache_key_id)
            if hasattr(updated_item_db, 'code'):
                cache_key_code_old = self._generate_cache_key(f"code:{getattr(item_db, 'code')}") # Старий код
                await self.cache_service.delete(cache_key_code_old)
                cache_key_code_new = self._generate_cache_key(f"code:{updated_item_db.code}") # type: ignore
                # Оновлений елемент одразу додається в кеш після оновлення нижче

            logger.debug(f"Кеші для {self._model_name} ID '{item_id}' та списку інвалідовано після оновлення.")

            response_item = self.response_schema.model_validate(updated_item_db)
            # Оновлення кешу для оновленого елемента
            await self.cache_service.set(cache_key_id, response_item.model_dump_json(), expire_seconds=settings.CACHE_EXPIRATION_DICTIONARIES)
            if hasattr(updated_item_db, 'code'):
                 await self.cache_service.set(cache_key_code_new, response_item.model_dump_json(), expire_seconds=settings.CACHE_EXPIRATION_DICTIONARIES)


            logger.info(f"{self._model_name} з ID '{item_id}' успішно оновлено.")
            return response_item
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності при оновленні {self._model_name} ID '{item_id}': {e}", exc_info=settings.DEBUG)
            raise ValueError(f"Не вдалося оновити {self._model_name}: конфлікт даних.") # i18n
        except Exception as e:
            await self.rollback()
            logger.error(f"Неочікувана помилка при оновленні {self._model_name} ID '{item_id}': {e}", exc_info=settings.DEBUG)
            raise

    async def delete(self, item_id: UUID) -> bool:
        logger.debug(f"Спроба видалення {self._model_name} з ID: {item_id}")

        # Потрібно отримати об'єкт, щоб знати його 'code' для інвалідації кешу, якщо він є
        item_db_to_delete = await self.repository.get_by_id(self.db_session, item_id) # type: ignore
        if not item_db_to_delete:
            logger.warning(f"{self._model_name} з ID '{item_id}' не знайдено для видалення.")
            return False

        item_code_for_cache = getattr(item_db_to_delete, 'code', None)

        try:
            deleted_item_orm = await self.repository.remove(self.db_session, id=item_id) # type: ignore
            if deleted_item_orm is None: # Якщо remove повертає None при невдачі або відсутності
                 logger.warning(f"{self._model_name} з ID '{item_id}' не вдалося видалити або не знайдено репозиторієм.")
                 return False

            # Інвалідація кешів
            await self.cache_service.delete(self._all_items_cache_key)
            await self.cache_service.delete(self._generate_cache_key(f"id:{item_id}"))
            if item_code_for_cache:
                await self.cache_service.delete(self._generate_cache_key(f"code:{item_code_for_cache}"))

            logger.info(f"{self._model_name} з ID '{item_id}' (Код: {item_code_for_cache or 'N/A'}) успішно видалено.")
            return True
        except IntegrityError as e:
            await self.rollback()
            logger.error(
                f"Помилка цілісності при видаленні {self._model_name} ID '{item_id}': {e}. Можливо, елемент використовується.",
                exc_info=settings.DEBUG)
            # TODO: [Error Handling] Розглянути можливість кидання кастомної помилки `CannotDeleteInUseError`.
            raise ValueError(f"{self._model_name} ID '{item_id}' використовується і не може бути видалений.") # i18n
        except Exception as e:
            await self.rollback()
            logger.error(f"Неочікувана помилка при видаленні {self._model_name} ID '{item_id}': {e}", exc_info=settings.DEBUG)
            raise

logger.info("BaseDictionaryService (базовий сервіс довідників) успішно визначено.")
