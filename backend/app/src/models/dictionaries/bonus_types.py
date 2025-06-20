# backend/app/src/services/dictionaries/bonus_types.py
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.src.services.dictionaries.base_dict import BaseDictionaryService
from backend.app.src.models.dictionaries.bonus_types import BonusType # Модель SQLAlchemy
from backend.app.src.repositories.dictionaries.bonus_type_repository import BonusTypeRepository # Імпорт репозиторію
from backend.app.src.services.cache.base_cache import BaseCacheService # Імпорт базового сервісу кешування
from backend.app.src.schemas.dictionaries.bonus_types import ( # Схеми Pydantic
    BonusTypeCreateSchema, # Виправлено
    BonusTypeUpdateSchema, # Виправлено
    BonusTypeResponseSchema, # Виправлено
)
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


class BonusTypeService(BaseDictionaryService[BonusType, BonusTypeRepository, BonusTypeCreateSchema, BonusTypeUpdateSchema, BonusTypeResponseSchema]):
    """
    Сервіс для управління елементами довідника "Типи Бонусів".
    Успадковує загальні CRUD-операції від BaseDictionaryService.
    Типи бонусів визначають різні категорії нарахувань або списань балів,
    наприклад, "Нагорода за виконання завдання", "Ручне коригування", "Штраф за протермінування".
    Кожен тип може мати позначку `is_penalty`, яка вказує, чи є цей тип штрафом.
    """

    def __init__(self, db_session: AsyncSession, cache_service: BaseCacheService):
        """
        Ініціалізує сервіс BonusTypeService.

        :param db_session: Асинхронна сесія бази даних SQLAlchemy.
        :param cache_service: Екземпляр сервісу кешування.
        """
        bonus_type_repo = BonusTypeRepository(model=BonusType)
        super().__init__(
            db_session,
            repository=bonus_type_repo,
            cache_service=cache_service,
            response_schema=BonusTypeResponse
        )
        # _model_name ініціалізується в BaseDictionaryService з repository.model.__name__
        logger.info(f"BonusTypeService ініціалізовано для моделі: {self._model_name}")

    # --- Кастомні методи для BonusTypeService (якщо потрібні) ---
    # Наприклад, метод для отримання тільки типів, які є штрафами:
    # async def get_penalty_bonus_types(self) -> List[BonusTypeResponse]:
    #     """Отримує всі типи бонусів, які є штрафами."""
    #     logger.debug(f"Спроба отримання всіх типів бонусів, які є штрафами ({self._model_name}).")
    #     if not hasattr(self.model, 'is_penalty'):
    #         logger.warning(f"Модель {self._model_name} не має атрибута 'is_penalty'. Повернення порожнього списку.")
    #         return []
    #
    #     stmt = select(self.model).where(self.model.is_penalty == True).order_by(self.model.name) # type: ignore
    #     items_db = (await self.db_session.execute(stmt)).scalars().all()
    #
    #     response_list = [self.response_schema.model_validate(item) for item in items_db]
    #     logger.info(f"Отримано {len(response_list)} типів бонусів, які є штрафами.")
    #     return response_list
    #
    # Примітка: Поля 'code', 'name', 'description', 'is_penalty' обробляються базовим сервісом,
    # якщо вони присутні в відповідних Pydantic схемах (Create, Update).

logger.debug(f"{BonusTypeService.__name__} (сервіс типів бонусів) успішно визначено.")
