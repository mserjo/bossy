# backend/app/src/models/gamification/level.py
"""
Модель SQLAlchemy для сутності "Рівень" (Level) в системі гейміфікації.

Цей модуль визначає модель `Level`, яка представляє різні рівні,
яких користувачі можуть досягати в межах групи на основі накопичених балів
або інших критеріїв.
"""
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, ForeignKey, Integer  # Integer для level_number
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Абсолютний імпорт базової моделі
from backend.app.src.models.base import BaseMainModel  # Включає id, name, description, state, group_id, etc.

if TYPE_CHECKING:
    from backend.app.src.models.groups.group import Group
    # from backend.app.src.models.gamification.user_level import UserLevel # Для зворотнього зв'язку, якщо потрібен


class Level(BaseMainModel):
    """
    Модель Рівня Гейміфікації.

    Успадковує `BaseMainModel` (id, name, description, state, group_id, notes, timestamps, soft_delete).
    Поле `name` - назва рівня (наприклад, "Новачок", "Експерт").
    Поле `description` - опис того, що означає цей рівень.
    Поле `state` - чи активний цей рівень для досягнення.
    Поле `group_id` - вказує, до якої групи належить цей рівень (якщо NULL - системний/глобальний рівень).

    Атрибути:
        required_points (Mapped[int]): Кількість балів, необхідна для досягнення цього рівня.
        level_number (Mapped[Optional[int]]): Порядковий номер рівня для сортування та відображення прогресу.
        icon_url (Mapped[Optional[str]]): URL або шлях до іконки рівня.

        group (Mapped[Optional["Group"]]): Зв'язок з групою, до якої належить рівень.
    """
    __tablename__ = "gamification_levels"

    # --- Специфічні поля для Рівня ---
    required_points: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Кількість балів, необхідна для досягнення рівня"
    )
    level_number: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True, comment="Порядковий номер рівня (1, 2, 3...)"
    )
    icon_url: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True, comment="URL або шлях до іконки, що представляє рівень"
    )

    # --- Зв'язки (Relationships) ---
    # group_id успадковано з BaseMainModel (через GroupAffiliationMixin)
    # Зв'язок з групою, якщо рівні є специфічними для груп.
    # Якщо group_id=NULL, це може бути глобальний/системний рівень.
    group: Mapped[Optional["Group"]] = relationship(
        foreign_keys=[BaseMainModel.group_id],  # Явно вказуємо foreign_keys
        # Якщо Group не має back_populates="levels", то тут його не вказуємо,
        # або додаємо "levels" до моделі Group.
        # back_populates="levels", # Потребує Mapped[List["Level"]] = relationship(...) в моделі Group
        lazy="selectin"
    )

    # Зв'язок з UserLevel для отримання всіх користувачів, що досягли цього рівня (якщо потрібно)
    # user_levels: Mapped[List["UserLevel"]] = relationship(back_populates="level", lazy="selectin")

    # _repr_fields успадковуються та збираються з BaseMainModel та його міксинів.
    # Додаємо специфічні для Level поля.
    _repr_fields = ["level_number", "required_points"]


if __name__ == "__main__":
    # Демонстраційний блок для моделі Level.
    print("--- Модель Рівня Гейміфікації (Level) ---")
    print(f"Назва таблиці: {Level.__tablename__}")

    print("\nОчікувані поля (успадковані та власні):")
    expected_fields = [
        'id', 'name', 'description', 'state', 'group_id', 'notes',
        'created_at', 'updated_at', 'deleted_at',
        'required_points', 'level_number', 'icon_url'
    ]
    for field in expected_fields:
        print(f"  - {field}")

    print("\nОчікувані зв'язки (relationships):")
    expected_relationships = ['group']  # , 'user_levels' (якщо додано)
    for rel in expected_relationships:
        print(f"  - {rel}")

    # Приклад створення екземпляра (без взаємодії з БД)
    from datetime import datetime, timezone

    example_level = Level(
        id=1,
        name="Новачок",  # TODO i18n
        description="Перший рівень для нових учасників.",  # TODO i18n
        group_id=202,  # Припустимо, цей рівень специфічний для групи 202
        required_points=0,
        level_number=1,
        state="active"
    )
    example_level.created_at = datetime.now(tz=timezone.utc)

    print(f"\nПриклад екземпляра Level (без сесії):\n  {example_level}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <Level(id=1, name='Новачок', state='active', group_id=202, level_number=1, required_points=0, created_at=...)>

    print("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
