# backend/app/src/repositories/dictionaries/user_role_repository.py
"""
Репозиторій для моделі "Системна Роль Користувача" (UserRole).

Цей модуль визначає клас `UserRoleRepository`, який успадковує `BaseDictionaryRepository`
та надає методи для роботи з довідником системних ролей користувачів.
"""

# Абсолютний імпорт базового репозиторію для довідників
from backend.app.src.repositories.dictionaries.base_dict_repository import BaseDictionaryRepository

# Абсолютний імпорт моделі та схем для Системних Ролей Користувачів
from backend.app.src.models.dictionaries.user_roles import UserRole
from backend.app.src.schemas.dictionaries.user_roles import UserRoleCreateSchema, UserRoleUpdateSchema
from backend.app.src.config import logging # Імпорт logging з конфігурації
# Отримання логера для цього модуля
logger = logging.getLogger(__name__)


class UserRoleRepository(BaseDictionaryRepository[UserRole, UserRoleCreateSchema, UserRoleUpdateSchema]):
    """
    Репозиторій для управління записами довідника "Системна Роль Користувача".

    Успадковує всі базові методи CRUD та специфічні для довідників методи
    від `BaseDictionaryRepository`.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `UserRole`.
        """
        super().__init__(model=UserRole)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    # Тут можна додати специфічні методи для UserRoleRepository, якщо вони потрібні.
    # Наприклад, отримання ролі "за замовчуванням для нового користувача" тощо.
    # async def get_default_role(self, session: AsyncSession) -> Optional[UserRole]:
    #     # логіка методу...
    #     pass


if __name__ == "__main__":
    # Демонстраційний блок для UserRoleRepository.
    logger.info("--- Репозиторій для Довідника Системних Ролей Користувачів (UserRoleRepository) ---")

    logger.info("Для тестування UserRoleRepository потрібна асинхронна сесія SQLAlchemy.")
    logger.info(f"Він успадковує методи від BaseDictionaryRepository для моделі {UserRole.__name__}.")
    logger.info(f"  Очікує схему створення: {UserRoleCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {UserRoleUpdateSchema.__name__}")
