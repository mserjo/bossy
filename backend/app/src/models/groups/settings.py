# backend/app/src/models/groups/settings.py
"""
Модель SQLAlchemy для сутності "Налаштування Групи" (GroupSetting).

Цей модуль визначає модель `GroupSetting`, яка зберігає специфічні
налаштування для кожної групи в системі Kudos.
"""
from datetime import datetime  # Необхідно для TYPE_CHECKING, якщо datetime використовується в типах
from typing import TYPE_CHECKING, Optional
from decimal import Decimal  # Для поля max_debt_amount

from sqlalchemy import String, ForeignKey, Numeric, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Абсолютний імпорт базових класів та міксинів
from backend.app.src.models.base import Base
from backend.app.src.models.mixins import TimestampedMixin  # Для відстеження часу створення/оновлення налаштувань
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

if TYPE_CHECKING:
    from backend.app.src.models.groups.group import Group


class GroupSetting(Base, TimestampedMixin):
    """
    Модель налаштувань групи.

    Кожен запис у цій таблиці відповідає налаштуванням для однієї конкретної групи.
    Зв'язок один-до-одного з моделлю `Group` (кожна група має один запис налаштувань).

    Атрибути:
        id (Mapped[int]): Унікальний ідентифікатор запису налаштувань.
        group_id (Mapped[int]): ID групи, до якої належать ці налаштування (унікальний, зовнішній ключ).
        currency_name (Mapped[str]): Назва валюти бонусів у групі (наприклад, "бали", "зірочки").
        allow_decimal_bonuses (Mapped[bool]): Чи дозволені дробові значення для бонусів.
        max_debt_amount (Mapped[Optional[Decimal]]): Максимально допустима сума "боргу" (від'ємного балансу) для учасника.
        task_completion_requires_review (Mapped[bool]): Чи потребує виконання завдання перевірки адміністратором.
        allow_task_reviews (Mapped[bool]): Чи дозволено користувачам залишати відгуки/рейтинги до завдань.
        allow_gamification_levels (Mapped[bool]): Чи використовуються рівні гейміфікації в групі.
        allow_gamification_badges (Mapped[bool]): Чи використовуються бейджі/досягнення в групі.
        allow_gamification_ratings (Mapped[bool]): Чи використовуються рейтинги користувачів в групі.

        group (Mapped["Group"]): Зв'язок з моделлю `Group`.
        created_at, updated_at: Часові мітки (успадковано).
    """
    __tablename__ = "group_settings"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True, comment="Унікальний ідентифікатор налаштувань групи"
    )
    group_id: Mapped[int] = mapped_column(
        ForeignKey('groups.id', name='fk_group_setting_group_id', ondelete="CASCADE"),
        unique=True,  # Гарантує, що одна група має лише один набір налаштувань
        nullable=False,
        comment="ID групи, до якої належать ці налаштування"
    )

    currency_name: Mapped[str] = mapped_column(
        String(50), default='бали', nullable=False, comment="Назва внутрішньої валюти/бонусів групи"
        # TODO i18n: default value
    )
    allow_decimal_bonuses: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Дозвіл на дробові значення бонусів"
    )
    max_debt_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True, comment="Максимально допустимий від'ємний баланс (борг)"
    )
    task_completion_requires_review: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Чи потребує виконання завдання перевірки адміністратором"
    )
    allow_task_reviews: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Чи дозволено користувачам залишати відгуки на завдання"
    )
    allow_gamification_levels: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Чи активна система рівнів у групі"
    )
    allow_gamification_badges: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Чи активна система бейджів/досягнень у групі"
    )
    allow_gamification_ratings: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Чи активна система рейтингів користувачів у групі"
    )

    # --- Зв'язок (Relationship) ---
    group: Mapped["Group"] = relationship(back_populates="settings", lazy="selectin")

    # Поля для __repr__
    # `id` автоматично додається через Base.__repr__
    # `created_at`, `updated_at` успадковуються з TimestampedMixin._repr_fields
    _repr_fields = ("group_id", "currency_name")


if __name__ == "__main__":
    # Демонстраційний блок для моделі GroupSetting.
    logger.info("--- Модель Налаштувань Групи (GroupSetting) ---")
    logger.info(f"Назва таблиці: {GroupSetting.__tablename__}")

    logger.info("\nОчікувані поля:")
    expected_fields = [
        'id', 'group_id', 'currency_name', 'allow_decimal_bonuses', 'max_debt_amount',
        'task_completion_requires_review', 'allow_task_reviews',
        'allow_gamification_levels', 'allow_gamification_badges', 'allow_gamification_ratings',
        'created_at', 'updated_at'
    ]
    for field in expected_fields:
        logger.info(f"  - {field}")

    logger.info("\nОчікувані зв'язки (relationships):")
    logger.info(f"  - group (до Group)")

    # Приклад створення екземпляра (без взаємодії з БД)
    example_settings = GroupSetting(
        id=1,
        group_id=202,
        currency_name="пункти",  # TODO i18n
        allow_decimal_bonuses=True,
        max_debt_amount=Decimal("-100.00"),
        task_completion_requires_review=False
    )
    # Імітуємо часові мітки
    example_settings.created_at = datetime.now(tz=timezone.utc)
    example_settings.updated_at = datetime.now(tz=timezone.utc)

    logger.info(f"\nПриклад екземпляра GroupSetting (без сесії):\n  {example_settings}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <GroupSetting(id=1, group_id=202, currency_name='пункти', created_at=...)>

    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
