# backend/app/src/models/dictionaries/statuses.py
"""
Модель SQLAlchemy для довідника "Статуси".

Цей модуль визначає модель `Status`, яка представляє записи в довіднику статусів.
Статуси можуть використовуватися для різних сутностей в системі, наприклад,
для завдань, користувачів, груп тощо, якщо для них не передбачено окремих Enum-станів.
"""

from sqlalchemy.orm import Mapped  # Mapped тут не потрібен, якщо немає нових полів

# Абсолютний імпорт базової моделі для довідників
from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel


class Status(BaseDictionaryModel):
    """
    Модель SQLAlchemy для довідника "Статуси".

    Успадковує всі поля від `BaseDictionaryModel` (включаючи `id`, `name`, `description`, `code`,
    часові мітки, м'яке видалення, стан, нотатки та опціональний `group_id`).

    Атрибути:
        __tablename__ (str): Назва таблиці в базі даних (`dict_statuses`).
    """
    __tablename__ = "dict_statuses"

    # Якщо для статусів потрібні специфічні додаткові поля, їх можна визначити тут.
    # Наприклад:
    # color_representation: Mapped[Optional[str]] = mapped_column(String(7), comment="Колір для візуального представлення статусу (HEX)")

    # _repr_fields успадковуються та збираються автоматично.
    # Якщо потрібно додати специфічні для Status поля до __repr__, можна визначити:
    # _repr_fields = ["color_representation"] # Це додасться до полів з BaseDictionaryModel


if __name__ == "__main__":
    # Демонстраційний блок для моделі Status.
    print("--- Модель Довідника: Status ---")

    # Інформація про таблицю та колонки (потребує відображення SQLAlchemy)
    # Для простої демонстрації, ми виведемо очікувані поля.
    print(f"Назва таблиці: {Status.__tablename__}")

    print("\nОчікувані поля (успадковані та власні):")
    expected_fields = ['id', 'name', 'description', 'code', 'created_at', 'updated_at', 'deleted_at', 'state',
                       'group_id', 'notes']
    # Якщо додано кастомні поля, наприклад, color_representation, їх теж сюди:
    # expected_fields.append('color_representation')
    for field in expected_fields:
        print(f"  - {field}")

    # Приклад створення екземпляра (без взаємодії з БД)
    # У реальному коді це робиться через сесію SQLAlchemy.
    example_status = Status(
        id=1,  # Зазвичай встановлюється БД
        name="Активний",
        description="Статус для активних елементів системи.",
        code="ACTIVE",
        state="enabled"  # Наприклад, сам запис довідника може бути 'enabled' або 'deprecated'
    )

    print(f"\nПриклад екземпляра Status (без сесії):\n  {example_status}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <Status(id=1, name='Активний', code='ACTIVE', state='enabled')>
    # (created_at, updated_at і т.д. будуть None, якщо не встановлені вручну або через БД)

    print("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
