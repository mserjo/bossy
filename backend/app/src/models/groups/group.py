# backend/app/src/models/groups/group.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `GroupModel` для представлення груп користувачів.
Групи є ключовим елементом системи, дозволяючи об'єднувати користувачів для спільних завдань,
нарахування бонусів, спілкування тощо. Групи можуть мати ієрархічну структуру.
"""
from typing import Optional, List

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Integer # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship, Mapped, mapped_column  # type: ignore
import uuid # Для роботи з UUID

from backend.app.src.models.base import BaseMainModel # Успадковуємо від BaseMainModel

class GroupModel(BaseMainModel):
    """
    Модель для представлення груп користувачів.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор групи (успадковано).
        name (str): Назва групи (успадковано).
        description (str | None): Опис групи (успадковано).
        state_id (uuid.UUID | None): Статус групи (наприклад, "активна", "архівована", "неактивна").
                                     Посилається на StatusModel. (успадковано)
        group_id (uuid.UUID | None): Для самої моделі групи це поле не використовується і буде NULL.
                                     Воно призначене для сутностей, що належать до групи. (успадковано)

        parent_group_id (uuid.UUID | None): Ідентифікатор батьківської групи для ієрархічних груп.
                                            Якщо NULL, група є кореневою.
        group_type_id (uuid.UUID | None): Ідентифікатор типу групи (наприклад, "сім'я", "відділ").
                                          Посилається на GroupTypeModel.
        icon_file_id (uuid.UUID | None): Ідентифікатор файлу іконки групи (посилання на FileModel).

        # Налаштування, специфічні для групи, можуть бути винесені в окрему модель GroupSettingsModel,
        # але деякі ключові можуть бути тут для швидкого доступу.
        # Наприклад:
        # currency_name (str): Назва валюти бонусів у цій групі (наприклад, "бали", "зірочки").
        # allow_decimal_bonuses (bool): Чи дозволені дробові бонуси.
        # max_debt_allowed (Numeric | None): Максимально допустимий борг.

        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення запису (успадковано).
        deleted_at (datetime | None): Дата та час "м'якого" видалення (успадковано).
        is_deleted (bool): Прапорець "м'якого" видалення (успадковано).
        notes (str | None): Додаткові нотатки (успадковано).

    Зв'язки:
        parent_group (relationship): Зв'язок з батьківською групою (self-referential).
        child_groups (relationship): Список дочірніх груп (self-referential).
        group_type (relationship): Зв'язок з GroupTypeModel.
        members (relationship): Список учасників групи (через GroupMembershipModel).
        # TODO: Додати інші зв'язки:
        # - settings (GroupSettingsModel) - один-до-одного
        # - tasks (TaskModel) - один-до-багатьох
        # - rewards (RewardModel) - один-до-багатьох
        # - accounts (AccountModel) - один-до-багатьох (рахунки користувачів у цій групі)
        # - polls (PollModel) - один-до-багатьох
        # - group_invitations (GroupInvitationModel) - один-до-багатьох
        # - icon_file (FileModel) - один-до-одного (якщо icon_file_id використовується)
    """
    __tablename__ = "groups"

    # Ієрархія груп: посилання на батьківську групу
    parent_group_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("groups.id", name="fk_groups_parent_group_id"), nullable=True, index=True)

    # Тип групи (з довідника GroupTypeModel)
    group_type_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("group_types.id", name="fk_groups_group_type_id", ondelete="SET NULL"), nullable=True, index=True)

    # Іконка групи (посилання на модель файлів)
    icon_file_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("files.id", name="fk_groups_icon_file_id", ondelete="SET NULL"), nullable=True)

    # Шаблон, з якого була створена група (якщо є)
    created_from_template_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("group_templates.id", name="fk_groups_template_id", ondelete="SET NULL"), nullable=True, index=True)

    # --- Зв'язки (Relationships) ---

    # Зв'язок для ієрархії груп (батьківська група)
    parent_group: Mapped[Optional["GroupModel"]] = relationship(remote_side="GroupModel.id", back_populates="child_groups", lazy="selectin") # SQLAlchemy 2.0 style

    # Зв'язок для ієрархії груп (дочірні групи)
    child_groups: Mapped[List["GroupModel"]] = relationship(back_populates="parent_group", cascade="all, delete-orphan", lazy="selectin")

    # Зв'язок з типом групи
    group_type: Mapped[Optional["GroupTypeModel"]] = relationship(foreign_keys=[group_type_id], back_populates="groups_of_this_type", lazy="selectin")

    # Зв'язок з учасниками групи через проміжну таблицю GroupMembershipModel
    memberships: Mapped[List["GroupMembershipModel"]] = relationship(back_populates="group", cascade="all, delete-orphan")

    # Зв'язок з налаштуваннями групи (один-до-одного)
    settings: Mapped[Optional["GroupSettingsModel"]] = relationship(back_populates="group", uselist=False, cascade="all, delete-orphan")

    # Зв'язок із завданнями, що належать цій групі
    tasks: Mapped[List["TaskModel"]] = relationship(back_populates="group", cascade="all, delete-orphan")

    # Зв'язок з нагородами, доступними в цій групі
    rewards: Mapped[List["RewardModel"]] = relationship(back_populates="group", cascade="all, delete-orphan")

    # Зв'язок з рахунками користувачів у цій групі
    accounts_in_group: Mapped[List["AccountModel"]] = relationship(back_populates="group", cascade="all, delete-orphan")

    # Зв'язок з опитуваннями/голосуваннями в групі
    polls: Mapped[List["PollModel"]] = relationship(back_populates="group", cascade="all, delete-orphan")

    # Зв'язок із запрошеннями до групи
    invitations: Mapped[List["GroupInvitationModel"]] = relationship(back_populates="group", cascade="all, delete-orphan")

    # Зв'язок з файлом іконки
    icon_file: Mapped[Optional["FileModel"]] = relationship(foreign_keys=[icon_file_id], back_populates="group_icon_for", lazy="selectin") # Додано back_populates

    # Зв'язок з шаблоном, з якого створена група
    created_from_template: Mapped[Optional["GroupTemplateModel"]] = relationship(
        foreign_keys=[created_from_template_id],
        back_populates="groups_created_from_this_template", # Назва зворотного зв'язку в GroupTemplateModel
        lazy="selectin"
    )

    # Поле `group_id` з `BaseMainModel` для самої `GroupModel` не використовується і буде `NULL`.
    # Це поле призначене для сутностей, які належать до певної групи.
    # `state_id` з `BaseMainModel` використовується для статусу групи.
    # state = relationship("StatusModel", foreign_keys=[state_id]) # Вже є в BaseMainModel, якщо там розкоментовано

    # Зв'язок з файлами, що належать до контексту цієї групи
    context_files: Mapped[List["FileModel"]] = relationship(
        back_populates="group_context",
        foreign_keys="[FileModel.group_context_id]" # Вказуємо зовнішній ключ з FileModel
    )

    # Зв'язок з пропозиціями завдань для цієї групи
    task_proposals: Mapped[List["TaskProposalModel"]] = relationship(back_populates="group", cascade="all, delete-orphan")

    # Зв'язок з досягненнями рівнів користувачами в цій групі
    user_level_achievements: Mapped[List["UserLevelModel"]] = relationship(back_populates="group", foreign_keys="[UserLevelModel.group_id]", cascade="all, delete-orphan")

    # Зв'язок з налаштуваннями бейджів для цієї групи
    badges: Mapped[List["BadgeModel"]] = relationship(back_populates="group", foreign_keys="[BadgeModel.group_id]", cascade="all, delete-orphan")

    # Зв'язок з історією рейтингів в цій групі
    ratings_history: Mapped[List["RatingModel"]] = relationship(back_populates="group", foreign_keys="[RatingModel.group_id]", cascade="all, delete-orphan")

    # Зв'язок зі сповіщеннями, що стосуються цієї групи
    notifications: Mapped[List["NotificationModel"]] = relationship(back_populates="group", foreign_keys="[NotificationModel.group_id]", cascade="all, delete-orphan")

    # Зв'язок зі звітами, що стосуються цієї групи
    reports: Mapped[List["ReportModel"]] = relationship(back_populates="group", foreign_keys="[ReportModel.group_id]", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі GroupModel.
        """
        return f"<{self.__class__.__name__}(id='{self.id}', name='{self.name}')>"

