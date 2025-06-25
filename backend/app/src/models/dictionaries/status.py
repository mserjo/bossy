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

from sqlalchemy import UniqueConstraint # type: ignore # Для визначення обмежень унікальності
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
    # Для статусів, що належать групі, `group_id` буде заповнено, і тоді
    # унікальність `(group_id, code)` має сенс.
    # Це можна реалізувати двома окремими UniqueConstraint з умовами postgresql_where
    # або одним, якщо `group_id` завжди NULL для цього довідника (що малоймовірно для всіх статусів).
    # Поки що залишаю простий UniqueConstraint на `code`.
    # TODO: Переглянути унікальність, якщо статуси будуть сильно залежати від груп.
    __table_args__ = (
        UniqueConstraint('code', name='uq_statuses_code'),
        # Приклад для унікальності в межах групи (якщо потрібно):
        # UniqueConstraint('group_id', 'code', name='uq_statuses_group_code', postgresql_where=(Column('group_id').isnot(None))),
        # UniqueConstraint('code', name='uq_statuses_global_code', postgresql_where=(Column('group_id').is_(None))),
    )

    # --- Зворотні зв'язки (Relationships) ---
    # Ці зв'язки показують, які сутності використовують цей статус.
    # Назви back_populates мають відповідати назвам зв'язків в тих моделях.

    # Зв'язок з BaseMainModel (для поля state_id в багатьох моделях)
    # Оскільки багато моделей можуть посилатися на StatusModel через state_id,
    # тут може бути багато зворотних зв'язків.
    # Наприклад, для UserModel:
    # users_with_this_state = relationship("UserModel", back_populates="state", foreign_keys="[UserModel.state_id]")
    # Для TaskModel:
    # tasks_with_this_state = relationship("TaskModel", back_populates="state", foreign_keys="[TaskModel.state_id]")
    # І так далі для GroupModel, GroupTemplateModel, PollModel, RewardModel, BadgeModel, LevelModel,
    # TaskProposalModel, ReportModel, FileModel (якщо матиме статус).
    #
    # Це робить StatusModel дуже "важкою" зі зв'язками.
    # Можливо, краще не визначати всі ці зворотні зв'язки тут,
    # а отримувати сутності за статусом через запити до відповідних таблиць.
    #
    # Або ж, якщо потрібно, визначати лише найважливіші або використовувати загальний підхід,
    # але це складно через різні foreign_keys.
    #
    # Поки що залишаю без явних зворотних зв'язків до всіх можливих моделей,
    # щоб уникнути надмірної складності та циклічних залежностей на цьому етапі.
    # `BaseMainModel.state` вже визначає зв'язок ЗВІДТИ СЮДИ.
    # Зворотний зв'язок звідси (StatusModel -> SpecificModel) опціональний.

    # Зв'язок зі статусами членства в групах (з GroupMembershipModel.status_in_group_id)
    # TODO: Узгодити back_populates="status_in_group" з GroupMembershipModel
    group_memberships_with_this_status = relationship("GroupMembershipModel", back_populates="status_in_group", foreign_keys="[GroupMembershipModel.status_in_group_id]")

    # Зв'язок зі статусами запрошень до груп (з GroupInvitationModel.status_id)
    # TODO: Узгодити back_populates="status" з GroupInvitationModel
    group_invitations_with_this_status = relationship("GroupInvitationModel", back_populates="status", foreign_keys="[GroupInvitationModel.status_id]")

    # Зв'язок зі статусами призначень завдань (з TaskAssignmentModel.status_id)
    # TODO: Узгодити back_populates="status" з TaskAssignmentModel
    task_assignments_with_this_status = relationship("TaskAssignmentModel", back_populates="status", foreign_keys="[TaskAssignmentModel.status_id]")

    # Зв'язок зі статусами виконань завдань (з TaskCompletionModel.status_id)
    # TODO: Узгодити back_populates="status" з TaskCompletionModel
    task_completions_with_this_status = relationship("TaskCompletionModel", back_populates="status", foreign_keys="[TaskCompletionModel.status_id]")

    # Зв'язок зі статусами пропозицій завдань (з TaskProposalModel.status_id)
    # TODO: Узгодити back_populates="status" з TaskProposalModel
    task_proposals_with_this_status = relationship("TaskProposalModel", back_populates="status", foreign_keys="[TaskProposalModel.status_id]")

    # Зв'язок зі статусами звітів (з ReportModel.status_id)
    # TODO: Узгодити back_populates="status" з ReportModel
    reports_with_this_status = relationship("ReportModel", back_populates="status", foreign_keys="[ReportModel.status_id]")

    # Якщо TaskReviewModel матиме status_id для модерації:
    # task_reviews_with_this_status = relationship("TaskReviewModel", back_populates="status", foreign_keys="[TaskReviewModel.status_id]")

    # TODO: Розглянути додавання поля `order` (Integer) для можливості сортування статусів
    # у визначеному порядку (наприклад, для відображення у випадаючих списках).
    # order: Column[int] = Column(Integer, default=0, nullable=False)

    # TODO: Розглянути додавання поля `color` (String) для зберігання кольору статусу
    # (наприклад, для візуального виділення в інтерфейсі).
    # color: Column[str] = Column(String(7), nullable=True)  # Формат #RRGGBB

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
