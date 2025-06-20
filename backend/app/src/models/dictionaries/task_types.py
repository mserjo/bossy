# backend/app/src/services/dictionaries/task_types.py
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.src.services.dictionaries.base_dict import BaseDictionaryService
from backend.app.src.models.dictionaries.task_types import TaskType # Модель SQLAlchemy
from backend.app.src.repositories.dictionaries.task_type_repository import TaskTypeRepository # Імпорт репозиторію
from backend.app.src.services.cache.base_cache import BaseCacheService # Імпорт базового сервісу кешування
from backend.app.src.schemas.dictionaries.task_types import ( # Схеми Pydantic
    TaskTypeCreateSchema, # Виправлено
    TaskTypeUpdateSchema, # Виправлено
    TaskTypeResponseSchema, # Виправлено
)
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


class TaskTypeService(BaseDictionaryService[TaskType, TaskTypeRepository, TaskTypeCreateSchema, TaskTypeUpdateSchema, TaskTypeResponseSchema]):
    """
    Сервіс для управління елементами довідника "Типи Завдань".
    Типи завдань визначають різні категорії завдань у системі, наприклад,
    'ЗАГАЛЬНЕ_ЗАВДАННЯ', 'ВІДВІДУВАННЯ_ЗУСТРІЧІ', 'ПОДАЧА_ЗВІТУ'.
    Кожен тип завдання може мати поле `default_points` для визначення балів за замовчуванням.
    Успадковує загальні CRUD-операції від BaseDictionaryService.
    """

    def __init__(self, db_session: AsyncSession, cache_service: BaseCacheService):
        """
        Ініціалізує сервіс TaskTypeService.

        :param db_session: Асинхронна сесія бази даних SQLAlchemy.
        :param cache_service: Екземпляр сервісу кешування.
        """
        task_type_repo = TaskTypeRepository(model=TaskType)
        super().__init__(
            db_session,
            repository=task_type_repo,
            cache_service=cache_service,
            response_schema=TaskTypeResponseSchema # Виправлено
        )
        # _model_name ініціалізується в BaseDictionaryService з repository.model.__name__
        logger.info(f"TaskTypeService ініціалізовано для моделі: {self._model_name}")

    # --- Кастомні методи для TaskTypeService (якщо потрібні) ---
    # Наприклад, якщо потрібно отримати типи завдань, які можуть мати бали за замовчуванням:
    #
    # async def get_task_types_with_default_points(self) -> List[TaskTypeResponse]:
    #     """
    #     Отримує типи завдань, для яких визначено бали за замовчуванням (default_points > 0).
    #     Припускає наявність поля 'default_points' в моделі TaskType.
    #     """
    #     logger.debug(f"Отримання типів завдань з балами за замовчуванням ({self._model_name}).")
    #     if not hasattr(self.model, 'default_points'):
    #         logger.warning(f"Модель {self._model_name} не має атрибута 'default_points'. Повернення порожнього списку.")
    #         return []
    #
    #     stmt = select(self.model).where(self.model.default_points > 0).order_by(self.model.name) # type: ignore
    #     items_db = (await self.db_session.execute(stmt)).scalars().all()
    #
    #     response_list = [self.response_schema.model_validate(item) for item in items_db]
    #     logger.info(f"Отримано {len(response_list)} типів завдань з балами за замовчуванням.")
    #     return response_list
    #
    # Примітка: Поля 'code', 'name', 'description', 'default_points' обробляються базовим сервісом,
    # якщо вони присутні в відповідних Pydantic схемах (Create, Update).

logger.debug(f"{TaskTypeService.__name__} (сервіс типів завдань) успішно визначено.")