# TODO: Перевірити відповідність `technical-task.md`:
# - "групи можуть бути ієрархічними" - реалізовано через `parent_group_id`.
# - "адмін вищої групи має доступ та повноваження адміна в усіх підпорядкованих" - логіка для сервісного шару.
# - "створення/редагування/видалення" - стандартні CRUD.
# - "масова розсилка повідомлень ... в рамках групи" - потребує зв'язку з повідомленнями.
# - "опитування/голосування користувачів групи" - реалізовано через зв'язок з `PollModel`.
# - "покинути групу" - логіка для `GroupMembershipModel`.
# - "при створенні групи, адмін обирає серед існуючих шаблонів груп" - потребує зв'язку з `GroupTemplateModel`.

# TODO: Узгодити назву таблиці `groups` з `structure-claude-v3.md`. Відповідає.
# Поля `name`, `description`, `state_id` успадковані. `group_id` успадковане, але тут `NULL`.
# Додані `parent_group_id`, `group_type_id`, `icon_file_id`.
# Зв'язки визначені для ієрархії, типу групи, учасників, налаштувань, завдань, нагород, рахунків, опитувань, запрошень.
# `lazy="joined"` використовується для деяких зв'язків для автоматичного завантаження пов'язаних об'єктів
# при запиті основного об'єкта. Це може бути зручно, але потрібно стежити за продуктивністю.
# Для зв'язків "один-до-багатьох" (наприклад, `child_groups`, `memberships`) `lazy="select"` (за замовчуванням)
# або `lazy="dynamic"` може бути кращим для великих об'ємів даних. Поки що залишено так для простоти.
# `cascade="all, delete-orphan"` використовується для автоматичного видалення пов'язаних об'єктів
# при видаленні групи (наприклад, членства, налаштування, завдання в цій групі).
# Це потрібно ретельно продумати для кожного зв'язку. Наприклад, чи потрібно видаляти всі завдання
# при видаленні групи, чи архівувати їх, чи перепризначати.
# Поки що встановлено каскадне видалення для більшості залежних сутностей.
# Зв'язок з `FileModel` для `icon_file_id` потребуватиме створення `FileModel`.
# Зв'язок з `StatusModel` для `state_id` успадкований.
# Зв'язок з `GroupTypeModel` для `group_type_id` визначений.
# Зв'язок з `GroupSettingsModel` визначений як один-до-одного.
# Зв'язок з `GroupMembershipModel` для учасників.
# Зв'язок з `TaskModel`, `RewardModel`, `AccountModel`, `PollModel`, `GroupInvitationModel`.
# Все виглядає логічно.
