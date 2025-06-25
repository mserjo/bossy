# backend/app/src/models/teams/team.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `TeamModel` для представлення команд користувачів
в межах групи. Команди можуть використовуватися для виконання спільних завдань
або участі у змаганнях.
"""

from sqlalchemy import Column, String, Text, ForeignKey, Integer # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship # type: ignore
import uuid # Для роботи з UUID

# Використовуємо BaseMainModel, оскільки команда має назву, опис, статус (активна/неактивна),
# і належить до групи.
from backend.app.src.models.base import BaseMainModel

class TeamModel(BaseMainModel):
    """
    Модель для представлення команд користувачів в групі.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор команди (успадковано).
        name (str): Назва команди (успадковано).
        description (str | None): Опис команди, її цілі (успадковано).
        state_id (uuid.UUID | None): Статус команди (наприклад, "активна", "розформована").
                                     Посилається на StatusModel. (успадковано)
        group_id (uuid.UUID): Ідентифікатор групи, до якої належить команда. (успадковано, тут буде NOT NULL)

        leader_user_id (uuid.UUID | None): Ідентифікатор користувача-лідера (капітана) команди.
                                           Посилається на UserModel.
        icon_file_id (uuid.UUID | None): Ідентифікатор файлу іконки команди (посилання на FileModel).

        # Додаткові поля
        max_members (int | None): Максимальна кількість учасників у команді.

        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення запису (успадковано).
        deleted_at (datetime | None): Дата та час "м'якого" видалення (успадковано).
        is_deleted (bool): Прапорець "м'якого" видалення (успадковано).
        notes (str | None): Додаткові нотатки (успадковано).

    Зв'язки:
        group (relationship): Зв'язок з GroupModel.
        leader (relationship): Зв'язок з UserModel (лідер команди).
        members (relationship): Список учасників команди (через TeamMembershipModel).
        tasks_assigned (relationship): Список завдань, призначених цій команді (TaskModel).
        # TODO: Додати інші зв'язки:
        # - status (StatusModel) - вже є через state_id.
        # - icon_file (FileModel) - якщо icon_file_id використовується.
    """
    __tablename__ = "teams"

    # group_id успадковано і має бути NOT NULL.
    # ForeignKey("groups.id") вже є в BaseMainModel.

    # Лідер (капітан) команди. Може бути необов'язковим.
    # TODO: Замінити "users.id" на константу або імпорт моделі UserModel.
    leader_user_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_teams_leader_id"), nullable=True, index=True)

    # Іконка команди (посилання на модель файлів)
    # TODO: Замінити "files.id" на константу або імпорт моделі FileModel.
    icon_file_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("files.id", name="fk_teams_icon_file_id"), nullable=True)

    max_members: Column[int | None] = Column(Integer, nullable=True) # NULL означає без обмежень

    # --- Зв'язки (Relationships) ---
    # group успадковано з BaseMainModel.
    # group = relationship("GroupModel", foreign_keys=[group_id], back_populates="teams")
    # Потрібно переконатися, що foreign_keys=[group_id] не конфліктує.
    # Оскільки group_id в BaseMainModel вже є ForeignKey, можна просто:
    group = relationship("GroupModel", foreign_keys="TeamModel.group_id") # back_populates="teams" буде в GroupModel


    leader = relationship("UserModel", foreign_keys=[leader_user_id]) # back_populates="led_teams" буде в UserModel

    # Учасники команди через проміжну таблицю TeamMembershipModel
    memberships = relationship("TeamMembershipModel", back_populates="team", cascade="all, delete-orphan")

    # Завдання, призначені цій команді
    # Це буде зворотний зв'язок від TaskModel.team_id
    tasks_assigned = relationship("TaskModel", back_populates="team") # foreign_keys=[TaskModel.team_id]

    # Зв'язок зі статусом (успадкований з BaseMainModel, якщо там визначено relationship `state`)
    # state = relationship("StatusModel", foreign_keys=[state_id])

    # icon_file = relationship("FileModel", foreign_keys=[icon_file_id]) # back_populates="team_icon_for" буде в FileModel

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі TeamModel.
        """
        return f"<{self.__class__.__name__}(id='{self.id}', name='{self.name}', group_id='{self.group_id}')>"

# TODO: Перевірити відповідність `technical-task.md`:
# - "завдання можуть бути командними - можливість об'єднувати користувачів у команди для виконання спільних завдань"
#   - Ця модель для команд. TaskModel матиме поле `team_id`.
# - "або участі у змаганнях між командами/користувачами всередині групи"
#   - Модель команди є основою для таких змагань.

# TODO: Узгодити назву таблиці `teams` з `structure-claude-v3.md`. Відповідає.
# Використання `BaseMainModel` як основи. `group_id` має бути NOT NULL.
# Поля `leader_user_id`, `icon_file_id`, `max_members` додані.
# Зв'язки визначені.
# `cascade="all, delete-orphan"` для `memberships` означає, що при видаленні команди
# записи про членство в ній також видаляються.
# Зв'язок `group` уточнено з `foreign_keys="TeamModel.group_id"`.
# Зв'язок `tasks_assigned` з `TaskModel`.
# Поле `name` з `BaseMainModel` - назва команди.
# `description`, `state_id`, `notes`, `deleted_at`, `is_deleted` - успадковані.
# `group_id` - успадковане, але тут має бути обов'язковим (контроль на рівні логіки/валідації).
# Все виглядає логічно.
# Лідер команди може мати спеціальні права в межах команди (наприклад, додавати/видаляти учасників).
# Це буде реалізовано на сервісному рівні.
# Максимальна кількість учасників (`max_members`) - корисне налаштування.
# Іконка для візуального представлення команди.
# Статус команди (активна, розформована тощо) через `state_id`.
