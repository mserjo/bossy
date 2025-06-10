# backend/app/src/repositories/bonuses/bonus_rule_repository.py
"""
Репозиторій для моделі "Правило Нарахування Бонусів" (BonusRule).

Цей модуль визначає клас `BonusRuleRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з правилами нарахування бонусів,
наприклад, отримання активних правил для конкретного завдання або події.
"""

from typing import List, Optional, Tuple, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import selectinload

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.bonuses.bonus_rule import BonusRule
from backend.app.src.schemas.bonuses.bonus_rule import BonusRuleCreateSchema, BonusRuleUpdateSchema


# from backend.app.src.core.dicts import SomeStateEnum # Якщо поле state використовує Enum
# from backend.app.src.config.logging import get_logger # Якщо потрібне логування

# logger = get_logger(__name__)

class BonusRuleRepository(BaseRepository[BonusRule, BonusRuleCreateSchema, BonusRuleUpdateSchema]):
    """
    Репозиторій для управління правилами нарахування бонусів (`BonusRule`).

    Успадковує базові CRUD-методи від `BaseRepository` та може містити
    додаткові методи для специфічного пошуку та фільтрації правил.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `BonusRule`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=BonusRule)

    async def get_rules_for_task(self, task_id: int, active_only: bool = True) -> List[BonusRule]:
        """
        Отримує список правил нарахування бонусів, пов'язаних із конкретним завданням.

        Args:
            task_id (int): ID завдання.
            active_only (bool): Якщо True, повертає лише активні правила.
                                Припускає, що модель BonusRule має поле `state` (успадковане від StateMixin).

        Returns:
            List[BonusRule]: Список правил нарахування бонусів.
        """
        filters = [self.model.task_id == task_id]
        if active_only:
            # Припускаємо, що активний стан позначається як "active".
            # Це може потребувати узгодження з Enum або конкретними значеннями стану.
            if hasattr(self.model, "state"):
                filters.append(self.model.state == "active")
                # Або, якщо є поле is_active:
            # elif hasattr(self.model, "is_active"):
            #     filters.append(self.model.is_active == True)
            # else:
            #     logger.warning(f"Модель {self.model.__name__} не має поля 'state' або 'is_active' для фільтрації активних правил.")

        # Використовуємо get_multi з дуже великим лімітом для отримання всіх відповідних записів.
        # Краще було б, якби get_multi міг приймати limit=None для відсутності ліміту.
        # Альтернатива: прямий запит select.
        items, _ = await self.get_multi(filters=filters, limit=1_000_000)  # Умовно великий ліміт
        return items

    async def get_rules_for_event_task(self, event_task_id: int, active_only: bool = True) -> List[BonusRule]:
        """
        Отримує список правил нарахування бонусів, пов'язаних із конкретною подією (завданням типу "подія").

        Args:
            event_task_id (int): ID завдання (події).
            active_only (bool): Якщо True, повертає лише активні правила.

        Returns:
            List[BonusRule]: Список правил нарахування бонусів.
        """
        # TODO: Уточнити, чи поле event_id в BonusRule є окремим, чи це task_id для завдання з типом "подія".
        # Поточна реалізація моделі BonusRule має обидва поля: task_id та event_id.
        # Якщо події - це завдання з певним типом, то цей метод може бути схожим на get_rules_for_task,
        # але з додатковою перевіркою типу завдання, або ж використовувати поле event_id.
        filters = [self.model.event_id == event_task_id]
        if active_only:
            if hasattr(self.model, "state"):
                filters.append(self.model.state == "active")
            # elif hasattr(self.model, "is_active"):
            #     filters.append(self.model.is_active == True)

        items, _ = await self.get_multi(filters=filters, limit=1_000_000)
        return items


if __name__ == "__main__":
    # Демонстраційний блок для BonusRuleRepository.
    print("--- Репозиторій Правил Нарахування Бонусів (BonusRuleRepository) ---")

    print("Для тестування BonusRuleRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    print(f"Він успадковує методи від BaseRepository для моделі {BonusRule.__name__}.")
    print(f"  Очікує схему створення: {BonusRuleCreateSchema.__name__}")
    print(f"  Очікує схему оновлення: {BonusRuleUpdateSchema.__name__}")

    print("\nСпецифічні методи:")
    print("  - get_rules_for_task(task_id: int, active_only: bool = True)")
    print("  - get_rules_for_event_task(event_task_id: int, active_only: bool = True)")

    print("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
    print("TODO: Узгодити логіку фільтрації 'active_only' з реальним полем стану в моделі BonusRule.")
    print("TODO: Уточнити використання `event_id` у `get_rules_for_event_task`.")
