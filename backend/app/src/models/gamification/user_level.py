# backend/app/src/models/gamification/user_level.py
"""
Модель SQLAlchemy для сутності "Рівень Користувача" (UserLevel).

Цей модуль визначає модель `UserLevel`, яка фіксує досягнення
користувачем певного рівня гейміфікації в межах конкретної групи.
"""
from datetime import datetime, timezone  # timezone для __main__
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Абсолютний імпорт базових класів та міксинів
from backend.app.src.models.base import Base
from backend.app.src.models.mixins import TimestampedMixin  # `created_at` як час досягнення рівня

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User
    from backend.app.src.models.gamification.level import Level
    from backend.app.src.models.groups.group import Group


class UserLevel(Base, TimestampedMixin):
    """
    Модель Рівня Користувача.

    Зберігає інформацію про те, якого рівня досяг користувач у конкретній групі
    та коли це сталося. Поле `created_at` з `TimestampedMixin` використовується
    як дата та час досягнення рівня (`achieved_at`).

    Атрибути:
        id (Mapped[int]): Унікальний ідентифікатор запису про досягнення рівня.
        user_id (Mapped[int]): ID користувача, який досяг рівня.
        level_id (Mapped[int]): ID досягнутого рівня.
        group_id (Mapped[int]): ID групи, в межах якої досягнуто рівень.

        user (Mapped["User"]): Зв'язок з моделлю `User`.
        level (Mapped["Level"]): Зв'язок з моделлю `Level`.
        group (Mapped["Group"]): Зв'язок з моделлю `Group`.
        created_at (Mapped[datetime]): Час досягнення рівня (успадковано).
        updated_at (Mapped[datetime]): Час оновлення запису (успадковано, менш релевантне тут).
    """
    __tablename__ = "gamification_user_levels"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True,
        comment="Унікальний ідентифікатор запису про рівень користувача"
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', name='fk_user_level_user_id', ondelete="CASCADE"),
        nullable=False,
        comment="ID користувача, який досяг рівня"
    )
    level_id: Mapped[int] = mapped_column(
        ForeignKey('gamification_levels.id', name='fk_user_level_level_id', ondelete="CASCADE"),
        # Якщо рівень видаляється, цей запис теж
        nullable=False,
        comment="ID досягнутого рівня гейміфікації"
    )
    group_id: Mapped[int] = mapped_column(
        ForeignKey('groups.id', name='fk_user_level_group_id', ondelete="CASCADE"),
        nullable=False,
        comment="ID групи, в якій досягнуто рівень"
    )
    # `created_at` з TimestampedMixin використовується як `achieved_at` (час досягнення)

    # Обмеження та індекси
    # Користувач може досягти кожного рівня в групі лише один раз.
    # Або, якщо це таблиця для зберігання *поточного* рівня, то пара (user_id, group_id) має бути унікальною.
    # Поточна назва `UserLevel` (Рівень користувача) більше схожа на запис про досягнення певного рівня.
    # Якщо це історія досягнень, то `UniqueConstraint('user_id', 'level_id', 'group_id', ...)` є коректним.
    # Якщо це поточний рівень, то `UniqueConstraint('user_id', 'group_id', ...)` і поле level_id оновлюється.
    # Припускаємо, що це запис про досягнення конкретного рівня.
    __table_args__ = (
        UniqueConstraint('user_id', 'level_id', 'group_id', name='uq_user_level_in_group_achievement'),
        Index('ix_user_levels_user_group', 'user_id', 'group_id'),  # Для швидкого пошуку рівнів користувача в групі
    )

    # --- Зв'язки (Relationships) ---
    user: Mapped["User"] = relationship(lazy="selectin")  # back_populates="achieved_levels" можна додати до User
    level: Mapped["Level"] = relationship(lazy="selectin")  # back_populates="user_levels" можна додати до Level
    group: Mapped["Group"] = relationship(
        lazy="selectin")  # back_populates="user_levels_achieved" можна додати до Group

    # Поля для __repr__
    # `created_at` (як achieved_at) та `updated_at` успадковуються з TimestampedMixin._repr_fields
    _repr_fields = ["id", "user_id", "level_id", "group_id"]


if __name__ == "__main__":
    # Демонстраційний блок для моделі UserLevel.
    print("--- Модель Рівня Користувача (UserLevel) ---")
    print(f"Назва таблиці: {UserLevel.__tablename__}")

    print("\nОчікувані поля:")
    expected_fields = ['id', 'user_id', 'level_id', 'group_id', 'created_at', 'updated_at']
    for field in expected_fields:
        print(f"  - {field}")

    print("\nОчікувані зв'язки (relationships):")
    expected_relationships = ['user', 'level', 'group']
    for rel in expected_relationships:
        print(f"  - {rel}")

    # Приклад створення екземпляра (без взаємодії з БД)
    example_user_level = UserLevel(
        id=1,
        user_id=101,
        level_id=1,  # ID рівня "Новачок"
        group_id=202
    )
    # Імітуємо часові мітки (created_at - час досягнення)
    example_user_level.created_at = datetime.now(tz=timezone.utc)
    example_user_level.updated_at = datetime.now(tz=timezone.utc)

    print(f"\nПриклад екземпляра UserLevel (без сесії):\n  {example_user_level}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <UserLevel(id=1, user_id=101, level_id=1, group_id=202, created_at=...)>

    print("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
