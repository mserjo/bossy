# backend/app/src/services/dictionaries/user_types.py
from typing import Optional # Потрібно для прикладу кастомного методу
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.src.services.dictionaries.base_dict import BaseDictionaryService
from backend.app.src.models.dictionaries.user_types import UserType # Модель SQLAlchemy
from backend.app.src.repositories.dictionaries.user_type_repository import UserTypeRepository # Імпорт репозиторію
from backend.app.src.services.cache.base_cache import BaseCacheService # Імпорт базового сервісу кешування
from backend.app.src.schemas.dictionaries.user_types import ( # Схеми Pydantic
    UserTypeCreateSchema, # Виправлено
    UserTypeUpdateSchema, # Виправлено
    UserTypeResponseSchema, # Виправлено
)
from backend.app.src.config import settings # Для доступу до налаштувань системи (наприклад, коду типу користувача за замовчуванням)
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


class UserTypeService(BaseDictionaryService[UserType, UserTypeRepository, UserTypeCreateSchema, UserTypeUpdateSchema, UserTypeResponseSchema]):
    """
    Сервіс для управління елементами довідника "Типи Користувачів".
    Типи користувачів визначають різні категорії користувачів у системі
    (наприклад, 'СПІВРОБІТНИК', 'ПІДРЯДНИК', 'КЛІЄНТ', 'СИСТЕМНИЙ_АГЕНТ').
    Успадковує загальні CRUD-операції від BaseDictionaryService.
    """

    def __init__(self, db_session: AsyncSession, cache_service: BaseCacheService):
        """
        Ініціалізує сервіс UserTypeService.

        :param db_session: Асинхронна сесія бази даних SQLAlchemy.
        :param cache_service: Екземпляр сервісу кешування.
        """
        user_type_repo = UserTypeRepository(model=UserType)
        super().__init__(
            db_session,
            repository=user_type_repo,
            cache_service=cache_service,
            response_schema=UserTypeResponse
        )
        # _model_name ініціалізується в BaseDictionaryService з repository.model.__name__
        logger.info(f"UserTypeService ініціалізовано для моделі: {self._model_name}")

    # --- Кастомні методи для UserTypeService (якщо потрібні) ---
    # Наприклад, отримання типу користувача за замовчуванням, визначеного в налаштуваннях системи.
    #
    # async def get_default_user_type(self) -> Optional[UserTypeResponse]:
    #     """
    #     Отримує тип користувача за замовчуванням, код якого вказано в системних налаштуваннях.
    #     """
    #     default_user_type_code = getattr(settings, 'DEFAULT_USER_TYPE_CODE', None)
    #     if not default_user_type_code:
    #         logger.warning("Код типу користувача за замовчуванням (DEFAULT_USER_TYPE_CODE) не визначено в налаштуваннях.")
    #         return None
    #
    #     logger.debug(f"Спроба отримання типу користувача за замовчуванням з кодом: '{default_user_type_code}'.")
    #     return await self.get_by_code(default_user_type_code)
    #
    # Примітка: Базовий сервіс вже надає get_by_code, тому цей метод є лише обгорткою
    # для отримання коду з налаштувань.

logger.debug(f"{UserTypeService.__name__} (сервіс типів користувачів) успішно визначено.")
