# backend/app/src/models/dictionaries/bonus_types.py

"""
Модель SQLAlchemy для таблиці-довідника 'BonusType'.
Ця таблиця зберігає різні типи або категорії бонусів чи штрафів
(наприклад, БонусЗаВиконанняЗавдання, БонусЗаЗавчаснеВиконання, ШтрафЗаПізнєПодання).
"""

import logging
from typing import Optional # Якщо додаються специфічні опціональні поля
from datetime import datetime, timezone # Для прикладу в __main__

from sqlalchemy.orm import Mapped, mapped_column # Якщо додаються специфічні поля
from sqlalchemy import Boolean, Integer # Якщо додаються специфічні поля

from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel

# Налаштувати логер для цього модуля
logger = logging.getLogger(__name__)

class BonusType(BaseDictionaryModel):
    """
    Представляє тип бонусу або штрафу в таблиці-довіднику.
    Приклади: Завершення завдання, Бонус за серію, Штраф за запізнення, Реферальний бонус.
    Успадковує загальні поля від BaseDictionaryModel.

    Поле 'code' буде важливим (наприклад, 'TASK_COMPLETION', 'STREAK_7_DAYS', 'LATE_PENALTY').
    """
    __tablename__ = "dict_bonus_types"

    # Додайте будь-які поля, специфічні для 'BonusType', яких немає в BaseDictionaryModel.
    # Наприклад, чи є цей тип зазвичай бонусом (позитивні бали) чи штрафом (негативні бали).
    # is_penalty_type: Mapped[bool] = mapped_column(
    #     Boolean,
    #     default=False,
    #     nullable=False,
    #     comment="True, якщо цей тип зазвичай призводить до негативних балів (штраф)."
    # )
    # default_point_impact: Mapped[Optional[int]] = mapped_column(
    #     Integer,
    #     nullable=True,
    #     comment="Кількість балів за замовчуванням, що нараховуються або знімаються для цього типу бонусу. Може бути перевизначено конкретним BonusRule."
    # )

    def __repr__(self) -> str:
        return super().__repr__() # BaseDictionaryModel надає хороший стандартний __repr__

if __name__ == "__main__":
    # Цей блок призначений для демонстрації структури моделі BonusType.
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Модель довідника BonusType --- Демонстрація")

    # Приклади екземплярів BonusType
    task_completion_bonus = BonusType(
        code="TASK_COMPLETION",
        name="Бонус за виконання завдання",
        description="Стандартний бонус, що нараховується за успішне виконання завдання.",
        state="active",
        display_order=1
        # is_penalty_type=False, # Якби поле було додано
        # default_point_impact=20 # Якби поле було додано
    )
    task_completion_bonus.id = 1 # Імітація ID, встановленого ORM
    task_completion_bonus.created_at = datetime.now(timezone.utc) # Імітація часової мітки
    task_completion_bonus.updated_at = datetime.now(timezone.utc) # Імітація часової мітки
    logger.info(f"Приклад BonusType: {task_completion_bonus!r}, Опис: {task_completion_bonus.description}")
    # if hasattr(task_completion_bonus, 'is_penalty_type'):
    #     logger.info(f"  Чи є типом штрафу: {task_completion_bonus.is_penalty_type}")

    late_penalty = BonusType(
        code="LATE_SUBMISSION_PENALTY",
        name="Штраф за пізнє подання",
        description="Штраф, що застосовується за подання завдання після встановленого терміну.",
        state="active",
        display_order=10
        # is_penalty_type=True, # Якби поле було додано
        # default_point_impact=-5 # Якби поле було додано
    )
    late_penalty.id = 2
    late_penalty.created_at = datetime.now(timezone.utc)
    late_penalty.updated_at = datetime.now(timezone.utc)
    logger.info(f"Приклад BonusType: {late_penalty!r}, Назва: {late_penalty.name}")

    streak_bonus = BonusType(
        code="STREAK_BONUS_7_DAY",
        name="Бонус за 7-денну серію",
        description="Бонус за послідовне виконання завдань протягом 7 днів.",
        state="active",
        display_order=3
    )
    streak_bonus.id = 3
    streak_bonus.created_at = datetime.now(timezone.utc)
    streak_bonus.updated_at = datetime.now(timezone.utc)
    logger.info(f"Приклад BonusType: {streak_bonus!r}, За замовчуванням: {streak_bonus.is_default}") # is_default за замовчуванням False

    # Показати успадковані та специфічні атрибути (якщо такі були додані)
    # from sqlalchemy import create_engine
    # from backend.app.src.config.database import Base # Переконайтеся, що Base правильно імпортовано
    # engine = create_engine("sqlite:///:memory:")
    # Base.metadata.create_all(engine) # Це створить усі таблиці, визначені за допомогою цього Base
    # logger.info(f"Стовпці в BonusType ({BonusType.__tablename__}): {[c.name for c in BonusType.__table__.columns]}")
    logger.info("Щоб побачити фактичні стовпці таблиці, метадані SQLAlchemy потрібно ініціалізувати за допомогою engine (наприклад, Base.metadata.create_all(engine)).")
