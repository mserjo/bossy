# backend/app/src/models/dictionaries/user_types.py
"""
Модель SQLAlchemy для довідника "Типи користувачів".

Цей модуль визначає модель `UserType`, яка представляє записи в довіднику
типів користувачів (наприклад, "SUPERUSER", "REGULAR_USER", "BOT_USER"
відповідно до `core.dicts.UserType`, або "адмін", "звичайний користувач"
якщо це більш загальний довідник).
"""

# Абсолютний імпорт базової моделі для довідників
from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel


# Можливо, знадобляться додаткові імпорти, якщо будуть специфічні поля.
# from sqlalchemy.orm import Mapped, mapped_column
# from sqlalchemy import Boolean

class UserType(BaseDictionaryModel):
    """
    Модель SQLAlchemy для довідника "Типи користувачів".

    Успадковує всі поля від `BaseDictionaryModel` (включаючи `id`, `name`, `description`, `code`,
    часові мітки, м'яке видалення, стан, нотатки та опціональний `group_id`).
    `group_id` для системних типів користувачів, ймовірно, буде NULL.

    Атрибути:
        __tablename__ (str): Назва таблиці в базі даних (`dict_user_types`).
    """
    __tablename__ = "dict_user_types"

    # Якщо для типів користувачів потрібні специфічні додаткові поля,
    # наприклад, чи дозволено цьому типу користувача мати кілька груп,
    # їх можна визначити тут.
    # Наприклад:
    # can_own_multiple_groups: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="Чи може цей тип користувача володіти кількома групами")

    # _repr_fields успадковуються та збираються автоматично.
    # Додавання специфічних полів до __repr__:
    # _repr_fields = ["can_own_multiple_groups"]


if __name__ == "__main__":
    # Демонстраційний блок для моделі UserType.
    print("--- Модель Довідника: UserType ---")
    print(f"Назва таблиці: {UserType.__tablename__}")

    print("\nОчікувані поля (успадковані та власні):")
    expected_fields = ['id', 'name', 'description', 'code', 'created_at', 'updated_at', 'deleted_at', 'state',
                       'group_id', 'notes']
    # Якщо додано кастомні поля:
    # expected_fields.append('can_own_multiple_groups')
    for field in expected_fields:
        print(f"  - {field}")

    # Приклад створення екземпляра (без взаємодії з БД)
    example_user_type = UserType(
        id=1,
        name="Звичайний користувач",
        description="Стандартний тип користувача з базовими правами.",
        code="REGULAR_USER",  # Може відповідати значенням з core.dicts.UserType
        state="active"
    )

    print(f"\nПриклад екземпляра UserType (без сесії):\n  {example_user_type}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <UserType(id=1, name='Звичайний користувач', code='REGULAR_USER', state='active')>

    print("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
