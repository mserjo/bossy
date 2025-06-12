# backend/app/src/repositories/dictionaries/user_type_repository.py
"""
Репозиторій для моделі "Тип Користувача" (UserType).

Цей модуль визначає клас `UserTypeRepository`, який успадковує `BaseDictionaryRepository`
та надає методи для роботи з довідником типів користувачів.
"""

# Абсолютний імпорт базового репозиторію для довідників
from backend.app.src.repositories.dictionaries.base_dict_repository import BaseDictionaryRepository

# Абсолютний імпорт моделі та схем для Типів Користувачів
from backend.app.src.models.dictionaries.user_types import UserType
from backend.app.src.schemas.dictionaries.user_types import UserTypeCreateSchema, UserTypeUpdateSchema
from backend.app.src.config import logging # Імпорт logging з конфігурації
# Отримання логера для цього модуля
logger = logging.getLogger(__name__)


class UserTypeRepository(BaseDictionaryRepository[UserType, UserTypeCreateSchema, UserTypeUpdateSchema]):
    """
    Репозиторій для управління записами довідника "Тип Користувача".

    Успадковує всі базові методи CRUD та специфічні для довідників методи
    від `BaseDictionaryRepository`.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `UserType`.
        """
        super().__init__(model=UserType)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    # Тут можна додати специфічні методи для UserTypeRepository, якщо вони потрібні.
    # Наприклад:
    # async def get_user_type_for_registration(self, session: AsyncSession) -> Optional[UserType]:
    #     # логіка методу...
    #     pass


if __name__ == "__main__":
    # Демонстраційний блок для UserTypeRepository.
    logger.info("--- Репозиторій для Довідника Типів Користувачів (UserTypeRepository) ---")

    logger.info("Для тестування UserTypeRepository потрібна асинхронна сесія SQLAlchemy.")
    logger.info(f"Він успадковує методи від BaseDictionaryRepository для моделі {UserType.__name__}.")
    logger.info(f"  Очікує схему створення: {UserTypeCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {UserTypeUpdateSchema.__name__}")
