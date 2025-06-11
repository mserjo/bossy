# backend/app/src/models/bonuses/reward.py
"""
Модель SQLAlchemy для сутності "Нагорода" (Reward).

Цей модуль визначає модель `Reward`, яка представляє нагороди,
які користувачі можуть "купувати" або отримувати за накопичені бонуси
в межах групи.
"""
from datetime import datetime, timezone  # timezone для __main__
from typing import TYPE_CHECKING, Optional
from decimal import Decimal

from sqlalchemy import String, ForeignKey, Text, Numeric, Integer  # Integer для quantity_available
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Абсолютний імпорт базової моделі
from backend.app.src.models.base import BaseMainModel  # Нагороди мають назву, опис, стан, group_id тощо.
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

if TYPE_CHECKING:
    from backend.app.src.models.groups.group import Group
    # Потенційно, зв'язок з AccountTransaction, якщо потрібно відстежувати, які транзакції пов'язані з отриманням нагород
    # from backend.app.src.models.bonuses.transaction import AccountTransaction


class Reward(BaseMainModel):
    """
    Модель Нагороди.

    Успадковує `BaseMainModel` (id, name, description, state, group_id, notes, timestamps, soft_delete).
    Поле `name` - назва нагороди.
    Поле `description` - детальний опис нагороди.
    Поле `state` - чи активна нагорода для отримання (наприклад, "active", "archived").
    Поле `group_id` - група, в якій доступна ця нагорода.

    Атрибути:
        cost (Mapped[Decimal]): "Вартість" нагороди в одиницях бонусів групи.
        quantity_available (Mapped[Optional[int]]): Кількість доступних екземплярів цієї нагороди.
                                                    NULL означає необмежену кількість.
        icon_url (Mapped[Optional[str]]): URL або шлях до іконки нагороди.

        group (Mapped["Group"]): Зв'язок з групою, до якої належить нагорода.
    """
    __tablename__ = "rewards"

    # --- Специфічні поля для Нагороди ---
    cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, comment="Вартість нагороди в одиницях бонусів"
    )
    quantity_available: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Доступна кількість (NULL для необмеженої)"
    )  # Якщо <= 0 і не NULL, то недоступна
    icon_url: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True, comment="URL або шлях до іконки нагороди"
    )

    # Поле 'state' (успадковане) використовується для активності нагороди.

    # --- Зв'язки (Relationships) ---
    # group_id успадковано з BaseMainModel (через GroupAffiliationMixin)
    group: Mapped["Group"] = relationship(
        foreign_keys=[BaseMainModel.group_id],  # Явно вказуємо foreign_keys
        back_populates="rewards",
        lazy="selectin"
    )

    # Можливий зв'язок з транзакціями, якщо потрібно відстежувати покупки нагород
    # transactions: Mapped[List["AccountTransaction"]] = relationship(back_populates="reward", lazy="selectin")

    # _repr_fields успадковуються та збираються з BaseMainModel та його міксинів.
    # Додаємо специфічні для Reward поля.
    _repr_fields = ["cost", "quantity_available"]


if __name__ == "__main__":
    # Демонстраційний блок для моделі Reward.
    logger.info("--- Модель Нагороди (Reward) ---")
    logger.info(f"Назва таблиці: {Reward.__tablename__}")

    logger.info("\nОчікувані поля (успадковані та власні):")
    expected_fields = [
        'id', 'name', 'description', 'state', 'group_id', 'notes',
        'created_at', 'updated_at', 'deleted_at',
        'cost', 'quantity_available', 'icon_url'
    ]
    for field in expected_fields:
        logger.info(f"  - {field}")

    logger.info("\nОчікувані зв'язки (relationships):")
    expected_relationships = ['group']  # , 'transactions' (якщо додано)
    for rel in expected_relationships:
        logger.info(f"  - {rel}")

    # Приклад створення екземпляра (без взаємодії з БД)
    example_reward = Reward(
        id=1,
        name="Чашка з логотипом",  # TODO i18n
        description="Фірмова чашка Kudos як чудова нагорода за активність.",  # TODO i18n
        group_id=202,
        cost=Decimal("150.00"),
        quantity_available=50,
        state="active"  # Успадковане поле
    )
    example_reward.created_at = datetime.now(tz=timezone.utc)

    logger.info(f"\nПриклад екземпляра Reward (без сесії):\n  {example_reward}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <Reward(id=1, name='Чашка з логотипом', state='active', cost=Decimal('150.00'), quantity_available=50, created_at=...)>

    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
