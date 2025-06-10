# backend/app/src/models/dictionaries/calendars.py
"""
Модель SQLAlchemy для довідника "Календарі" (постачальники календарів).

Цей модуль визначає модель `CalendarProvider`, яка представляє записи
в довіднику постачальників календарів, з якими система може інтегруватися
(наприклад, Google Calendar, Outlook Calendar).
"""

# Абсолютний імпорт базової моделі для довідників
from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel


# Можливо, знадобляться додаткові імпорти, якщо будуть специфічні поля.
# from sqlalchemy.orm import Mapped, mapped_column
# from sqlalchemy import String

class CalendarProvider(BaseDictionaryModel):
    """
    Модель SQLAlchemy для довідника "Постачальники календарів".

    Успадковує всі поля від `BaseDictionaryModel` (включаючи `id`, `name`, `description`, `code`,
    часові мітки, м'яке видалення, стан, нотатки та опціональний `group_id`).
    `group_id` для цього типу довідника, ймовірно, буде NULL, оскільки це системний довідник.

    Атрибути:
        __tablename__ (str): Назва таблиці в базі даних (`dict_calendar_providers`).
    """
    __tablename__ = "dict_calendar_providers"

    # Якщо для постачальників календарів потрібні специфічні додаткові поля,
    # наприклад, URL API для інтеграції або іконка постачальника,
    # їх можна визначити тут.
    # Наприклад:
    # api_endpoint_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="Базовий URL API постачальника")
    # icon_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="URL іконки постачальника")

    # _repr_fields успадковуються та збираються автоматично.
    # Додавання специфічних полів до __repr__:
    # _repr_fields = ["api_endpoint_url"]


if __name__ == "__main__":
    # Демонстраційний блок для моделі CalendarProvider.
    print("--- Модель Довідника: CalendarProvider ---")
    print(f"Назва таблиці: {CalendarProvider.__tablename__}")

    print("\nОчікувані поля (успадковані та власні):")
    expected_fields = ['id', 'name', 'description', 'code', 'created_at', 'updated_at', 'deleted_at', 'state',
                       'group_id', 'notes']
    # Якщо додано кастомні поля:
    # expected_fields.extend(['api_endpoint_url', 'icon_url'])
    for field in expected_fields:
        print(f"  - {field}")

    # Приклад створення екземпляра (без взаємодії з БД)
    example_calendar_provider = CalendarProvider(
        id=1,
        name="Google Calendar",
        description="Інтеграція з Google Calendar для синхронізації завдань та подій.",
        code="GOOGLE_CALENDAR",
        state="active"
    )

    print(f"\nПриклад екземпляра CalendarProvider (без сесії):\n  {example_calendar_provider}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <CalendarProvider(id=1, name='Google Calendar', code='GOOGLE_CALENDAR', state='active')>

    print("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
