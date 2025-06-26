# backend/app/src/models/gamification/achievement.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `AchievementModel`.
Ця модель представляє факт отримання користувачем (`UserModel`)
конкретного бейджа (`BadgeModel`). Це зв'язок "багато-до-багатьох"
між користувачами та бейджами, що фіксує, хто який бейдж отримав і коли.
"""

from sqlalchemy import Column, ForeignKey, DateTime, UniqueConstraint, Text # type: ignore
from sqlalchemy.dialects.postgresql import UUID, JSONB # type: ignore
from sqlalchemy.orm import relationship # type: ignore
import uuid # Для роботи з UUID
from datetime import datetime # Для роботи з датами та часом

from backend.app.src.models.base import BaseModel # Використовуємо BaseModel

class AchievementModel(BaseModel):
    """
    Модель для фіксації отримання бейджа користувачем.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор запису про досягнення (успадковано).
        user_id (uuid.UUID): Ідентифікатор користувача, який отримав бейдж.
        badge_id (uuid.UUID): Ідентифікатор отриманого бейджа (з BadgeModel).
        achieved_at (datetime): Дата та час отримання бейджа (може бути `created_at`).
        # Додаткові дані, якщо бейдж повторюваний і має контекст
        context_details (JSONB | None): Наприклад, якщо бейдж "Працівник місяця", тут може бути місяць/рік.
        # Посилання на сутність, що спричинила досягнення (якщо застосовно)
        # source_trigger_entity_type (str | None): Тип сутності ('task_completion', 'event').
        # source_trigger_entity_id (uuid.UUID | None): ID сутності.

        # Якщо бейдж був вручну присуджений адміністратором
        awarded_by_user_id (uuid.UUID | None): Адміністратор, який вручну присудив бейдж.
        award_reason (Text | None): Причина ручного присудження.

        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення (успадковано).

    Зв'язки:
        user (relationship): Зв'язок з UserModel.
        badge (relationship): Зв'язок з BadgeModel.
        awarder (relationship): Зв'язок з UserModel (хто вручну присудив).
    """
    __tablename__ = "achievements"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    badge_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("badges.id", ondelete="CASCADE"), nullable=False, index=True)

    context_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    awarded_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_achievements_awarder_id", ondelete="SET NULL"), nullable=True, index=True)
    award_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


    # --- Зв'язки (Relationships) ---
    # TODO: Узгодити back_populates="achievements_earned" з UserModel
    user: Mapped["UserModel"] = relationship(foreign_keys=[user_id], back_populates="achievements_earned")
    badge: Mapped["BadgeModel"] = relationship(back_populates="achievements")
    # TODO: Узгодити back_populates="awarded_achievements_by_admin" з UserModel
    awarder: Mapped[Optional["UserModel"]] = relationship(foreign_keys=[awarded_by_user_id], back_populates="awarded_achievements_by_admin")


    # Обмеження унікальності:
    # Якщо бейдж не повторюваний (BadgeModel.is_repeatable = False),
    # то пара (user_id, badge_id) має бути унікальною.
    # Якщо бейдж повторюваний, то ця унікальність не потрібна, або вона має включати
    # якийсь контекст (наприклад, дату або spezifische дані з context_details).
    # Поки що, для простоти, припускаємо, що (user_id, badge_id) унікальні,
    # що означає, що бейджі за замовчуванням не повторювані.
    # Якщо `BadgeModel.is_repeatable` буде використовуватися для контролю,
    # то це обмеження має бути умовним або знятим, а логіка створення записів
    # в `AchievementModel` буде це враховувати.
    #
    # Якщо бейджі НЕ повторювані, то:
    # __table_args__ = (
    #     UniqueConstraint('user_id', 'badge_id', name='uq_user_badge_achievement'),
    # )
    # Якщо бейджі МОЖУТЬ бути повторювані, то такого обмеження не повинно бути,
    # або воно має включати `context_details` чи інший дискримінатор.
    #
    # Приймаємо рішення: `BadgeModel.is_repeatable` контролює логіку.
    # Якщо `is_repeatable = False`, то сервіс перевіряє унікальність `(user_id, badge_id)`.
    # Якщо `is_repeatable = True`, то сервіс дозволяє створювати нові записи.
    # Тому жорсткого UniqueConstraint на рівні БД поки що не додаємо,
    # покладаючись на логіку сервісу, керовану полем `BadgeModel.is_repeatable`.
    # Це дає більшу гнучкість.

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі AchievementModel.
        """
        return f"<{self.__class__.__name__}(user_id='{self.user_id}', badge_id='{self.badge_id}')>"

# TODO: Перевірити відповідність `technical-task.md`:
# - "Досягнення за виконання певних умов ... Досягнення, на відміну від нагород, не купуються, а заробляються"
#   - Ця модель фіксує зароблене досягнення (бейдж).

# TODO: Узгодити назву таблиці `achievements` з `structure-claude-v3.md`. Відповідає.
# Використання `BaseModel` як основи.
# Ключові поля: `user_id`, `badge_id`.
# `ondelete="CASCADE"` для зовнішніх ключів.
# `context_details` для повторюваних бейджів з контекстом.
# Поля для ручного присудження: `awarded_by_user_id`, `award_reason`.
# Зв'язки визначені.
# Унікальність `(user_id, badge_id)` буде контролюватися сервісом на основі `BadgeModel.is_repeatable`.
# Якщо `is_repeatable=False`, сервіс не дозволить створити дублікат.
# Якщо `is_repeatable=True`, дублікати (з різними `created_at` та, можливо, `context_details`) дозволені.
# Все виглядає логічно.
# `created_at` використовується як час отримання досягнення.
# `awarder_id` та `award_reason` корисні для аудиту ручних нагороджень.
# `context_details` у JSONB форматі дає гнучкість для зберігання специфічної інформації
# для повторюваних досягнень (наприклад, "Працівник місяця - Січень 2024").
# Якщо `context_details` не використовується, то для повторюваних бейджів просто створюється
# новий запис з новою датою `created_at`.
# Це дозволяє відстежувати, скільки разів користувач отримав повторюваний бейдж.
