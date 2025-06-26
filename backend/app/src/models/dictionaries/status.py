# backend/app/src/models/dictionaries/status.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `StatusModel` для довідника "Статуси".
Статуси використовуються для позначення стану різних об'єктів в системі,
наприклад, завдань (нове, в роботі, виконано, скасовано), користувачів (активний, заблокований) тощо.

Модель `StatusModel` успадковує `BaseDictModel`, що надає їй стандартний набір полів
(id, name, description, code, state_id, group_id, created_at, updated_at, deleted_at, is_deleted, notes)
та функціональність.
"""
from typing import List, Optional

from sqlalchemy import UniqueConstraint, Integer, String  # type: ignore # Для визначення обмежень унікальності
from sqlalchemy.orm import relationship, Mapped, mapped_column

# from sqlalchemy.orm import relationship # type: ignore # Для визначення зв'язків (якщо потрібно)

from backend.app.src.models.dictionaries.base import BaseDictModel # Імпорт базової моделі для довідників

# TODO: Визначити, чи потрібні специфічні поля для моделі StatusModel, окрім успадкованих.
# Наприклад, колір для візуального представлення статусу, або порядок сортування.

class StatusModel(BaseDictModel):
    """
    Модель для довідника "Статуси".

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор статусу (успадковано).
        name (str): Назва статусу, що відображається користувачеві (наприклад, "Нове", "В роботі") (успадковано).
        description (str | None): Детальний опис статусу (успадковано).
        code (str): Унікальний символьний код статусу (наприклад, "new", "in_progress") (успадковано).
                    Використовується для програмної ідентифікації статусу.
        state_id (uuid.UUID | None): Ідентифікатор стану самого запису статусу (успадковано, використання під питанням для довідників).
        group_id (uuid.UUID | None): Ідентифікатор групи, якщо статус специфічний для групи (успадковано).
                                     Для глобальних статусів це поле буде NULL.
        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення запису (успадковано).
        deleted_at (datetime | None): Дата та час "м'якого" видалення запису (успадковано).
        is_deleted (bool): Прапорець, що вказує, чи запис "м'яко" видалено (успадковано).
        notes (str | None): Додаткові нотатки (успадковано).

    Ім'я таблиці в базі даних: `statuses`.
    """
    __tablename__ = "statuses"

    # Обмеження унікальності для поля `code`.
    # Це гарантує, що кожен символьний код статусу є унікальним в межах таблиці.
    # Якщо статуси можуть бути специфічними для груп (`group_id IS NOT NULL`),
    # то унікальність `code` може розглядатися в межах кожної групи.
    # В такому випадку, обмеження може бути `UniqueConstraint('group_id', 'code', name='uq_status_group_code')`.
    # Наразі припускаємо, що `code` має бути глобально унікальним, або унікальним серед тих, де `group_id IS NULL`.
    # TODO: Уточнити вимоги до унікальності кодів статусів (глобальна чи в межах групи).
    # Поки що робимо `code` унікальним глобально.
    # Якщо статуси можуть бути специфічними для груп (group_id IS NOT NULL),
    # то унікальність `code` може бути в межах `(group_id, code)`.
    # Поки що, для загальних статусів, `code` має бути унікальним.
    # Для статусів, що належать групі (якщо такі будуть), `group_id` буде заповнено,
    # і тоді унікальність `(group_id, code)` має сенс.
    # Alembic міграції мають реалізувати ці обмеження:
    # 1. UniqueConstraint('code', name='uq_statuses_global_code', postgresql_where=(Column('group_id').is_(None)))
    # 2. UniqueConstraint('group_id', 'code', name='uq_statuses_group_code', postgresql_where=(Column('group_id').isnot(None)))
    # Поки що в моделі залишаємо простий UniqueConstraint на 'code' для базової перевірки,
    # а більш складні обмеження - через міграції.
    __table_args__ = (
        UniqueConstraint('code', name='uq_statuses_code_model_level'), # Базове обмеження на рівні моделі
        # Коментар для Alembic:
        # Додати в міграцію:
        # op.create_unique_constraint('uq_statuses_global_code', 'statuses', ['code'], postgresql_where=sa.text('group_id IS NULL'))
        # op.create_unique_constraint('uq_statuses_group_code', 'statuses', ['group_id', 'code'], postgresql_where=sa.text('group_id IS NOT NULL'))
        # І видалити 'uq_statuses_code_model_level', якщо він буде конфліктувати.
    )

    # --- Зворотні зв'язки (Relationships) ---
    # Назви back_populates мають відповідати назвам зв'язків в цільових моделях.
    # ForeignKey рядки вказують на поле в цільовій моделі, яке посилається на StatusModel.id.

    # Зв'язок з UserModel.state_id
    users_with_this_state = relationship("UserModel", back_populates="state", foreign_keys="[UserModel.state_id]")
    # Зв'язок з GroupModel.state_id
    groups_with_this_state = relationship("GroupModel", back_populates="state", foreign_keys="[GroupModel.state_id]")
    # Зв'язок з TaskModel.state_id
    tasks_with_this_state = relationship("TaskModel", back_populates="state", foreign_keys="[TaskModel.state_id]")
    # ... і так далі для інших моделей, що успадковують BaseMainModel і використовують state_id ...
    # GroupTemplateModel, PollModel, RewardModel, BadgeModel, LevelModel, TeamModel
    group_templates_with_this_state = relationship("GroupTemplateModel", back_populates="state", foreign_keys="[GroupTemplateModel.state_id]")
    polls_with_this_state = relationship("PollModel", back_populates="state", foreign_keys="[PollModel.state_id]")
    rewards_with_this_state = relationship("RewardModel", back_populates="state", foreign_keys="[RewardModel.state_id]")
    badges_with_this_state = relationship("BadgeModel", back_populates="state", foreign_keys="[BadgeModel.state_id]")
    levels_with_this_state = relationship("LevelModel", back_populates="state", foreign_keys="[LevelModel.state_id]")
    teams_with_this_state = relationship("TeamModel", back_populates="state", foreign_keys="[TeamModel.state_id]")


    # Зв'язок зі статусами членства в групах (з GroupMembershipModel.status_in_group_id)
    group_memberships_with_this_status = relationship("GroupMembershipModel", back_populates="status_in_group", foreign_keys="[GroupMembershipModel.status_in_group_id]")

    # Зв'язок зі статусами запрошень до груп (з GroupInvitationModel.status_id)
    group_invitations_with_this_status = relationship("GroupInvitationModel", back_populates="status", foreign_keys="[GroupInvitationModel.status_id]")

    # Зв'язок зі статусами призначень завдань (з TaskAssignmentModel.status_id)
    task_assignments_with_this_status = relationship("TaskAssignmentModel", back_populates="status", foreign_keys="[TaskAssignmentModel.status_id]")

    # Зв'язок зі статусами виконань завдань (з TaskCompletionModel.status_id)
    task_completions_with_this_status = relationship("TaskCompletionModel", back_populates="status", foreign_keys="[TaskCompletionModel.status_id]")

    # Зв'язок зі статусами пропозицій завдань (з TaskProposalModel.status_id)
    task_proposals_with_this_status = relationship("TaskProposalModel", back_populates="status", foreign_keys="[TaskProposalModel.status_id]")

    # Зв'язок зі статусами звітів (з ReportModel.status_id)
    reports_with_this_status = relationship("ReportModel", back_populates="status", foreign_keys="[ReportModel.status_id]")

    # Якщо TaskReviewModel матиме status_id для модерації:
    # task_reviews_with_this_status = relationship("TaskReviewModel", back_populates="status", foreign_keys="[TaskReviewModel.status_id]")
    # Якщо FileModel матиме status_id:
    # files_with_this_status = relationship("FileModel", back_populates="status", foreign_keys="[FileModel.status_id]")

    # Зв'язок зі статусами звітів (з ReportModel.status_id)
    report_statuses: Mapped[List["ReportModel"]] = relationship(back_populates="status", foreign_keys="[ReportModel.status_id]")

    # Поле для сортування статусів у визначеному порядку (наприклад, для UI).
    display_order: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True)

    # Поле для зберігання кольору статусу (наприклад, для візуального виділення в UI).
    # Формат кольору, наприклад, HEX (#RRGGBB) або назва кольору.
    color_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True) # Збільшено довжину для назв кольорів

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі StatusModel.
        Наприклад: <StatusModel(id='...', name='Нове', code='new')>
        """
        return f"<{self.__class__.__name__}(id='{self.id}', name='{self.name}', code='{self.code}')>"

