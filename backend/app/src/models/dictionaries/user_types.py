# backend/app/src/models/dictionaries/user_types.py

"""
Модель SQLAlchemy для таблиці-довідника 'UserType'.
Ця таблиця може зберігати різні класифікації користувачів (наприклад, Людина, Бот, Система).
"""

import logging
from typing import Optional # Для Mapped[Optional[...]], якщо якесь поле є опціональним
from datetime import datetime, timezone # Для прикладу в __main__

from sqlalchemy.orm import Mapped, mapped_column # Якщо додаються специфічні поля
from sqlalchemy import Boolean # Якщо додаються специфічні поля, такі як can_login_via_ui

from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel

# Налаштувати логер для цього модуля
logger = logging.getLogger(__name__)

class UserType(BaseDictionaryModel):
    """
    Представляє тип користувача в таблиці-довіднику (наприклад, Людина, Бот, Система, Сервісний обліковий запис).
    Успадковує загальні поля від BaseDictionaryModel.

    Поле 'code' буде важливим (наприклад, 'HUMAN', 'BOT', 'SYSTEM').
    Поле 'description' може уточнювати призначення або природу типу користувача.
    """
    __tablename__ = "dict_user_types"

    # Додайте будь-які поля, специфічні для 'UserType', яких немає в BaseDictionaryModel.
    # Наприклад, прапорець, що вказує, чи може цей тип користувача входити через UI:
    # can_login_via_ui: Mapped[bool] = mapped_column(
    #     Boolean,
    #     default=True,
    #     nullable=False,
    #     comment="Вказує, чи можуть користувачі цього типу зазвичай входити через користувацький інтерфейс."
    # )

    def __repr__(self) -> str:
        return super().__repr__() # BaseDictionaryModel надає хороший стандартний __repr__

if __name__ == "__main__":
    # Цей блок призначений для демонстрації структури моделі UserType.
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Модель довідника UserType --- Демонстрація")

    # Приклади екземплярів UserType
    human_user_type = UserType(
        code="HUMAN",
        name="Людина-користувач",
        description="Звичайний користувач-людина, що взаємодіє з системою.",
        state="active",
        display_order=1
        # can_login_via_ui=True # Якби поле було додано
    )
    human_user_type.id = 1 # Імітація ID, встановленого ORM
    human_user_type.created_at = datetime.now(timezone.utc) # Імітація часової мітки
    human_user_type.updated_at = datetime.now(timezone.utc) # Імітація часової мітки
    logger.info(f"Приклад UserType: {human_user_type!r}, Опис: {human_user_type.description}")
    # if hasattr(human_user_type, 'can_login_via_ui'):
    #     logger.info(f"  Може входити через UI: {human_user_type.can_login_via_ui}")

    bot_user_type = UserType(
        code="BOT_SERVICE",
        name="Бот/Сервісний обліковий запис",
        description="Автоматизований агент або сервісний обліковий запис, що виконує дії.",
        state="active",
        display_order=2
        # can_login_via_ui=False # Якби поле було додано
    )
    bot_user_type.id = 2
    bot_user_type.created_at = datetime.now(timezone.utc)
    bot_user_type.updated_at = datetime.now(timezone.utc)
    logger.info(f"Приклад UserType: {bot_user_type!r}, Назва: {bot_user_type.name}")

    system_user_type = UserType(
        code="SYSTEM_INTERNAL",
        name="Внутрішній системний користувач",
        description="Внутрішній системний користувач для автоматизованих процесів, не пов'язаних безпосередньо з ботом (наприклад, Тіньовий користувач для cron-завдань).",
        state="active",
        display_order=3
        # can_login_via_ui=False # Якби поле було додано
    )
    system_user_type.id = 3
    system_user_type.created_at = datetime.now(timezone.utc)
    system_user_type.updated_at = datetime.now(timezone.utc)
    logger.info(f"Приклад UserType: {system_user_type!r}, За замовчуванням: {system_user_type.is_default}") # is_default за замовчуванням False

    # Показати успадковані та специфічні атрибути (якщо такі були додані)
    # from sqlalchemy import create_engine
    # from backend.app.src.config.database import Base # Переконайтеся, що Base правильно імпортовано
    # engine = create_engine("sqlite:///:memory:")
    # Base.metadata.create_all(engine) # Це створить усі таблиці, визначені за допомогою цього Base
    # logger.info(f"Стовпці в UserType ({UserType.__tablename__}): {[c.name for c in UserType.__table__.columns]}")
    logger.info("Щоб побачити фактичні стовпці таблиці, метадані SQLAlchemy потрібно ініціалізувати за допомогою engine (наприклад, Base.metadata.create_all(engine)).")
