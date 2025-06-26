# backend/app/src/models/gamification/rating.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `RatingModel` для зберігання рейтингів користувачів
в межах групи. Рейтинги можуть розраховуватися за різними критеріями
(кількість виконаних завдань, накопичені бонуси тощо) і можуть зберігатися
періодично для відстеження динаміки та історії.
"""

from sqlalchemy import Column, ForeignKey, DateTime, String, Numeric, Integer, Index # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship # type: ignore
import uuid # Для роботи з UUID
from datetime import datetime # Для роботи з датами та часом

from backend.app.src.models.base import BaseModel # Використовуємо BaseModel

class RatingModel(BaseModel):
    """
    Модель для зберігання записів про рейтинг користувача в групі на певну дату.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор запису рейтингу (успадковано).
        user_id (uuid.UUID): Ідентифікатор користувача.
        group_id (uuid.UUID): Ідентифікатор групи, в якій розрахований рейтинг.
        rating_type_code (str): Код типу рейтингу (наприклад, "by_completed_tasks", "by_earned_bonuses").
                                TODO: Визначити Enum або довідник для типів рейтингів.
        rating_value (Numeric): Значення рейтингу (наприклад, кількість балів, позиція).
        rank_position (int | None): Позиція користувача в рейтингу на момент розрахунку (якщо застосовно).
        period_start_date (datetime | None): Початок періоду, за який розрахований рейтинг (для періодичних рейтингів).
        period_end_date (datetime): Кінець періоду або дата розрахунку рейтингу.

        # Додаткові деталі
        # calculation_details (JSONB | None): Деталі, використані для розрахунку (наприклад, кількість завдань, сума бонусів).

        created_at (datetime): Дата та час створення запису (успадковано, відповідає даті розрахунку).
        updated_at (datetime): Дата та час останнього оновлення (успадковано, зазвичай не оновлюється).

    Зв'язки:
        user (relationship): Зв'язок з UserModel.
        group (relationship): Зв'язок з GroupModel.
    """
    __tablename__ = "ratings"

    user_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    group_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)

    # Тип рейтингу, наприклад, 'tasks_completed_monthly', 'total_bonus_points_all_time'.
    # TODO: Створити Enum або довідник для RatingType.
    rating_type_code: Column[str] = Column(String(100), nullable=False, index=True)

    # Значення рейтингу. Може бути кількістю балів, виконаних завдань тощо.
    rating_value: Column[Numeric] = Column(Numeric(12, 2), nullable=False) # Або Integer, залежно від типу рейтингу

    # Позиція в рейтингу (1-ше місце, 2-ге тощо). Може бути NULL, якщо це не ранговий рейтинг.
    rank_position: Column[int | None] = Column(Integer, nullable=True)

    # Дата, на яку або за період до якої розрахований рейтинг.
    # `created_at` з BaseModel може слугувати як `calculated_at_date` або `period_end_date`.
    # Для періодичних рейтингів (наприклад, місячний) можуть знадобитися start/end дати.
    period_start_date: Column[DateTime | None] = Column(DateTime(timezone=True), nullable=True)
    # `created_at` буде використовуватися як `period_end_date` або `snapshot_date`.
    # Для ясності можна додати окреме поле:
    snapshot_date: Column[DateTime] = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)


    # --- Зв'язки (Relationships) ---
    # TODO: Узгодити back_populates="ratings_history" з UserModel
    user: Mapped["UserModel"] = relationship(foreign_keys=[user_id], back_populates="ratings_history")
    # TODO: Узгодити back_populates="ratings_history" (або схоже) з GroupModel
    group: Mapped["GroupModel"] = relationship(foreign_keys=[group_id], back_populates="ratings_history")

    # Обмеження та індекси
    # Забезпечує, що для користувача, групи, типу рейтингу та дати зрізу є лише один запис.
    # Це важливо, якщо рейтинги зберігаються як знімки стану.
    # __table_args__ = (
    #     UniqueConstraint('user_id', 'group_id', 'rating_type_code', 'snapshot_date', name='uq_user_group_rating_snapshot'),
    # )
    # Або, якщо `snapshot_date` - це `created_at`, то індекс на ці поля.
    # Індекси для швидкого пошуку рейтингів
    __table_args__ = (
        Index('ix_ratings_user_group_type_date', 'user_id', 'group_id', 'rating_type_code', 'snapshot_date'),
    )


    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі RatingModel.
        """
        return f"<{self.__class__.__name__}(user='{self.user_id}', group='{self.group_id}', type='{self.rating_type_code}', value='{self.rating_value}', date='{self.snapshot_date}')>"

# TODO: Перевірити відповідність `technical-task.md`:
# - "різні рейтинги користувачів: за кількістю виконаних завдань; за накопиченими/заробленими бонусами в групі; і т.д. (в групі)"
#   - Ця модель дозволяє зберігати такі рейтинги. `rating_type_code` для розрізнення типів.
#   - Зберігання історії дозволяє відстежувати динаміку.

# TODO: Узгодити назву таблиці `ratings` з `structure-claude-v3.md`. Відповідає.
# Використання `BaseModel` як основи.
# Ключові поля: `user_id`, `group_id`, `rating_type_code`, `rating_value`, `snapshot_date`.
# Додаткові поля: `rank_position`, `period_start_date`.
# `ondelete="CASCADE"` для `user_id` та `group_id`.
# Індекси для ефективного запиту даних. `UniqueConstraint` може бути занадто жорстким,
# якщо можливі кілька записів за одну дату (наприклад, якщо оновлюється протягом дня).
# Індекс на основні поля фільтрації є кращим.
# Зв'язки визначені.
# Все виглядає логічно для зберігання історії рейтингів.
# Розрахунок самих рейтингів буде відбуватися на сервісному рівні (можливо, фоновими задачами),
# а ця таблиця слугуватиме для зберігання результатів цих розрахунків.
# `snapshot_date` (або `created_at`) важлива для часових зрізів рейтингу.
# `rating_value` може бути Numeric або Integer залежно від того, що вимірюється.
# Numeric(12,2) є досить гнучким.
# `rating_type_code` дозволить мати різні типи рейтингів (щотижневий, місячний, за всі часи, за завданнями, за бонусами).
# `rank_position` для зберігання позиції в топі.
# `period_start_date` та `snapshot_date` (як `period_end_date`) для визначення періоду рейтингу.
