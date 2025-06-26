# backend/app/src/models/gamification/level.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `LevelModel` для представлення рівнів гейміфікації.
Рівні можуть надаватися користувачам за досягнення певних умов, наприклад,
накопичення певної кількості бонусів або виконання заданої кількості завдань.
Рівні налаштовуються адміністратором групи.
"""
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import Column, String, Text, ForeignKey, Integer, Numeric, CheckConstraint, \
    UniqueConstraint  # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship, Mapped, mapped_column  # type: ignore
import uuid # Для роботи з UUID

# Використовуємо BaseMainModel, оскільки рівень має назву (наприклад, "Новачок", "Експерт"),
# опис, може мати статус (активний/неактивний для налаштування), і належить до групи
# (якщо рівні специфічні для груп, а не глобальні).
# ТЗ: "налаштовується ... адміном групі", що вказує на приналежність до групи.
from backend.app.src.models.base import BaseMainModel

class LevelModel(BaseMainModel):
    """
    Модель для представлення рівнів гейміфікації.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор рівня (успадковано).
        name (str): Назва рівня (наприклад, "Бронзовий", "Золотий", "Легенда") (успадковано).
        description (str | None): Опис рівня та переваг, які він надає (успадковано).
        state_id (uuid.UUID | None): Статус налаштування рівня (наприклад, "активний", "неактивний").
                                     Посилається на StatusModel. (успадковано)
        group_id (uuid.UUID): Ідентифікатор групи, до якої належить це налаштування рівня. (успадковано, тут буде NOT NULL)

        level_number (int): Порядковий номер рівня (наприклад, 1, 2, 3...). Використовується для сортування та визначення прогресу.
        required_points (Numeric | None): Кількість бонусних балів, необхідних для досягнення цього рівня.
        required_tasks_completed (int | None): Кількість виконаних завдань, необхідних для досягнення цього рівня.

        # Додаткові умови для досягнення рівня (можуть бути в JSON або окремих полях)
        # custom_conditions (JSONB | None): Наприклад, {"min_streak_days": 7, "specific_badge_id": "uuid"}

        icon_file_id (uuid.UUID | None): Ідентифікатор файлу іконки рівня (посилання на FileModel).

        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення запису (успадковано).
        deleted_at (datetime | None): Дата та час "м'якого" видалення (успадковано).
        is_deleted (bool): Прапорець "м'якого" видалення (успадковано).
        notes (str | None): Додаткові нотатки (успадковано).

    Зв'язки:
        group (relationship): Зв'язок з GroupModel.
        # status (relationship): Зв'язок зі статусом (вже є через state_id).
        # icon_file (relationship): Зв'язок з FileModel.
        user_levels (relationship): Список користувачів, які досягли цього рівня (через UserLevelModel).
    """
    __tablename__ = "levels"

    # group_id успадковано і має бути NOT NULL.

    level_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    required_points: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    required_tasks_completed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    icon_file_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("files.id", name="fk_levels_icon_file_id", ondelete="SET NULL"), nullable=True)

    # --- Зв'язки (Relationships) ---
    # group: Mapped["GroupModel"] - успадковано з BaseMainModel

    # TODO: Узгодити back_populates з FileModel
    icon_file: Mapped[Optional["FileModel"]] = relationship(foreign_keys=[icon_file_id], back_populates="level_icon_for")

    user_levels: Mapped[List["UserLevelModel"]] = relationship(back_populates="level", cascade="all, delete-orphan")

    # state: Mapped[Optional["StatusModel"]] - успадковано з BaseMainModel

    __table_args__ = (
        CheckConstraint('group_id IS NOT NULL', name='ck_level_group_id_not_null'),
        UniqueConstraint('group_id', 'level_number', name='uq_level_group_level_number'),
        UniqueConstraint('group_id', 'name', name='uq_level_group_name'),
    )

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі LevelModel.
        """
        return f"<{self.__class__.__name__}(id='{self.id}', name='{self.name}', group_id='{self.group_id}', level_num='{self.level_number}')>"

# TODO: Перевірити відповідність `technical-task.md`:
# - "користувачам можуть надаватися рівні ... за виконану кількість завдань/подій або накопиченими/заробленими бонусами
#   (налаштовується в адміном групі)"
#   - Ця модель для налаштування рівнів. `required_points`, `required_tasks_completed`.
#   - Належність до групи (`group_id`).

# TODO: Узгодити назву таблиці `levels` з `structure-claude-v3.md`. Відповідає.
# Використання `BaseMainModel` як основи. `group_id` має бути NOT NULL.
# Поля `level_number`, `required_points`, `required_tasks_completed`, `icon_file_id` додані.
# Зв'язки визначені.
# `level_number` важливий для визначення послідовності рівнів.
# Унікальність `level_number` та `name` в межах групи важлива.
# `state_id` для активації/деактивації налаштувань рівнів.
# Все виглядає логічно.
# `UserLevelModel` буде зв'язувати користувача з досягнутим рівнем.
# Умови досягнення рівня (required_points, required_tasks_completed) можуть бути комбінованими (AND/OR) -
# це визначається логікою сервісу. Поля в моделі просто зберігають порогові значення.
# Можливість додавання `custom_conditions` у JSONB для більш складних правил.
# Зв'язок `group` уточнено з `foreign_keys`.
# Зв'язок з `UserLevelModel` для відстеження, хто досяг цього рівня.
# Поле `name` з `BaseMainModel` - назва рівня.
# `description`, `notes`, `deleted_at`, `is_deleted` - успадковані.
# `group_id` - успадковане, але тут має бути обов'язковим.
# Контроль обов'язковості `group_id` - на рівні логіки/валідації.
# Або перевизначити `group_id` тут як `nullable=False`.
# Поки що залишаю як є.
