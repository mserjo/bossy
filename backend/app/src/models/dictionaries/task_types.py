# backend/app/src/models/dictionaries/task_types.py

"""
Модель SQLAlchemy для таблиці-довідника 'TaskType'.
Ця таблиця зберігає різні типи або категорії завдань (наприклад, Домашнє завдання, Робочий елемент, Нагадування, Підтип події).
"""

import logging
from typing import Optional # Якщо додаються специфічні опціональні поля
from datetime import datetime, timezone # Для прикладу в __main__

from sqlalchemy.orm import Mapped, mapped_column # Якщо додаються специфічні поля
from sqlalchemy import Boolean, Integer # Якщо додаються специфічні поля

from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel

# Налаштувати логер для цього модуля
logger = logging.getLogger(__name__)

class TaskType(BaseDictionaryModel):
    """
    Представляє тип завдання в таблиці-довіднику (наприклад, Домашнє завдання, Робочий елемент, Помилка, Функція, Нагадування).
    Успадковує загальні поля від BaseDictionaryModel.

    Поле 'code' буде ключовим (наприклад, 'CHORE', 'WORK_ITEM', 'BUG').
    Поле 'description' може пояснювати, що зазвичай передбачає цей тип завдання.
    """
    __tablename__ = "dict_task_types"

    # Додайте будь-які поля, специфічні для 'TaskType', яких немає в BaseDictionaryModel.
    # Наприклад, прапорець, що вказує, чи завдання цього типу зазвичай нараховують бали:
    # awards_points_by_default: Mapped[bool] = mapped_column(
    #     Boolean,
    #     default=True,
    #     nullable=False,
    #     comment="Чи цей тип завдання зазвичай призводить до нарахування балів/бонусів після виконання?"
    # )
    # default_points_value: Mapped[Optional[int]] = mapped_column(
    #     Integer,
    #     nullable=True,
    #     comment="Значення балів за замовчуванням для завдань цього типу, якщо застосовно."
    # )

    def __repr__(self) -> str:
        return super().__repr__() # BaseDictionaryModel надає хороший стандартний __repr__

if __name__ == "__main__":
    # Цей блок призначений для демонстрації структури моделі TaskType.
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Модель довідника TaskType --- Демонстрація")

    # Приклади екземплярів TaskType
    chore_type = TaskType(
        code="CHORE",
        name="Домашнє завдання",
        description="Звичайне домашнє завдання або особисте доручення.",
        state="active",
        display_order=1
        # awards_points_by_default=True, # Якби поле було додано
        # default_points_value=10      # Якби поле було додано
    )
    chore_type.id = 1 # Імітація ID, встановленого ORM
    chore_type.created_at = datetime.now(timezone.utc) # Імітація часової мітки
    chore_type.updated_at = datetime.now(timezone.utc) # Імітація часової мітки
    logger.info(f"Приклад TaskType: {chore_type!r}, Опис: {chore_type.description}")
    # if hasattr(chore_type, 'awards_points_by_default'):
    #     logger.info(f"  Нараховує бали за замовчуванням: {chore_type.awards_points_by_default}")

    work_item_type = TaskType(
        code="WORK_ITEM",
        name="Робочий елемент",
        description="Завдання, пов'язане з професійною роботою або проектом.",
        state="active",
        display_order=2
        # awards_points_by_default=False # Якби поле було додано
    )
    work_item_type.id = 2
    work_item_type.created_at = datetime.now(timezone.utc)
    work_item_type.updated_at = datetime.now(timezone.utc)
    logger.info(f"Приклад TaskType: {work_item_type!r}, Назва: {work_item_type.name}")

    reminder_type = TaskType(
        code="REMINDER",
        name="Нагадування",
        description="Просте нагадування про майбутню подію або дію.",
        state="active",
        display_order=3,
        # awards_points_by_default=False # Якби поле було додано
    )
    reminder_type.id = 3
    reminder_type.created_at = datetime.now(timezone.utc)
    reminder_type.updated_at = datetime.now(timezone.utc)
    logger.info(f"Приклад TaskType: {reminder_type!r}, За замовчуванням: {reminder_type.is_default}") # is_default за замовчуванням False

    # Показати успадковані та специфічні атрибути (якщо такі були додані)
    # from sqlalchemy import create_engine
    # from backend.app.src.config.database import Base # Переконайтеся, що Base правильно імпортовано
    # engine = create_engine("sqlite:///:memory:")
    # Base.metadata.create_all(engine) # Це створить усі таблиці, визначені за допомогою цього Base
    # logger.info(f"Стовпці в TaskType ({TaskType.__tablename__}): {[c.name for c in TaskType.__table__.columns]}")
    logger.info("Щоб побачити фактичні стовпці таблиці, метадані SQLAlchemy потрібно ініціалізувати за допомогою engine (наприклад, Base.metadata.create_all(engine)).")
