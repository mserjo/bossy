# backend/app/src/models/gamification/rating.py
# -*- coding: utf-8 -*-
"""
Модель SQLAlchemy для сутності "Рейтинг Користувача в Групі" (UserGroupRating).

Цей модуль визначає модель `UserGroupRating`, яка зберігає розрахований
рейтинг або бали користувача в контексті конкретної групи за певний період
або для певного типу рейтингу (наприклад, загальний, місячний).
"""
from datetime import datetime, date, timezone  # date для period_*, timezone для __main__
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, ForeignKey, UniqueConstraint, Index, Integer, func  # Integer для rating_score
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Абсолютний імпорт базових класів та міксинів
from backend.app.src.models.base import Base
from backend.app.src.models.mixins import TimestampedMixin  # `updated_at` як час останнього розрахунку рейтингу
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

from backend.app.src.core.dicts import RatingType # Імпорт Enum
from sqlalchemy import Enum as SQLEnum # Імпорт SQLEnum

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User
    from backend.app.src.models.groups.group import Group


class UserGroupRating(Base, TimestampedMixin):
    """
    Модель Рейтингу Користувача в Групі.

    Зберігає розрахований рейтинг (або суму балів) для користувача в певній групі.
    Може використовуватися для різних типів рейтингів (загальний, за період).
    Поле `updated_at` з `TimestampedMixin` може використовуватися для позначення
    часу останнього оновлення/перерахунку цього рейтингу.

    Атрибути:
        id (Mapped[int]): Унікальний ідентифікатор запису рейтингу.
        user_id (Mapped[int]): ID користувача.
        group_id (Mapped[int]): ID групи.
        rating_score (Mapped[int]): Розрахований рейтинг або кількість балів.
        period_start_date (Mapped[Optional[date]]): Дата початку періоду, за який розраховано рейтинг (якщо застосовно).
        period_end_date (Mapped[Optional[date]]): Дата кінця періоду, за який розраховано рейтинг (якщо застосовно).
        rating_type (Mapped[Optional[RatingType]]): Тип рейтингу (наприклад, "monthly", "overall"). # Використовує Enum RatingType

        user (Mapped["User"]): Зв'язок з моделлю `User`.
        group (Mapped["Group"]): Зв'язок з моделлю `Group`.
        created_at, updated_at: Успадковано. `updated_at` - час останнього розрахунку.
    """
    __tablename__ = "gamification_user_group_ratings"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True, comment="Унікальний ідентифікатор запису рейтингу"
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', name='fk_user_group_rating_user_id', ondelete="CASCADE"),
        nullable=False,
        comment="ID користувача"
    )
    group_id: Mapped[int] = mapped_column(
        ForeignKey('groups.id', name='fk_user_group_rating_group_id', ondelete="CASCADE"),
        nullable=False,
        comment="ID групи"
    )
    rating_score: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Розрахований рейтинг або кількість балів"
    )

    # Поля для визначення періоду рейтингу (якщо рейтинг не є загальним за весь час)
    period_start_date: Mapped[Optional[date]] = mapped_column(
        nullable=True, comment="Дата початку періоду рейтингу (якщо застосовно)"
    )
    period_end_date: Mapped[Optional[date]] = mapped_column(
        nullable=True, index=True, comment="Дата кінця періоду рейтингу (якщо застосовно)"
    )

    rating_type: Mapped[Optional[RatingType]] = mapped_column(
        SQLEnum(RatingType), nullable=True, index=True, comment="Тип рейтингу (наприклад, 'monthly', 'overall')"
    )

    # Обмеження та індекси
    # Унікальність для користувача, групи, типу рейтингу та дати кінця періоду.
    # Це дозволяє мати, наприклад, місячний рейтинг для кожного місяця, загальний рейтинг тощо.
    __table_args__ = (
        UniqueConstraint('user_id', 'group_id', 'rating_type', 'period_end_date',
                         name='uq_user_group_rating_period_type'),
        Index('ix_user_group_ratings_user_group', 'user_id', 'group_id'),
    # Для швидкого пошуку рейтингів користувача в групі
    )

    # --- Зв'язки (Relationships) ---
    user: Mapped["User"] = relationship(lazy="selectin")  # back_populates="group_ratings" можна додати до User
    group: Mapped["Group"] = relationship(lazy="selectin")  # back_populates="user_ratings" можна додати до Group

    # Поля для __repr__
    # `id` автоматично додається через Base.__repr__
    # `created_at`, `updated_at` успадковуються з TimestampedMixin._repr_fields
    _repr_fields = ("user_id", "group_id", "rating_score", "rating_type", "period_end_date")


if __name__ == "__main__":
    # Демонстраційний блок для моделі UserGroupRating.
    logger.info("--- Модель Рейтингу Користувача в Групі (UserGroupRating) ---")
    logger.info(f"Назва таблиці: {UserGroupRating.__tablename__}")

    logger.info("\nОчікувані поля:")
    expected_fields = [
        'id', 'user_id', 'group_id', 'rating_score',
        'period_start_date', 'period_end_date', 'rating_type',
        'created_at', 'updated_at'
    ]
    for field in expected_fields:
        logger.info(f"  - {field}")

    logger.info("\nОчікувані зв'язки (relationships):")
    expected_relationships = ['user', 'group']
    for rel in expected_relationships:
        logger.info(f"  - {rel}")

    # Приклад створення екземпляра (без взаємодії з БД)
    example_rating = UserGroupRating(
        id=1,
        user_id=101,
        group_id=202,
        rating_score=1500,
        rating_type=RatingType.OVERALL,
        period_end_date=None  # Для загального рейтингу може не бути дати кінця періоду
    )
    # Імітуємо часові мітки
    example_rating.created_at = datetime.now(tz=timezone.utc) - timedelta(days=30)  # Створено місяць тому
    example_rating.updated_at = datetime.now(tz=timezone.utc)  # Оновлено сьогодні

    logger.info(f"\nПриклад екземпляра UserGroupRating (без сесії):\n  {example_rating}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <UserGroupRating(id=1, user_id=101, group_id=202, rating_score=1500, rating_type=<RatingType.OVERALL: 'overall'>, updated_at=...)>

    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
