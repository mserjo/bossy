# backend/app/src/models/dictionaries/bonus_types.py
# -*- coding: utf-8 -*-
"""
Модель SQLAlchemy для довідника "Типи бонусів".

Цей модуль визначає модель `BonusType`, яка представляє записи в довіднику
типів бонусів (наприклад, "Нагорода", "Штраф"
відповідно до `core.dicts.BonusType` або технічного завдання).
Ці типи визначають характер бонусної транзакції.
"""

# Абсолютний імпорт базової моделі для довідників
from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

# Можливо, знадобляться додаткові імпорти, якщо будуть специфічні поля.
# from sqlalchemy.orm import Mapped, mapped_column
# from sqlalchemy import Float

class BonusType(BaseDictionaryModel):
    """
    Модель SQLAlchemy для довідника "Типи бонусів".

    Успадковує всі поля від `BaseDictionaryModel` (включаючи `id`, `name`, `description`, `code`,
    часові мітки, м'яке видалення, стан, нотатки та опціональний `group_id`).
    `group_id` для системних типів бонусів, ймовірно, буде NULL.

    Атрибути:
        __tablename__ (str): Назва таблиці в базі даних (`dict_bonus_types`).
    """
    __tablename__ = "dict_bonus_types"

    # Якщо для типів бонусів потрібні специфічні додаткові поля,
    # наприклад, множник за замовчуванням для цього типу бонусу,
    # їх можна визначити тут.
    # Наприклад:
    # default_multiplier: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="Множник за замовчуванням (наприклад, -1 для штрафів)")

    # _repr_fields успадковуються та збираються автоматично з BaseDictionaryModel (id, name, code, state_id тощо).
    # Немає додаткових специфічних полів для __repr__ на цьому рівні.
    _repr_fields: tuple[str, ...] = ()


if __name__ == "__main__":
    # Демонстраційний блок для моделі BonusType.
    logger.info("--- Модель Довідника: BonusType ---")
    logger.info(f"Назва таблиці: {BonusType.__tablename__}")

    logger.info("\nОчікувані поля (успадковані та власні):")
    expected_fields = ['id', 'name', 'description', 'code', 'created_at', 'updated_at', 'deleted_at', 'state',
                       'group_id', 'notes']
    # Якщо додано кастомні поля:
    # expected_fields.append('default_multiplier')
    for field in expected_fields:
        logger.info(f"  - {field}")

    # Приклад створення екземпляра (без взаємодії з БД)
    example_bonus_type = BonusType(
        id=1,
        name="Нагорода за завдання",
        description="Стандартний тип бонусу за виконання завдання.",
        code="REWARD",  # Може відповідати значенням з core.dicts.BonusType
        state="active"
    )

    logger.info(f"\nПриклад екземпляра BonusType (без сесії):\n  {example_bonus_type}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <BonusType(id=1, name='Нагорода за завдання', code='REWARD', state='active')>

    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
