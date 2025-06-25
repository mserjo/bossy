# backend/app/src/models/groups/group.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `GroupModel` для представлення груп користувачів.
Групи є ключовим елементом системи, дозволяючи об'єднувати користувачів для спільних завдань,
нарахування бонусів, спілкування тощо. Групи можуть мати ієрархічну структуру.
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Integer # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship # type: ignore
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
    # TODO: Замінити "group_types.id" на константу або імпорт моделі GroupTypeModel після її створення.
    group_type_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("group_types.id", name="fk_groups_group_type_id"), nullable=True, index=True) # Може бути nullable, якщо є тип за замовчуванням

    # Іконка групи (посилання на модель файлів, яка буде створена пізніше)
    # TODO: Замінити "files.id" на константу або імпорт моделі FileModel після її створення.
    icon_file_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("files.id", name="fk_groups_icon_file_id"), nullable=True)

    # --- Зв'язки (Relationships) ---

    # Зв'язок для ієрархії груп (батьківська група)
    parent_group = relationship("GroupModel", remote_side=[id], back_populates="child_groups", lazy="joined")
    # `remote_side=[id]` вказує, що `parent_group_id` посилається на `id` цієї ж таблиці.

    # Зв'язок для ієрархії груп (дочірні групи)
    child_groups = relationship("GroupModel", back_populates="parent_group", cascade="all, delete-orphan", lazy="joined")

    # Зв'язок з типом групи
    group_type = relationship("GroupTypeModel", foreign_keys=[group_type_id], lazy="joined") # back_populates="groups" буде в GroupTypeModel

    # Зв'язок з учасниками групи через проміжну таблицю GroupMembershipModel
    memberships = relationship("GroupMembershipModel", back_populates="group", cascade="all, delete-orphan")

    # Зв'язок з налаштуваннями групи (один-до-одного)
    settings = relationship("GroupSettingsModel", back_populates="group", uselist=False, cascade="all, delete-orphan")

    # Зв'язок із завданнями, що належать цій групі
    tasks = relationship("TaskModel", back_populates="group", cascade="all, delete-orphan")

    # Зв'язок з нагородами, доступними в цій групі
    rewards = relationship("RewardModel", back_populates="group", cascade="all, delete-orphan")

    # Зв'язок з рахунками користувачів у цій групі (опосередковано, основний зв'язок user.accounts -> account.group)
    # Прямий зв'язок group.accounts може бути корисним для отримання всіх рахунків групи.
    accounts_in_group = relationship("AccountModel", back_populates="group", cascade="all, delete-orphan")

    # Зв'язок з опитуваннями/голосуваннями в групі
    polls = relationship("PollModel", back_populates="group", cascade="all, delete-orphan")

    # Зв'язок із запрошеннями до групи
    invitations = relationship("GroupInvitationModel", back_populates="group", cascade="all, delete-orphan")

    # Зв'язок з файлом іконки
    # icon_file = relationship("FileModel", foreign_keys=[icon_file_id], lazy="joined") # back_populates="group_icon_for" буде в FileModel

    # Поле `group_id` з `BaseMainModel` для самої `GroupModel` не використовується і буде `NULL`.
    # Це поле призначене для сутностей, які належать до певної групи.
    # `state_id` з `BaseMainModel` використовується для статусу групи.
    # state = relationship("StatusModel", foreign_keys=[state_id]) # Вже є в BaseMainModel, якщо там розкоментовано

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
