# backend/app/src/repositories/dictionaries/user_type_repository.py
"""
Репозиторій для моделі "Тип Користувача" (UserType).

Цей модуль визначає клас `UserTypeRepository`, який успадковує `BaseDictionaryRepository`
та надає методи для роботи з довідником типів користувачів.
"""

from sqlalchemy.ext.asyncio import AsyncSession

# Абсолютний імпорт базового репозиторію для довідників
from backend.app.src.repositories.dictionaries.base_dict_repository import BaseDictionaryRepository

# Абсолютний імпорт моделі та схем для Типів Користувачів
from backend.app.src.models.dictionaries.user_types import UserType
from backend.app.src.schemas.dictionaries.user_types import UserTypeCreateSchema, UserTypeUpdateSchema


class UserTypeRepository(BaseDictionaryRepository[UserType, UserTypeCreateSchema, UserTypeUpdateSchema]):
    """
    Репозиторій для управління записами довідника "Тип Користувача".

    Успадковує всі базові методи CRUD та специфічні для довідників методи
    від `BaseDictionaryRepository`.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `UserType`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=UserType)

    # Тут можна додати специфічні методи для UserTypeRepository, якщо вони потрібні.


if __name__ == "__main__":
    # Демонстраційний блок для UserTypeRepository.
    print("--- Репозиторій для Довідника Типів Користувачів (UserTypeRepository) ---")

    print("Для тестування UserTypeRepository потрібна асинхронна сесія SQLAlchemy.")
    print(f"Він успадковує методи від BaseDictionaryRepository для моделі {UserType.__name__}.")
    print(f"  Очікує схему створення: {UserTypeCreateSchema.__name__}")
    print(f"  Очікує схему оновлення: {UserTypeUpdateSchema.__name__}")
