# backend/app/src/services/dictionaries/user_roles.py
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.src.services.dictionaries.base_dict import BaseDictionaryService
from backend.app.src.models.dictionaries.user_roles import UserRole # Модель SQLAlchemy
from backend.app.src.repositories.dictionaries.user_role_repository import UserRoleRepository # Імпорт репозиторію
from backend.app.src.services.cache.base_cache import BaseCacheService # Імпорт базового сервісу кешування
from backend.app.src.schemas.dictionaries.user_roles import ( # Схеми Pydantic
    UserRoleCreate,
    UserRoleUpdate,
    UserRoleResponse,
)
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


class UserRoleService(BaseDictionaryService[UserRole, UserRoleRepository, UserRoleCreate, UserRoleUpdate, UserRoleResponse]):
    """
    Сервіс для управління елементами довідника "Ролі Користувачів".
    Ролі визначають набір прав та обов'язків користувачів у системі
    (наприклад, 'SUPERUSER', 'ADMIN', 'GROUP_MANAGER', 'USER').
    Успадковує загальні CRUD-операції від BaseDictionaryService.

    Кожна роль може мати поле `permissions` (наприклад, JSONB або текстове поле),
    що описує конкретні дозволи. Обробка цього поля залежить від його реалізації
    в моделі та Pydantic-схемах.
    """

    def __init__(self, db_session: AsyncSession, cache_service: BaseCacheService):
        """
        Ініціалізує сервіс UserRoleService.

        :param db_session: Асинхронна сесія бази даних SQLAlchemy.
        :param cache_service: Екземпляр сервісу кешування.
        """
        user_role_repo = UserRoleRepository(model=UserRole)
        super().__init__(
            db_session,
            repository=user_role_repo,
            cache_service=cache_service,
            response_schema=UserRoleResponse
        )
        # _model_name ініціалізується в BaseDictionaryService з repository.model.__name__
        logger.info(f"UserRoleService ініціалізовано для моделі: {self._model_name}")

    # --- Кастомні методи для UserRoleService (якщо потрібні) ---
    # Наприклад, для управління дозволами, пов'язаними з ролями,
    # або для обробки системних ролей, які не можна видаляти/змінювати.

    # TODO: Розглянути додавання логіки для захисту системних ролей (наприклад, 'SUPERUSER')
    # від видалення або зміни критичних полів через стандартні методи update/delete.
    # Це може вимагати перевірки 'code' ролі перед виконанням операції.
    # Наприклад, в методі delete:
    # async def delete(self, item_id: UUID) -> bool:
    #     item_to_delete = await self.get_by_id_orm_model(item_id) # Потрібен метод для отримання ORM моделі
    #     if item_to_delete and getattr(item_to_delete, 'code', None) == 'SUPERUSER':
    #         logger.warning(f"Спроба видалення системної ролі 'SUPERUSER' (ID: {item_id}). Відхилено.")
    #         # i18n
    #         raise ValueError("Системну роль 'SUPERUSER' не можна видалити.")
    #     return await super().delete(item_id)
    #
    # Примітка: `BaseDictionaryService` вже забезпечує перевірку унікальності 'code' та 'name'
    # при створенні та оновленні, якщо ці поля є в схемах.

logger.debug(f"{UserRoleService.__name__} (сервіс ролей користувачів) успішно визначено.")
