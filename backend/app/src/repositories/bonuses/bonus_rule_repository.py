# backend/app/src/repositories/bonuses/bonus_rule_repository.py
"""
Репозиторій для моделі "Правило Нарахування Бонусів" (BonusRule).

Цей модуль визначає клас `BonusRuleRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з правилами нарахування бонусів,
наприклад, отримання активних правил для конкретного завдання або події.
"""

from typing import List, Dict, Any

from sqlalchemy import select # select може знадобитися для складніших запитів, не через get_multi
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import selectinload

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.bonuses.bonus_rule import BonusRule
from backend.app.src.schemas.bonuses.bonus_rule import BonusRuleCreateSchema, BonusRuleUpdateSchema
from backend.app.src.config.logging import get_logger # Стандартизований імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

# from backend.app.src.core.dicts import SomeStateEnum # Якщо поле state використовує Enum

class BonusRuleRepository(BaseRepository[BonusRule, BonusRuleCreateSchema, BonusRuleUpdateSchema]):
    """
    Репозиторій для управління правилами нарахування бонусів (`BonusRule`).

    Успадковує базові CRUD-методи від `BaseRepository` та може містити
    додаткові методи для специфічного пошуку та фільтрації правил.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `BonusRule`.
        """
        super().__init__(model=BonusRule)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_rules_for_task(
            self, session: AsyncSession, task_id: int, active_only: bool = True
    ) -> List[BonusRule]:
        """
        Отримує список правил нарахування бонусів, пов'язаних із конкретним завданням.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            task_id (int): ID завдання.
            active_only (bool): Якщо True, повертає лише активні правила.
                                # TODO: [Перевірка Поля Стану] Узгодити з `technical_task.txt` та `structure-claude-v2.md`
                                #       наявність та назву поля стану (напр., `state`, `is_active`) в моделі `BonusRule`.

        Returns:
            List[BonusRule]: Список правил нарахування бонусів.
        """
        logger.debug(f"Отримання правил для завдання ID: {task_id}, active_only: {active_only}")
        filters_dict: Dict[str, Any] = {"task_id": task_id}

        if active_only:
            # Модель BonusRule успадковує StateMixin, який має поле 'state'.
            # TODO: [Визначення Активного Стану] Уточнити значення для активного стану (наприклад, "active" або Enum.value).
            #       Поточна реалізація StateMixin використовує Optional[str].
            filters_dict["state"] = "active" # Припускаємо, що активний стан це рядок "active"
            # видалено блок hasattr(self.model, "is_active") оскільки is_active не є стандартним полем моделі BonusRule
            # Якщо поле стану буде іншим або використовувати Enum, це місце потребуватиме оновлення.
            # Коментар про logger.warning видалено, оскільки else блок, де він був, видалено.
                )

        try:
            # Використовуємо get_multi з дуже великим лімітом для отримання всіх відповідних записів.
            # TODO: [Оптимізація Get All] Розглянути додавання методу `get_all_filtered` до BaseRepository
            #       або підтримку `limit=None` в `get_multi` для уникнення магічного числа 1_000_000.
            items = await super().get_multi(session=session, filters=filters_dict, limit=1_000_000)
            logger.debug(f"Знайдено {len(items)} правил для завдання ID: {task_id}")
            return items
        except Exception as e:
            logger.error(f"Помилка при отриманні правил для завдання {task_id}: {e}", exc_info=True)
            return []

    async def get_rules_for_event_task(
            self, session: AsyncSession, event_task_id: int, active_only: bool = True
    ) -> List[BonusRule]:
        """
        Отримує список правил нарахування бонусів, пов'язаних із конкретною подією (завданням типу "подія").

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            event_task_id (int): ID завдання (події).
            active_only (bool): Якщо True, повертає лише активні правила.
                                # TODO: [Перевірка Поля Стану] Аналогічно до get_rules_for_task.

        Returns:
            List[BonusRule]: Список правил нарахування бонусів.
        """
        # TODO: [Уточнення Поля Event ID] Перевірити `technical_task.txt` / `structure-claude-v2.md`:
        #       Чи поле `event_id` в `BonusRule` є окремим ForeignKey, чи це `task_id` для завдання
        #       з певним типом "подія"? Поточна реалізація передбачає наявність `event_id`.
        logger.debug(f"Отримання правил для події ID: {event_task_id}, active_only: {active_only}")
        filters_dict: Dict[str, Any] = {"event_id": event_task_id}

        if active_only:
            # TODO: [Визначення Активного Стану] Аналогічно до get_rules_for_task.
            filters_dict["state"] = "active" # Припускаємо, що активний стан це рядок "active"
            # видалено блок hasattr(self.model, "is_active")
            # Коментар про logger.warning видалено, оскільки else блок, де він був, видалено.
                )

        try:
            # TODO: [Оптимізація Get All] Аналогічно до get_rules_for_task.
            items = await super().get_multi(session=session, filters=filters_dict, limit=1_000_000)
            logger.debug(f"Знайдено {len(items)} правил для події ID: {event_task_id}")
        return items


if __name__ == "__main__":
    # Демонстраційний блок для BonusRuleRepository.
    logger.info("--- Репозиторій Правил Нарахування Бонусів (BonusRuleRepository) ---")

    logger.info("Для тестування BonusRuleRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    logger.info(f"Він успадковує методи від BaseRepository для моделі {BonusRule.__name__}.")
    logger.info(f"  Очікує схему створення: {BonusRuleCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {BonusRuleUpdateSchema.__name__}")

    logger.info("\nСпецифічні методи:")
    logger.info("  - get_rules_for_task(task_id: int, active_only: bool = True)")
    logger.info("  - get_rules_for_event_task(event_task_id: int, active_only: bool = True)")

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
    logger.info("TODO: Узгодити логіку фільтрації 'active_only' з реальним полем стану в моделі BonusRule.")
    logger.info("TODO: Уточнити використання `event_id` у `get_rules_for_event_task`.")
