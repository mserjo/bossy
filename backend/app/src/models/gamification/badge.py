# backend/app/src/models/gamification/badge.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `BadgeModel` для представлення бейджів (значків) гейміфікації.
Бейджі надаються користувачам за виконання певних умов або досягнень і слугують для престижу.
Бейджі налаштовуються адміністратором групи.
"""
from typing import Optional, List

from sqlalchemy import Column, String, Text, ForeignKey, Integer, UniqueConstraint, Boolean, \
    CheckConstraint  # type: ignore
from sqlalchemy.dialects.postgresql import UUID, JSONB # type: ignore
from sqlalchemy.orm import relationship, Mapped  # type: ignore
import uuid # Для роботи з UUID

# Використовуємо BaseMainModel, оскільки бейдж має назву, опис, статус (активний/неактивний для налаштування),
# і належить до групи.
from backend.app.src.models.base import BaseMainModel

class BadgeModel(BaseMainModel):
    """
    Модель для представлення бейджів гейміфікації.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор бейджа (успадковано).
        name (str): Назва бейджа (наприклад, "Марафонець", "Першопроходець") (успадковано).
        description (str | None): Опис бейджа та умов його отримання (успадковано).
        state_id (uuid.UUID | None): Статус налаштування бейджа (наприклад, "активний", "неактивний").
                                     Посилається на StatusModel. (успадковано)
        group_id (uuid.UUID): Ідентифікатор групи, до якої належить це налаштування бейджа. (успадковано, тут буде NOT NULL)

        # Умови отримання бейджа
        # Можуть бути простими (кількість виконаних завдань певного типу)
        # або складними (комбінація умов, збережена в JSON).
        condition_type (str): Тип умови ('task_count', 'specific_task', 'custom_event', 'manual_award').
                              TODO: Визначити Enum або довідник.
        condition_details (JSONB | None): Деталі умови. Наприклад:
                                          - для 'task_count': {"task_type_code": "chore", "count": 10, "period_days": 7} (10 завдань типу "chore" за 7 днів)
                                          - для 'specific_task': {"task_id": "uuid", "first_to_complete": true}
                                          - для 'custom_event': {"event_name": "won_competition_X"}
                                          - для 'manual_award': null (присуджується вручну адміном)

        icon_file_id (uuid.UUID | None): Ідентифікатор файлу іконки бейджа (посилання на FileModel).

        # Чи можна отримати бейдж кілька разів (наприклад, "Працівник місяця")
        is_repeatable (bool): Чи можна отримувати цей бейдж повторно.

        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення запису (успадковано).
        deleted_at (datetime | None): Дата та час "м'якого" видалення (успадковано).
        is_deleted (bool): Прапорець "м'якого" видалення (успадковано).
        notes (str | None): Додаткові нотатки (успадковано).

    Зв'язки:
        group (relationship): Зв'язок з GroupModel.
        # status (relationship): Зв'язок зі статусом (вже є через state_id).
        # icon_file (relationship): Зв'язок з FileModel.
        achievements (relationship): Список користувачів, які отримали цей бейдж (через AchievementModel).
    """
    __tablename__ = "badges"

    # group_id успадковано і має бути NOT NULL.

    # Тип умови для отримання бейджа.
    # TODO: Створити Enum або довідник для BadgeConditionType.
    # Приклади: 'TASK_COUNT_GENERAL', 'TASK_COUNT_BY_TYPE', 'STREAK_COMPLETION',
    # 'FIRST_COMPLETER', 'MANUAL_AWARD', 'CUSTOM_EVENT_TRIGGER'.
    condition_type_code: Column[str] = Column(String(100), nullable=False, index=True)

    # Деталі умови у форматі JSONB.
    condition_details: Column[JSONB | None] = Column(JSONB, nullable=True)

    # Іконка бейджа
    # TODO: Замінити "files.id" на константу або імпорт моделі FileModel.
    icon_file_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("files.id", name="fk_badges_icon_file_id"), nullable=True)

    is_repeatable: Column[bool] = Column(Boolean, default=False, nullable=False)


    # --- Зв'язки (Relationships) ---
    # group: Mapped["GroupModel"] - успадковано з BaseMainModel, якщо там є back_populates="badges_in_group" або подібне.
    # Оскільки BaseMainModel.group є загальним, тут може знадобитися явне визначення,
    # якщо потрібен специфічний back_populates.
    # Поки що припускаємо, що успадкованого достатньо, якщо GroupModel не має явного `badges` relationship.
    # Якщо GroupModel матиме `badges = relationship("BadgeModel", back_populates="group")`, то успадкований зв'язок спрацює.

    icon_file: Mapped[Optional["FileModel"]] = relationship(foreign_keys=[icon_file_id], back_populates="badge_icon_for")

    # Досягнення (хто і коли отримав цей бейдж)
    achievements: Mapped[List["AchievementModel"]] = relationship(back_populates="badge", cascade="all, delete-orphan")

    # `state_id` з BaseMainModel використовується для статусу налаштування бейджа.
    # state: Mapped[Optional["StatusModel"]] - успадковано

    __table_args__ = (
        CheckConstraint('group_id IS NOT NULL', name='ck_badge_group_id_not_null'),
        UniqueConstraint('group_id', 'name', name='uq_badge_group_name'),
    )

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі BadgeModel.
        """
        return f"<{self.__class__.__name__}(id='{self.id}', name='{self.name}', group_id='{self.group_id}')>"

