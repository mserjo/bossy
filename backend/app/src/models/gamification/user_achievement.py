# backend/app/src/models/gamification/user_achievement.py
# -*- coding: utf-8 -*-
"""
Модель SQLAlchemy для сутності "Досягнення Користувача" (UserAchievement).

Цей модуль визначає модель `UserAchievement`, яка фіксує факт отримання
користувачем певного бейджа (значка досягнень), можливо, в контексті групи.
"""
from datetime import datetime, timezone  # timezone для __main__
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, UniqueConstraint, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Абсолютний імпорт базових класів та міксинів
from backend.app.src.models.base import Base
from backend.app.src.models.mixins import TimestampedMixin  # `created_at` як час отримання досягнення
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User
    from backend.app.src.models.gamification.badge import Badge
    from backend.app.src.models.groups.group import Group


class UserAchievement(Base, TimestampedMixin):
    """
    Модель Досягнення Користувача (отримання бейджа).

    Зберігає інформацію про те, який бейдж, коли та в якій групі (якщо застосовно)
    отримав користувач. Поле `created_at` з `TimestampedMixin` використовується
    як дата та час отримання досягнення (`achieved_at`).

    Атрибути:
        id (Mapped[int]): Унікальний ідентифікатор запису про досягнення.
        user_id (Mapped[int]): ID користувача, який отримав досягнення.
        badge_id (Mapped[int]): ID отриманого бейджа.
        group_id (Mapped[Optional[int]]): ID групи, в контексті якої отримано досягнення (якщо бейдж груповий).

        user (Mapped["User"]): Зв'язок з моделлю `User`.
        badge (Mapped["Badge"]): Зв'язок з моделлю `Badge`.
        group (Mapped[Optional["Group"]]): Зв'язок з моделлю `Group`.
        created_at (Mapped[datetime]): Час отримання досягнення (успадковано).
        updated_at (Mapped[datetime]): Час оновлення запису (успадковано).
    """
    __tablename__ = "gamification_user_achievements"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True, comment="Унікальний ідентифікатор запису про досягнення"
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', name='fk_user_achievement_user_id', ondelete="CASCADE"),
        nullable=False,
        comment="ID користувача, який отримав досягнення"
    )
    badge_id: Mapped[int] = mapped_column(
        ForeignKey('gamification_badges.id', name='fk_user_achievement_badge_id', ondelete="CASCADE"),
        # Якщо бейдж видаляється, досягнення теж
        nullable=False,
        comment="ID отриманого бейджа"
    )
    group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('groups.id', name='fk_user_achievement_group_id', ondelete="CASCADE"),
        # Якщо група видаляється, досягнення в цій групі теж
        nullable=True,  # Може бути NULL, якщо бейдж глобальний, а не груповий
        comment="ID групи, в контексті якої отримано досягнення (якщо застосовно)"
    )
    # `created_at` з TimestampedMixin використовується як `achieved_at` (час досягнення)

    # Обмеження та індекси
    # Користувач може отримати конкретний бейдж в конкретній групі лише один раз.
    # Якщо group_id є NULL (глобальний бейдж), то пара (user_id, badge_id) має бути унікальною.
    # SQLAlchemy може мати проблеми з UniqueConstraint, що включає NULLABLE колонки в деяких діалектах БД.
    # Розглянути окремі унікальні індекси або логіку на рівні програми/БД, якщо це потрібно.
    # Для простоти, припускаємо, що NULL в group_id розглядається як унікальне значення або
    # що глобальні бейджі не мають group_id і для них діє uq(user_id, badge_id).
    # Більш надійний підхід - умовні індекси на рівні БД або розділення на дві таблиці.
    # Наразі, для прикладу:
    __table_args__ = (
        UniqueConstraint('user_id', 'badge_id', 'group_id', name='uq_user_badge_group_achievement'),
        Index('ix_user_achievements_user_group', 'user_id', 'group_id'),
    # Для швидкого пошуку досягнень користувача в групі
    )

    # --- Зв'язки (Relationships) ---
    user: Mapped["User"] = relationship(lazy="selectin")  # back_populates="achievements" можна додати до User
    badge: Mapped["Badge"] = relationship(lazy="selectin")  # back_populates="user_achievements" можна додати до Badge
    group: Mapped[Optional["Group"]] = relationship(
        lazy="selectin")  # back_populates="user_achievements" можна додати до Group

    # Поля для __repr__
    # `id` автоматично додається через Base.__repr__
    # `created_at`, `updated_at` успадковуються з TimestampedMixin._repr_fields
    _repr_fields = ("user_id", "badge_id", "group_id")


if __name__ == "__main__":
    # Демонстраційний блок для моделі UserAchievement.
    logger.info("--- Модель Досягнення Користувача (UserAchievement) ---")
    logger.info(f"Назва таблиці: {UserAchievement.__tablename__}")

    logger.info("\nОчікувані поля:")
    expected_fields = ['id', 'user_id', 'badge_id', 'group_id', 'created_at', 'updated_at']
    for field in expected_fields:
        logger.info(f"  - {field}")

    logger.info("\nОчікувані зв'язки (relationships):")
    expected_relationships = ['user', 'badge', 'group']
    for rel in expected_relationships:
        logger.info(f"  - {rel}")

    # Приклад створення екземпляра (без взаємодії з БД)
    example_achievement = UserAchievement(
        id=1,
        user_id=101,
        badge_id=1,  # ID бейджа "Майстер Завдань"
        group_id=None  # Припустимо, це глобальне досягнення
    )
    # Імітуємо часові мітки (created_at - час досягнення)
    example_achievement.created_at = datetime.now(tz=timezone.utc)
    example_achievement.updated_at = datetime.now(tz=timezone.utc)

    logger.info(f"\nПриклад екземпляра UserAchievement (без сесії):\n  {example_achievement}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <UserAchievement(id=1, user_id=101, badge_id=1, group_id=None, created_at=...)>

    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
