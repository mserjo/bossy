# backend/app/src/models/dictionaries/calendars.py

"""
Модель SQLAlchemy для таблиці-довідника 'CalendarProvider'.
Ця таблиця зберігає різні календарні сервіси, з якими система може інтегруватися (наприклад, Google Calendar, Outlook Calendar).
"""

import logging
from typing import Optional # Якщо додаються специфічні опціональні поля
from datetime import datetime, timezone # Для прикладу в __main__

from sqlalchemy.orm import Mapped, mapped_column # Якщо додаються специфічні поля
from sqlalchemy import String # Якщо додаються специфічні поля

from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel

# Налаштувати логер для цього модуля
logger = logging.getLogger(__name__)

class CalendarProvider(BaseDictionaryModel):
    """
    Представляє постачальника календарних сервісів у таблиці-довіднику (наприклад, Google Calendar, Outlook Calendar, Apple Calendar).
    Успадковує загальні поля від BaseDictionaryModel.

    Поле 'code' буде важливим (наприклад, 'GOOGLE_CALENDAR', 'OUTLOOK_CALENDAR').
    Поле 'name' буде 'Google Calendar', 'Outlook Calendar'.
    """
    __tablename__ = "dict_calendar_providers"

    # Додайте будь-які поля, специфічні для 'CalendarProvider', яких немає в BaseDictionaryModel.
    # Наприклад, URL-адреса іконки для постачальника або підказки щодо конкретних кінцевих точок API (хоча фактичні кінцеві точки краще зберігати в конфігурації).
    # icon_url: Mapped[Optional[str]] = mapped_column(
    #     String(512),
    #     nullable=True,
    #     comment="URL-адреса іконки, що представляє цього постачальника календарів."
    # )
    # integration_docs_url: Mapped[Optional[str]] = mapped_column(
    #     String(512),
    #     nullable=True,
    #     comment="Посилання на документацію для інтеграції з цим постачальником."
    # )

    def __repr__(self) -> str:
        return super().__repr__() # BaseDictionaryModel надає хороший стандартний __repr__

if __name__ == "__main__":
    # Цей блок призначений для демонстрації структури моделі CalendarProvider.
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Модель довідника CalendarProvider --- Демонстрація")

    # Приклади екземплярів CalendarProvider
    google_calendar = CalendarProvider(
        code="GOOGLE_CALENDAR",
        name="Google Calendar",
        description="Інтеграція з Google Calendar для синхронізації завдань та подій.",
        state="active",
        display_order=1
        # icon_url="https://example.com/icons/google_calendar.png" # Якби поле було додано
    )
    google_calendar.id = 1 # Імітація ID, встановленого ORM
    google_calendar.created_at = datetime.now(timezone.utc) # Імітація часової мітки
    google_calendar.updated_at = datetime.now(timezone.utc) # Імітація часової мітки
    logger.info(f"Приклад CalendarProvider: {google_calendar!r}, Опис: {google_calendar.description}")
    # if hasattr(google_calendar, 'icon_url'):
    #     logger.info(f"  URL іконки: {google_calendar.icon_url}")

    outlook_calendar = CalendarProvider(
        code="OUTLOOK_CALENDAR",
        name="Outlook Calendar",
        description="Інтеграція з Outlook Calendar.",
        state="active",
        display_order=2
    )
    outlook_calendar.id = 2
    outlook_calendar.created_at = datetime.now(timezone.utc)
    outlook_calendar.updated_at = datetime.now(timezone.utc)
    logger.info(f"Приклад CalendarProvider: {outlook_calendar!r}, Назва: {outlook_calendar.name}")

    # Показати успадковані та специфічні атрибути (якщо такі були додані)
    # from sqlalchemy import create_engine
    # from backend.app.src.config.database import Base # Переконайтеся, що Base правильно імпортовано
    # engine = create_engine("sqlite:///:memory:")
    # Base.metadata.create_all(engine) # Це створить усі таблиці, визначені за допомогою цього Base
    # logger.info(f"Стовпці в CalendarProvider ({CalendarProvider.__tablename__}): {[c.name for c in CalendarProvider.__table__.columns]}")
    logger.info("Щоб побачити фактичні стовпці таблиці, метадані SQLAlchemy потрібно ініціалізувати за допомогою engine (наприклад, Base.metadata.create_all(engine)).")
