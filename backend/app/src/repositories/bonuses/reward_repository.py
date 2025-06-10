# backend/app/src/repositories/bonuses/reward_repository.py
"""
Репозиторій для моделі "Нагорода" (Reward).

Цей модуль визначає клас `RewardRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з нагородами, доступними в групах.
"""

from typing import List, Optional, Tuple, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import selectinload

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.bonuses.reward import Reward
from backend.app.src.schemas.bonuses.reward import RewardCreateSchema, RewardUpdateSchema


# from backend.app.src.core.dicts import SomeStateEnum # Якщо поле state використовує Enum
# from backend.app.src.config.logging import get_logger # Якщо потрібне логування

# logger = get_logger(__name__)

class RewardRepository(BaseRepository[Reward, RewardCreateSchema, RewardUpdateSchema]):
    """
    Репозиторій для управління нагородами (`Reward`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    методи для отримання нагород, доступних у конкретній групі.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `Reward`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=Reward)

    async def get_rewards_by_group_id(
            self,
            group_id: int,
            active_only: bool = True,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[Reward], int]:
        """
        Отримує список нагород, доступних у вказаній групі, з пагінацією.

        Args:
            group_id (int): ID групи.
            active_only (bool): Якщо True, повертає лише активні нагороди
                                (де поле `state` має значення "active").
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[Reward], int]: Кортеж зі списком нагород та їх загальною кількістю.
        """
        filters = [self.model.group_id == group_id]
        if active_only:
            # Модель Reward успадковує BaseMainModel, який має поле 'state' через StateMixin.
            # Припускаємо, що активний стан позначається як "active".
            # TODO: Узгодити значення "active" з можливим Enum для станів, якщо такий буде використовуватися.
            filters.append(self.model.state == "active")
            # Додатково можна фільтрувати за quantity_available > 0, якщо це потрібно
            # filters.append(or_(self.model.quantity_available > 0, self.model.quantity_available == None))

        order_by = [self.model.cost.asc(), self.model.name.asc()]  # Сортувати за вартістю, потім за назвою
        # options = [selectinload(self.model.group)] # Якщо потрібно завантажувати групу

        return await self.get_multi(skip=skip, limit=limit, filters=filters, order_by=order_by)  # , options=options)


if __name__ == "__main__":
    # Демонстраційний блок для RewardRepository.
    print("--- Репозиторій Нагород (RewardRepository) ---")

    print("Для тестування RewardRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    print(f"Він успадковує методи від BaseRepository для моделі {Reward.__name__}.")
    print(f"  Очікує схему створення: {RewardCreateSchema.__name__}")
    print(f"  Очікує схему оновлення: {RewardUpdateSchema.__name__}")

    print("\nСпецифічні методи:")
    print("  - get_rewards_by_group_id(group_id: int, active_only: bool = True, skip: int = 0, limit: int = 100)")

    print("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
    print("TODO: Узгодити значення 'active' для фільтра `active_only` з можливим Enum для станів.")
