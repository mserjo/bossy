# backend/app/src/repositories/dictionaries/messenger_platform_repository.py
"""
Репозиторій для моделі "Платформа Месенджера" (MessengerPlatform).

Цей модуль визначає клас `MessengerPlatformRepository`, який успадковує `BaseDictionaryRepository`
та надає методи для роботи з довідником платформ месенджерів.
"""

from sqlalchemy.ext.asyncio import AsyncSession

# Абсолютний імпорт базового репозиторію для довідників
from backend.app.src.repositories.dictionaries.base_dict_repository import BaseDictionaryRepository

# Абсолютний імпорт моделі та схем для Платформ Месенджерів
from backend.app.src.models.dictionaries.messengers import MessengerPlatform
from backend.app.src.schemas.dictionaries.messengers import MessengerPlatformCreateSchema, MessengerPlatformUpdateSchema
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)


class MessengerPlatformRepository(
    BaseDictionaryRepository[MessengerPlatform, MessengerPlatformCreateSchema, MessengerPlatformUpdateSchema]):
    """
    Репозиторій для управління записами довідника "Платформа Месенджера".

    Успадковує всі базові методи CRUD та специфічні для довідників методи
    від `BaseDictionaryRepository`.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `MessengerPlatform`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=MessengerPlatform)

    # Тут можна додати специфічні методи для MessengerPlatformRepository, якщо вони потрібні.


if __name__ == "__main__":
    # Демонстраційний блок для MessengerPlatformRepository.
    logger.info("--- Репозиторій для Довідника Платформ Месенджерів (MessengerPlatformRepository) ---")

    logger.info("Для тестування MessengerPlatformRepository потрібна асинхронна сесія SQLAlchemy.")
    logger.info(f"Він успадковує методи від BaseDictionaryRepository для моделі {MessengerPlatform.__name__}.")
    logger.info(f"  Очікує схему створення: {MessengerPlatformCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {MessengerPlatformUpdateSchema.__name__}")
