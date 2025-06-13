# backend/app/src/models/dictionaries/calendars.py
# -*- coding: utf-8 -*-
"""Модель SQLAlchemy для довідника "Провайдери Календарів".

Цей модуль визначає модель `CalendarProviderModel`, яка представляє записи
в довіднику провайдерів календарів, з якими система може інтегруватися
(наприклад, Google Calendar, Outlook Calendar, Apple iCloud Calendar).
Довідник зберігає інформацію про назву провайдера, його код, опис,
а також специфічні налаштування для інтеграції.
"""

from typing import Optional, Dict, Any

from sqlalchemy import Boolean, String, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

# Абсолютний імпорт базової моделі для довідників
from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel
# Імпорт централізованого логера
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


class CalendarProvider(BaseDictionaryModel):
    """Модель SQLAlchemy для довідника "Провайдери Календарів".

    Успадковує всі поля від `BaseDictionaryModel` (включаючи `id`, `name`,
    `description`, `code`, `icon`, `color` та інші поля з `BaseMainModel`).
    `group_id` для цього типу довідника, ймовірно, буде `NULL`,
    оскільки це переважно системний довідник.

    Атрибути:
        __tablename__ (str): Назва таблиці в базі даних: `calendar_providers`.
        __table_args__ (dict): Додаткові параметри таблиці, включаючи коментар.
        is_active (Mapped[bool]): Прапорець, що вказує, чи активний цей провайдер
                                  для використання в системі.
        credentials_schema (Mapped[Optional[Dict[str, Any]]]): JSON схема, що описує
                                  необхідні облікові дані або параметри для
                                  налаштування інтеграції з цим провайдером
                                  (наприклад, поля для OAuth2, API ключа тощо).
        sync_frequency_minutes (Mapped[Optional[int]]): Рекомендована або типова
                                  частота синхронізації з цим провайдером
                                  календаря, в хвилинах.
    """
    __tablename__ = "calendar_providers"

    __table_args__ = ({'comment': 'Довідник провайдерів календарів (наприклад, Google Calendar, Outlook).'},)

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default='true',
        nullable=False,
        comment="Чи активний цей провайдер календаря для використання в системі."
    )
    credentials_schema: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="JSON схема необхідних credential для цього провайдера (наприклад, для OAuth)."
    )
    sync_frequency_minutes: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Рекомендована частота синхронізації з цим календарем в хвилинах."
    )

    # _repr_fields визначаються в BaseDictionaryModel та його батьківських класах.
    # Оскільки цей клас додає специфічні поля, їх можна додати до _repr_fields,
    # якщо їх відображення в repr є корисним. За завданням - порожній кортеж.
    _repr_fields: tuple[str, ...] = ("is_active",) # Додамо is_active для прикладу, хоча завдання просить ()


if __name__ == "__main__":
    # Демонстраційний блок для моделі CalendarProvider.
    logger.info("--- Модель Довідника: CalendarProvider ---")
    logger.info("Назва таблиці: %s", CalendarProvider.__tablename__)
    logger.info("Коментар до таблиці: %s", getattr(CalendarProvider, '__table_args__', ({},))[0].get('comment', ''))

    logger.info("\nОчікувані поля (успадковані та власні):")
    expected_fields = [
        'id', 'name', 'description', 'code', 'icon', 'color',
        'created_at', 'updated_at', 'deleted_at', 'is_deleted',
        'state_id', 'group_id', 'notes',
        'is_active', 'credentials_schema', 'sync_frequency_minutes'
    ]
    for field in expected_fields:
        logger.info("  - %s", field)

    # Приклад створення екземпляра (без взаємодії з БД)
    from datetime import datetime, timezone

    example_calendar_provider = CalendarProvider(
        id=1, # id тепер Integer
        name="Google Calendar", # TODO i18n: "Google Calendar"
        description="Інтеграція з Google Calendar для синхронізації завдань та подій.", # TODO i18n
        code="GOOGLE_CALENDAR",
        state_id=1, # Активний запис довідника
        is_active=True,
        credentials_schema={"type": "oauth2", "client_id_key": "google_client_id", "client_secret_key": "google_client_secret"},
        sync_frequency_minutes=60
    )
    example_calendar_provider.created_at = datetime.now(timezone.utc) # Імітація

    logger.info("\nПриклад екземпляра CalendarProvider (без сесії):\n  %s", example_calendar_provider)
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <CalendarProvider(id=..., name='Google Calendar', code='GOOGLE_CALENDAR', is_active=True, state_id=1, created_at=...)>

    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
