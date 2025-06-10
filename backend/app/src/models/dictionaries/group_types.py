# backend/app/src/models/dictionaries/group_types.py
"""
Модель SQLAlchemy для довідника "Типи груп".

Цей модуль визначає модель `GroupType`, яка представляє записи в довіднику
типів груп (наприклад, "Сім'я", "Відділ", "Організація"
відповідно до `core.dicts.GroupType` або технічного завдання).
"""

# Абсолютний імпорт базової моделі для довідників
from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel


# Можливо, знадобляться додаткові імпорти, якщо будуть специфічні поля.
# from sqlalchemy.orm import Mapped, mapped_column
# from sqlalchemy import Integer

class GroupType(BaseDictionaryModel):
    """
    Модель SQLAlchemy для довідника "Типи груп".

    Успадковує всі поля від `BaseDictionaryModel` (включаючи `id`, `name`, `description`, `code`,
    часові мітки, м'яке видалення, стан, нотатки та опціональний `group_id`).
    `group_id` для системних типів груп, ймовірно, буде NULL.

    Атрибути:
        __tablename__ (str): Назва таблиці в базі даних (`dict_group_types`).
    """
    __tablename__ = "dict_group_types"

    # Якщо для типів груп потрібні специфічні додаткові поля,
    # наприклад, максимальна кількість учасників за замовчуванням для цього типу групи,
    # їх можна визначити тут.
    # Наприклад:
    # default_max_members: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="Макс. учасників за замовчуванням")

    # _repr_fields успадковуються та збираються автоматично.
    # Додавання специфічних полів до __repr__:
    # _repr_fields = ["default_max_members"]


if __name__ == "__main__":
    # Демонстраційний блок для моделі GroupType.
    print("--- Модель Довідника: GroupType ---")
    print(f"Назва таблиці: {GroupType.__tablename__}")

    print("\nОчікувані поля (успадковані та власні):")
    expected_fields = ['id', 'name', 'description', 'code', 'created_at', 'updated_at', 'deleted_at', 'state',
                       'group_id', 'notes']
    # Якщо додано кастомні поля:
    # expected_fields.append('default_max_members')
    for field in expected_fields:
        print(f"  - {field}")

    # Приклад створення екземпляра (без взаємодії з БД)
    example_group_type = GroupType(
        id=1,
        name="Сім'я",
        description="Група для сімейного використання, з відповідними налаштуваннями приватності.",
        code="FAMILY",  # Може відповідати значенням з core.dicts.GroupType
        state="active"
    )

    print(f"\nПриклад екземпляра GroupType (без сесії):\n  {example_group_type}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <GroupType(id=1, name='Сім'я', code='FAMILY', state='active')>

    print("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