# TODO: Перевірити відповідність `technical-task.md`:
# - "користувачам можуть надаватися ... бейджі ... за виконану кількість завдань/подій або накопиченими/заробленими бонусами
#   (налаштовується в адміном групі)" - ця модель для налаштування бейджів.
# - "Досягнення за виконання певних умов (наприклад, "Марафонець" – виконати 10 завдань за тиждень;
#   "Першопроходець" – першим виконати нове завдання; "Командний гравець" – успішно завершити 5 командних завдань).
#   Досягнення, на відміну від нагород, не купуються, а заробляються і слугують для престижу."
#   - `condition_type_code` та `condition_details` для умов.
#   - `AchievementModel` буде фіксувати факт отримання бейджа користувачем.

# TODO: Узгодити назву таблиці `badges` з `structure-claude-v3.md`. Відповідає.
# Використання `BaseMainModel` як основи. `group_id` має бути NOT NULL.
# Поля `condition_type_code`, `condition_details`, `icon_file_id`, `is_repeatable` додані.
# Зв'язки визначені.
# `JSONB` для `condition_details` для гнучкості умов.
# Унікальність `name` в межах групи важлива.
# `state_id` для активації/деактивації налаштувань бейджів.
# Все виглядає логічно.
# Логіка перевірки умов та присудження бейджів (створення записів в `AchievementModel`)
# буде реалізована на сервісному рівні, можливо, через фонові задачі або обробники подій.
# Поле `name` з `BaseMainModel` - назва бейджа.
# `description`, `notes`, `deleted_at`, `is_deleted` - успадковані.
# `group_id` - успадковане, але тут має бути обов'язковим.
# Зв'язок `group` уточнено з `foreign_keys`.
# Зв'язок з `AchievementModel` для відстеження, хто отримав цей бейдж.
# `is_repeatable` дозволяє, наприклад, бейдж "Працівник місяця".
# Якщо `is_repeatable=True`, то в `AchievementModel` для одного `user_id` та `badge_id`
# може бути кілька записів (з різними `achieved_at`).
# Якщо `is_repeatable=False`, то `UniqueConstraint(user_id, badge_id)` в `AchievementModel`.
# Поки що `AchievementModel` буде мати такий UniqueConstraint, що означає, що бейджі не повторювані за замовчуванням.
# Якщо потрібні повторювані, логіку `AchievementModel` треба буде змінити.
# Або ж, `is_repeatable` в `BadgeModel` керує тим, чи можна створювати дублікати в `AchievementModel`.
# Це більш гнучко.
