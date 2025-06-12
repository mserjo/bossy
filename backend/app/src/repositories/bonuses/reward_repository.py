# backend/app/src/repositories/bonuses/reward_repository.py
"""
Репозиторій для моделі "Нагорода" (Reward).

Цей модуль визначає клас `RewardRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з нагородами, доступними в групах.
"""

from typing import List, Tuple, Dict, Any

from sqlalchemy import select, func # select, func можуть бути корисні для майбутніх складних запитів
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import selectinload

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.bonuses.reward import Reward
from backend.app.src.schemas.bonuses.reward import RewardCreateSchema, RewardUpdateSchema
from backend.app.src.config import logging # Імпорт logging з конфігурації
# Отримання логера для цього модуля
logger = logging.getLogger(__name__)

# from backend.app.src.core.dicts import SomeStateEnum # Якщо поле state використовує Enum

class RewardRepository(BaseRepository[Reward, RewardCreateSchema, RewardUpdateSchema]):
    """
    Репозиторій для управління нагородами (`Reward`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    методи для отримання нагород, доступних у конкретній групі.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `Reward`.
        """
        super().__init__(model=Reward)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_rewards_by_group_id(
            self,
            session: AsyncSession,
            group_id: int,
            active_only: bool = True,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[Reward], int]:
        """
        Отримує список нагород, доступних у вказаній групі, з пагінацією.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            group_id (int): ID групи.
            active_only (bool): Якщо True, повертає лише активні нагороди.
                                # TODO: [Перевірка Поля Стану] Узгодити з `technical_task.txt` / `structure-claude-v2.md`
                                #       наявність та значення поля стану (напр., `state="active"`).
            skip (int): Кількість записів для пропуску.
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            Tuple[List[Reward], int]: Кортеж зі списком нагород та їх загальною кількістю.
        """
        logger.debug(
            f"Отримання нагород для групи ID: {group_id}, active_only: {active_only}, skip: {skip}, limit: {limit}"
        )
        filters_dict: Dict[str, Any] = {"group_id": group_id}

        if active_only:
            # Модель Reward успадковує BaseMainModel, який має поле 'state' через StateMixin.
            # Припускаємо, що активний стан позначається як "active".
            # TODO: [Визначення Активного Стану] Уточнити значення для активного стану ("active", True, etc.)
            #       згідно з `technical_task.txt` / моделлю даних.
            filters_dict["state"] = "active"
            # Додатково можна фільтрувати за quantity_available > 0, якщо це потрібно
            # filters_dict["quantity_available__gt"] = 0 # Приклад, якщо потрібно quantity_available > 0
            # Або якщо quantity_available може бути None (необмежено):
            # or_filters = [("quantity_available__gt", 0), ("quantity_available", None)]
            # Але BaseRepository не підтримує OR фільтри напряму в filters_dict. Це потребувало б розширення.

        # TODO: [Сортування] BaseRepository.get_multi наразі підтримує сортування лише за одним полем.
        #       Початковий запит був `order_by = [self.model.cost.asc(), self.model.name.asc()]`.
        #       Наразі сортуємо за `cost`. Розглянути розширення BaseRepository для мульти-сортування.
        sort_by_field = "cost"
        sort_order_str = "asc"

        # options = [selectinload(self.model.group)] # Якщо потрібно завантажувати групу, передати в get_multi

        try:
            items = await super().get_multi(
                session=session,
                skip=skip,
                limit=limit,
                filters=filters_dict,
                sort_by=sort_by_field,
                sort_order=sort_order_str
                # options=options # Якщо використовуються
            )
            total_count = await super().count(session=session, filters=filters_dict)
            logger.debug(f"Знайдено {total_count} нагород для групи ID: {group_id}")
            return items, total_count
        except Exception as e:
            logger.error(f"Помилка при отриманні нагород для групи {group_id}: {e}", exc_info=True)
            return [], 0


if __name__ == "__main__":
    # Демонстраційний блок для RewardRepository.
    logger.info("--- Репозиторій Нагород (RewardRepository) ---")

    logger.info("Для тестування RewardRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    logger.info(f"Він успадковує методи від BaseRepository для моделі {Reward.__name__}.")
    logger.info(f"  Очікує схему створення: {RewardCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {RewardUpdateSchema.__name__}")

    logger.info("\nСпецифічні методи:")
    logger.info("  - get_rewards_by_group_id(group_id: int, active_only: bool = True, skip: int = 0, limit: int = 100)")

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
    logger.info("TODO: Узгодити значення 'active' для фільтра `active_only` з можливим Enum для станів.")