# Приклади початкових даних для довідника статусів (згідно technical-task.md):
# - створено (code: 'created')
# - в роботі (code: 'in_progress')
# - перевірка (code: 'pending_review')
# - підтверджено (code: 'confirmed', 'approved')
# - відхилено (code: 'rejected', 'declined')
# - заблоковано (code: 'blocked', 'suspended')
# - скасовано (code: 'cancelled')
# - видалено (code: 'deleted') - цей статус може бути зайвим, якщо використовується is_deleted/deleted_at

# TODO: Переконатися, що назви полів та їх типи відповідають вимогам `technical-task.md` та `structure-claude-v3.md`.
# `BaseDictModel` вже включає `name`, `description`, `code`.
# `state_id` успадковано, але його доцільність для самих записів довідника обговорюється в `BaseDictModel`.
# `group_id` успадковано для можливості створення статусів, специфічних для груп.
# Якщо статуси завжди глобальні, `group_id` для них буде `None`.
# Поля аудиту `created_at`, `updated_at`, `deleted_at`, `is_deleted`, `notes` також успадковані.
# Унікальність `code` додана через `UniqueConstraint`.
# Назва таблиці `statuses` відповідає структурі.
# Подальші специфічні поля (як `order` чи `color`) можуть бути додані за потреби.
