# backend/app/src/services/dictionaries/bonus_types.py
# import logging # Замінено на централізований логер
# from typing import List # Для потенційних кастомних методів (наразі не використовуються)
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select # Для потенційних кастомних методів

# Повні шляхи імпорту
from backend.app.src.services.dictionaries.base_dict import BaseDictionaryService
from backend.app.src.models.dictionaries.bonus_types import BonusType # Модель SQLAlchemy
from backend.app.src.schemas.dictionaries.bonus_types import ( # Схеми Pydantic
    BonusTypeCreate,
    BonusTypeUpdate,
    BonusTypeResponse,
)
from backend.app.src.config.logging import logger # Централізований логер

class BonusTypeService(BaseDictionaryService[BonusType, BonusTypeCreate, BonusTypeUpdate, BonusTypeResponse]):
    """
    Сервіс для управління елементами довідника "Типи Бонусів".
    Успадковує загальні CRUD-операції від BaseDictionaryService.
    Типи бонусів визначають різні категорії нарахувань або списань балів,
    наприклад, "Нагорода за виконання завдання", "Ручне коригування", "Штраф за протермінування".
    Кожен тип може мати позначку `is_penalty`, яка вказує, чи є цей тип штрафом.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує сервіс BonusTypeService.

        :param db_session: Асинхронна сесія бази даних SQLAlchemy.
        """
        super().__init__(db_session, model=BonusType, response_schema=BonusTypeResponse)
        logger.info(f"BonusTypeService ініціалізовано для моделі: {self._model_name}")

    # --- Кастомні методи для BonusTypeService (якщо потрібні) ---
    # Наприклад, метод для отримання тільки типів, які є штрафами:
    # async def get_penalty_bonus_types(self) -> List[BonusTypeResponse]:
    #     """Отримує всі типи бонусів, які є штрафами."""
    #     logger.debug(f"Спроба отримання всіх типів бонусів, які є штрафами ({self._model_name}).")
    #     if not hasattr(self.model, 'is_penalty'):
    #         logger.warning(f"Модель {self._model_name} не має атрибута 'is_penalty'. Повернення порожнього списку.")
    #         return []
    #
    #     stmt = select(self.model).where(self.model.is_penalty == True).order_by(self.model.name) # type: ignore
    #     items_db = (await self.db_session.execute(stmt)).scalars().all()
    #
    #     response_list = [self.response_schema.model_validate(item) for item in items_db]
    #     logger.info(f"Отримано {len(response_list)} типів бонусів, які є штрафами.")
    #     return response_list
    #
    # Примітка: Поля 'code', 'name', 'description', 'is_penalty' обробляються базовим сервісом,
    # якщо вони присутні в відповідних Pydantic схемах (Create, Update).

logger.debug(f"{BonusTypeService.__name__} (сервіс типів бонусів) успішно визначено.")
