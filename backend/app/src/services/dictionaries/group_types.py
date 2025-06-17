# backend/app/src/services/dictionaries/group_types.py
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.src.services.dictionaries.base_dict import BaseDictionaryService
from backend.app.src.models.dictionaries.group_types import GroupType # Модель SQLAlchemy
from backend.app.src.repositories.dictionaries.group_type_repository import GroupTypeRepository # Імпорт репозиторію
from backend.app.src.services.cache.base_cache import BaseCacheService # Імпорт базового сервісу кешування
from backend.app.src.schemas.dictionaries.group_types import ( # Схеми Pydantic
    GroupTypeCreate,
    GroupTypeUpdate,
    GroupTypeResponse,
)
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


class GroupTypeService(BaseDictionaryService[GroupType, GroupTypeRepository, GroupTypeCreate, GroupTypeUpdate, GroupTypeResponse]):
    """
    Сервіс для управління елементами довідника "Типи Груп".
    Типи груп визначають різні категорії груп у системі, наприклад,
    'ВІДДІЛ', 'ПРОЕКТНА_КОМАНДА', 'НАВЧАЛЬНА_ГРУПА'.
    Успадковує загальні CRUD-операції від BaseDictionaryService.
    """

    def __init__(self, db_session: AsyncSession, cache_service: BaseCacheService):
        """
        Ініціалізує сервіс GroupTypeService.

        :param db_session: Асинхронна сесія бази даних SQLAlchemy.
        :param cache_service: Екземпляр сервісу кешування.
        """
        group_type_repo = GroupTypeRepository(model=GroupType)
        super().__init__(
            db_session,
            repository=group_type_repo,
            cache_service=cache_service,
            response_schema=GroupTypeResponse
        )
        # _model_name ініціалізується в BaseDictionaryService з repository.model.__name__
        logger.info(f"GroupTypeService ініціалізовано для моделі: {self._model_name}")

    # --- Кастомні методи для GroupTypeService (якщо потрібні) ---
    # Наприклад, якщо певні типи груп мають спеціальну логіку або атрибути:
    # async def get_group_types_for_organizations(self) -> List[GroupTypeResponse]:
    #     """
    #     Приклад методу: отримує типи груп, які можуть бути використані для організаційних структур.
    #     (Потребує додаткової логіки або поля в моделі для розрізнення).
    #     """
    #     logger.debug(f"Отримання типів груп, придатних для організацій ({self._model_name}).")
    #     # Приклад:
    #     # stmt = select(self.model).where(self.model.can_be_organization == True) # type: ignore
    #     # items_db = (await self.db_session.execute(stmt)).scalars().all()
    #     # return [self.response_schema.model_validate(item) for item in items_db]
    #     return await self.get_all() # Поки що повертає всі як приклад

logger.debug(f"{GroupTypeService.__name__} (сервіс типів груп) успішно визначено.")
