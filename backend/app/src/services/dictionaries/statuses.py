# backend/app/src/services/dictionaries/statuses.py
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.src.services.dictionaries.base_dict import BaseDictionaryService
from backend.app.src.models.dictionaries.statuses import Status # Модель SQLAlchemy
from backend.app.src.repositories.dictionaries.status_repository import StatusRepository # Імпорт репозиторію
from backend.app.src.services.cache.base_cache import BaseCacheService # Імпорт базового сервісу кешування
from backend.app.src.schemas.dictionaries.statuses import ( # Схеми Pydantic
    StatusCreateSchema,
    StatusUpdateSchema,
    StatusResponseSchema,
)
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


class StatusService(BaseDictionaryService[Status, StatusRepository, StatusCreateSchema, StatusUpdateSchema, StatusResponseSchema]):
    """
    Сервіс для управління елементами довідника "Статуси".
    Статуси є загальними для системи і можуть застосовуватися до різних сутностей
    (наприклад, 'НОВИЙ', 'В РОБОТІ', 'ЗАВЕРШЕНО', 'СКАСОВАНО').
    Кожен статус може мати поле `entity_type`, що вказує, до якого типу сутності
    він застосовується (наприклад, 'ЗАВДАННЯ', 'ПРОЕКТ').
    Успадковує загальні CRUD-операції від BaseDictionaryService.
    Згідно з `technical_task.txt`, перегляд доступний усім, але зміни - тільки суперкористувачам
    (це контролюється на рівні API, сервіс надає операції).
    """

    def __init__(self, db_session: AsyncSession, cache_service: BaseCacheService):
        """
        Ініціалізує сервіс StatusService.

        :param db_session: Асинхронна сесія бази даних SQLAlchemy.
        :param cache_service: Екземпляр сервісу кешування.
        """
        status_repo = StatusRepository(model=Status)
        super().__init__(
            db_session,
            repository=status_repo,
            cache_service=cache_service,
            response_schema=StatusResponse
        )
        # _model_name ініціалізується в BaseDictionaryService з repository.model.__name__
        logger.info(f"StatusService ініціалізовано для моделі: {self._model_name}")

    # --- Кастомні методи для StatusService (якщо потрібні) ---
    # Наприклад, якщо статуси мають специфічну бізнес-логіку або потрібно фільтрувати
    # статуси за типом сутності, до якої вони застосовуються.
    #
    # async def get_statuses_for_entity_type(self, entity_type: str) -> List[StatusResponse]:
    #     """
    #     Отримує всі статуси, що застосовуються до вказаного типу сутності.
    #     Припускає наявність поля 'entity_type' в моделі Status.
    #
    #     :param entity_type: Тип сутності (наприклад, 'TASK', 'PROJECT').
    #     :return: Список Pydantic схем StatusResponse.
    #     """
    #     # TODO: Розглянути використання Enum для entity_type, якщо значення фіксовані.
    #     logger.debug(f"Спроба отримання статусів для типу сутності: {entity_type} ({self._model_name}).")
    #     if not hasattr(self.model, 'entity_type'):
    #         logger.warning(f"Модель {self._model_name} не має атрибута 'entity_type'. Повернення порожнього списку.")
    #         return []
    #
    #     stmt = select(self.model).where(self.model.entity_type == entity_type).order_by(self.model.name) # type: ignore
    #     items_db = (await self.db_session.execute(stmt)).scalars().all()
    #
    #     response_list = [self.response_schema.model_validate(item) for item in items_db]
    #     logger.info(f"Отримано {len(response_list)} статусів для типу сутності '{entity_type}'.")
    #     return response_list
    #
    # Загальні CRUD-методи (get_by_id, get_by_code, get_all, create, update, delete)
    # успадковуються від BaseDictionaryService і використовують модель Status та відповідні схеми.
    # Поле 'entity_type' буде оброблятися базовим сервісом, якщо воно є в схемах Create/Update.

logger.debug(f"{StatusService.__name__} (сервіс статусів) успішно визначено.")
