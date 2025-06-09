# backend/app/src/models/dictionaries/statuses.py

"""
Модель SQLAlchemy для таблиці-довідника 'Status'.
Ця таблиця може зберігати різні статуси, що використовуються в програмі (наприклад, статус завдання, статус користувача).
"""

import logging
from typing import Optional # Для Mapped[Optional[str]], якщо якесь поле є опціональним
from datetime import datetime, timezone # Для прикладу в __main__

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String # Приклад, якщо додаються специфічні поля, яких немає в базовій моделі

from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel

# Налаштувати логер для цього модуля
logger = logging.getLogger(__name__)

class Status(BaseDictionaryModel):
    """
    Представляє запис статусу в таблиці-довіднику.
    Успадковує загальні поля (id, code, name, description, state, is_default, display_order тощо)
    від BaseDictionaryModel.

    Цю модель можна використовувати для визначення статусів для різних сутностей, таких як завдання, користувачі, замовлення тощо.
    Поле 'state' з BaseDictionaryModel можна використовувати для подальшої категоризації статусів
    (наприклад, статус з кодом 'COMPLETED' може мати стан 'final').
    """
    __tablename__ = "dict_statuses" # Явне іменування таблиць-довідників з префіксом може бути хорошою практикою

    # Додайте будь-які поля, специфічні для 'Status', яких немає в BaseDictionaryModel.
    # Наприклад, ви можете захотіти пов'язати колір зі статусом для цілей UI:
    # color_hex: Mapped[Optional[str]] = mapped_column(String(7), comment="Шістнадцятковий код кольору для відображення в UI (наприклад, #FF0000)")

    # Або поле для категоризації самого статусу, якщо 'state' у BaseDictionaryModel використовується інакше:
    # category: Mapped[Optional[str]] = mapped_column(String(100), index=True, comment="Категорія, до якої належить цей статус (наприклад, 'TaskWorkflow', 'UserLifecycle')")

    def __repr__(self) -> str:
        # BaseDictionaryModel вже надає хороший __repr__
        # Ви можете перевизначити його, якщо хочете включити більше полів, специфічних для Status
        return super().__repr__()

if __name__ == "__main__":
    # Цей блок призначений для демонстрації структури моделі Status.
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Модель довідника Status --- Демонстрація")

    # Приклад екземпляра Status
    active_status = Status(
        code="ACTIVE",
        name="Активний",
        description="Вказує, що сутність наразі активна та функціонує.",
        state="enabled", # Приклад використання поля 'state' з BaseDictionaryModel
        is_default=True,
        display_order=1,
        # color_hex="#00FF00" # Якби поле 'color_hex' було додано
    )
    # Імітація полів, встановлених ORM, для демонстрації
    active_status.id = 1
    active_status.created_at = datetime.now(timezone.utc) # Імітація часової мітки
    active_status.updated_at = datetime.now(timezone.utc) # Імітація часової мітки

    logger.info(f"Приклад екземпляра Status: {active_status!r}")
    logger.info(f"  Код: {active_status.code}")
    logger.info(f"  Назва: {active_status.name}")
    logger.info(f"  Опис: {active_status.description}")
    logger.info(f"  Стан: {active_status.state}")
    logger.info(f"  За замовчуванням: {active_status.is_default}")
    logger.info(f"  Порядок відображення: {active_status.display_order}")
    # logger.info(f"  Колір: {active_status.color_hex}") # Якби поле 'color_hex' було додано
    logger.info(f"  Створено: {active_status.created_at.isoformat() if active_status.created_at else 'N/A'}")


    pending_status = Status(
        code="PENDING_APPROVAL",
        name="Очікує затвердження",
        description="Елемент очікує на затвердження, перш ніж стати активним.",
        state="awaiting_action",
        display_order=2
    )
    pending_status.id = 2
    pending_status.created_at = datetime.now(timezone.utc)
    pending_status.updated_at = datetime.now(timezone.utc)
    logger.info(f"Інший екземпляр Status: {pending_status!r}")
    logger.info(f"  За замовчуванням (не встановлено, за замовчуванням False через Mapped): {pending_status.is_default}")


    # Показати успадковані та специфічні атрибути
    # Щоб перевірити фактичні стовпці, вам потрібно було б ініціалізувати Base.metadata за допомогою engine
    # from sqlalchemy import create_engine
    # from backend.app.src.config.database import Base # Переконайтеся, що Base правильно імпортовано
    # engine = create_engine("sqlite:///:memory:")
    # Base.metadata.create_all(engine) # Це створить усі таблиці, визначені за допомогою цього Base
    # logger.info(f"Стовпці в Status ({Status.__tablename__}): {[c.name for c in Status.__table__.columns]}")
    # Очікувані стовпці: id, created_at, updated_at, name, description, state, deleted_at, notes, code, is_default, display_order
    # Плюс будь-які власні поля, такі як 'color_hex' або 'category', якщо додано.
    logger.info("Щоб побачити фактичні стовпці таблиці, метадані SQLAlchemy потрібно ініціалізувати за допомогою engine (наприклад, Base.metadata.create_all(engine)).")
