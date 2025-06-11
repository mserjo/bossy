# backend/app/src/repositories/dictionaries/user_role_repository.py
"""
Репозиторій для моделі "Системна Роль Користувача" (UserRole).

Цей модуль визначає клас `UserRoleRepository`, який успадковує `BaseDictionaryRepository`
та надає методи для роботи з довідником системних ролей користувачів.
"""

from sqlalchemy.ext.asyncio import AsyncSession

# Абсолютний імпорт базового репозиторію для довідників
from backend.app.src.repositories.dictionaries.base_dict_repository import BaseDictionaryRepository

# Абсолютний імпорт моделі та схем для Системних Ролей Користувачів
from backend.app.src.models.dictionaries.user_roles import UserRole
from backend.app.src.schemas.dictionaries.user_roles import UserRoleCreateSchema, UserRoleUpdateSchema
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)


class UserRoleRepository(BaseDictionaryRepository[UserRole, UserRoleCreateSchema, UserRoleUpdateSchema]):
    """
    Репозиторій для управління записами довідника "Системна Роль Користувача".

    Успадковує всі базові методи CRUD та специфічні для довідників методи
    від `BaseDictionaryRepository`.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `UserRole`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=UserRole)

    # Тут можна додати специфічні методи для UserRoleRepository, якщо вони потрібні.
    # Наприклад, отримання ролі "за замовчуванням для нового користувача" тощо.


if __name__ == "__main__":
    # Демонстраційний блок для UserRoleRepository.
    logger.info("--- Репозиторій для Довідника Системних Ролей Користувачів (UserRoleRepository) ---")

    logger.info("Для тестування UserRoleRepository потрібна асинхронна сесія SQLAlchemy.")
    logger.info(f"Він успадковує методи від BaseDictionaryRepository для моделі {UserRole.__name__}.")
    logger.info(f"  Очікує схему створення: {UserRoleCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {UserRoleUpdateSchema.__name__}")
