# backend/app/src/models/dictionaries/group_types.py

"""
Модель SQLAlchemy для таблиці-довідника 'GroupType'.
Ця таблиця зберігає різні типи або категорії груп (наприклад, Сім'я, Відділ, Організація).
"""

import logging
from typing import Optional # Якщо додаються специфічні опціональні поля
from datetime import datetime, timezone # Для прикладу в __main__

from sqlalchemy.orm import Mapped, mapped_column # Якщо додаються специфічні поля
from sqlalchemy import Integer, Boolean # Якщо додаються специфічні поля, такі як default_max_members

from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel

# Налаштувати логер для цього модуля
logger = logging.getLogger(__name__)

class GroupType(BaseDictionaryModel):
    """
    Представляє тип групи в таблиці-довіднику (наприклад, Сім'я, Команда, Відділ, Організація).
    Успадковує загальні поля від BaseDictionaryModel.

    Поле 'code' буде важливим (наприклад, 'FAMILY', 'TEAM', 'DEPARTMENT').
    Поле 'description' може уточнювати типовий випадок використання або характеристики цього типу групи.
    """
    __tablename__ = "dict_group_types"

    # Додайте будь-які поля, специфічні для 'GroupType', яких немає в BaseDictionaryModel.
    # Наприклад, ви можете захотіти вказати дозволи за замовчуванням або функції, увімкнені для цього типу групи:
    # default_max_members: Mapped[Optional[int]] = mapped_column(
    #     Integer,
    #     nullable=True,
    #     comment="Максимальна кількість учасників за замовчуванням для груп цього типу (може бути перевизначено на рівні групи)."
    # )
    # allows_subgroups: Mapped[bool] = mapped_column(
    #     Boolean,
    #     default=False,
    #     nullable=False,
    #     comment="Чи можуть групи цього типу мати підгрупи."
    # )

    def __repr__(self) -> str:
        return super().__repr__() # BaseDictionaryModel надає хороший стандартний __repr__

if __name__ == "__main__":
    # Цей блок призначений для демонстрації структури моделі GroupType.
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Модель довідника GroupType --- Демонстрація")

    # Приклади екземплярів GroupType
    family_type = GroupType(
        code="FAMILY",
        name="Сім'я",
        description="Група для членів сім'ї для обміну завданнями та винагородами.",
        state="active",
        display_order=1
        # default_max_members=10, # Якби поле було додано
        # allows_subgroups=False   # Якби поле було додано
    )
    family_type.id = 1 # Імітація ID, встановленого ORM
    family_type.created_at = datetime.now(timezone.utc) # Імітація часової мітки
    family_type.updated_at = datetime.now(timezone.utc) # Імітація часової мітки
    logger.info(f"Приклад GroupType: {family_type!r}, Опис: {family_type.description}")
    # if hasattr(family_type, 'default_max_members'):
    #     logger.info(f"  Макс. учасників за замовчуванням: {family_type.default_max_members}")

    department_type = GroupType(
        code="DEPARTMENT",
        name="Відділ",
        description="Група, що представляє відділ в організації.",
        state="active",
        display_order=2
    )
    department_type.id = 2
    department_type.created_at = datetime.now(timezone.utc)
    department_type.updated_at = datetime.now(timezone.utc)
    logger.info(f"Приклад GroupType: {department_type!r}, Назва: {department_type.name}")

    organization_type = GroupType(
        code="ORGANIZATION",
        name="Організація",
        description="Група верхнього рівня, що представляє всю організацію.",
        state="active",
        display_order=3,
        # allows_subgroups=True # Якби поле було додано
    )
    organization_type.id = 3
    organization_type.created_at = datetime.now(timezone.utc)
    organization_type.updated_at = datetime.now(timezone.utc)
    logger.info(f"Приклад GroupType: {organization_type!r}, За замовчуванням: {organization_type.is_default}")

    # Показати успадковані та специфічні атрибути (якщо такі були додані)
    # from sqlalchemy import create_engine
    # from backend.app.src.config.database import Base # Переконайтеся, що Base правильно імпортовано
    # engine = create_engine("sqlite:///:memory:")
    # Base.metadata.create_all(engine) # Це створить усі таблиці, визначені за допомогою цього Base
    # logger.info(f"Стовпці в GroupType ({GroupType.__tablename__}): {[c.name for c in GroupType.__table__.columns]}")
    logger.info("Щоб побачити фактичні стовпці таблиці, метадані SQLAlchemy потрібно ініціалізувати за допомогою engine (наприклад, Base.metadata.create_all(engine)).")
