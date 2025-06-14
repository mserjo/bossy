# backend/app/src/models/gamification/badge.py
# -*- coding: utf-8 -*-
"""
Модель SQLAlchemy для сутності "Бейдж" (Badge) в системі гейміфікації.

Цей модуль визначає модель `Badge`, яка представляє значки або досягнення,
які користувачі можуть отримувати за виконання певних умов або завдань.
"""
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, ForeignKey  # ForeignKey для group_id з BaseMainModel
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Абсолютний імпорт базової моделі
from backend.app.src.models.base import BaseMainModel  # Включає id, name, description, state, group_id, etc.
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

if TYPE_CHECKING:
    from backend.app.src.models.groups.group import Group
    # from backend.app.src.models.gamification.user_achievement import UserAchievement # Для зворотнього зв'язку


class Badge(BaseMainModel):
    """
    Модель Бейджа Гейміфікації.

    Успадковує `BaseMainModel` (id, name, description, state, group_id, notes, timestamps, soft_delete).
    Поле `name` - назва бейджа (наприклад, "Першопроходець", "Майстер завдань").
    Поле `description` - опис умов отримання бейджа.
    Поле `state` - чи активний цей бейдж для отримання.
    Поле `group_id` - вказує, чи є бейдж специфічним для групи, чи глобальним (якщо NULL).

    Атрибути:
        icon_url (Mapped[Optional[str]]): URL або шлях до іконки бейджа.

        group (Mapped[Optional["Group"]]): Зв'язок з групою, до якої належить бейдж (якщо є).
    """
    __tablename__ = "gamification_badges"

    # --- Специфічні поля для Бейджа ---
    icon_url: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True, comment="URL або шлях до іконки, що представляє бейдж"
    )

    # --- Зв'язки (Relationships) ---
    # group_id успадковано з BaseMainModel (через GroupAffiliationMixin)
    # Зв'язок з групою, якщо бейджі є специфічними для груп.
    # Якщо group_id=NULL, це може бути глобальний/системний бейдж.
    group: Mapped[Optional["Group"]] = relationship(
        foreign_keys=[BaseMainModel.group_id],  # Явно вказуємо foreign_keys
        # Якщо Group не має back_populates="badges", то тут його не вказуємо,
        # або додаємо "badges" до моделі Group.
        # back_populates="badges", # Потребує Mapped[List["Badge"]] = relationship(...) в моделі Group
        lazy="selectin"
    )

    # Зв'язок з UserAchievement для отримання всіх користувачів, що отримали цей бейдж (якщо потрібно)
    # user_achievements: Mapped[List["UserAchievement"]] = relationship(back_populates="badge", lazy="selectin")

    # _repr_fields успадковуються та збираються з BaseMainModel та його міксинів (id, name, state_id, group_id, created_at тощо).
    # Додаємо специфічні для Badge поля.
    _repr_fields = ("icon_url",)


if __name__ == "__main__":
    # Демонстраційний блок для моделі Badge.
    logger.info("--- Модель Бейджа Гейміфікації (Badge) ---")
    logger.info(f"Назва таблиці: {Badge.__tablename__}")

    logger.info("\nОчікувані поля (успадковані та власні):")
    expected_fields = [
        'id', 'name', 'description', 'state', 'group_id', 'notes',
        'created_at', 'updated_at', 'deleted_at',
        'icon_url'
    ]
    for field in expected_fields:
        logger.info(f"  - {field}")

    logger.info("\nОчікувані зв'язки (relationships):")
    expected_relationships = ['group']  # , 'user_achievements' (якщо додано)
    for rel in expected_relationships:
        logger.info(f"  - {rel}")

    # Приклад створення екземпляра (без взаємодії з БД)
    from datetime import datetime, timezone

    example_badge = Badge(
        id=1,
        name="Майстер Завдань",  # TODO i18n
        description="Надається за виконання 100 завдань.",  # TODO i18n
        group_id=None,  # Припустимо, це глобальний бейдж
        icon_url="https://example.com/icons/master_of_tasks.png",
        state="active"
    )
    example_badge.created_at = datetime.now(tz=timezone.utc)

    logger.info(f"\nПриклад екземпляра Badge (без сесії):\n  {example_badge}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <Badge(id=1, name='Майстер Завдань', state='active', icon_url='https://example.com/icons/master_of_tasks.png', created_at=...)>

    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
