# backend/app/src/models/teams/membership.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `TeamMembershipModel`.
Ця модель представляє зв'язок "багато-до-багатьох" між користувачами (`UserModel`)
та командами (`TeamModel`), фіксуючи, хто є членом якої команди.
Може також зберігати роль користувача в команді (якщо є така потреба, окрім лідера).
"""

from sqlalchemy import Column, ForeignKey, DateTime, UniqueConstraint, String # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship # type: ignore
import uuid # Для роботи з UUID
from datetime import datetime # Для роботи з датами та часом

from backend.app.src.models.base import BaseModel # Використовуємо BaseModel

class TeamMembershipModel(BaseModel):
    """
    Модель для представлення членства користувача в команді.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор запису про членство (успадковано).
        user_id (uuid.UUID): Ідентифікатор користувача.
        team_id (uuid.UUID): Ідентифікатор команди.
        role_in_team (str | None): Роль користувача в команді (наприклад, "member", "sub_leader").
                                   Лідер команди визначається в TeamModel.leader_user_id.
        joined_at (datetime): Дата та час приєднання користувача до команди (може бути `created_at`).

        created_at (datetime): Дата та час створення запису (успадковано, відповідає `joined_at`).
        updated_at (datetime): Дата та час останнього оновлення (успадковано).

    Зв'язки:
        user (relationship): Зв'язок з UserModel.
        team (relationship): Зв'язок з TeamModel.
    """
    __tablename__ = "team_memberships"

    user_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)

    # Роль користувача в команді, якщо потрібна більш гранульована диференціація,
    # окрім лідера, визначеного в TeamModel.
    # Наприклад, "учасник", "заступник лідера", "скарбник" тощо.
    # TODO: Визначити Enum або довідник для ролей в команді, якщо вони будуть стандартизовані.
    role_in_team: Column[str | None] = Column(String(100), nullable=True)

    # `created_at` з BaseModel може слугувати як `joined_at`.

    # --- Зв'язки (Relationships) ---
    user = relationship("UserModel", foreign_keys=[user_id]) # back_populates="team_memberships" буде в UserModel
    team = relationship("TeamModel", back_populates="memberships") # memberships - назва зв'язку в TeamModel

    # Обмеження унікальності: один користувач може бути членом однієї команди лише один раз.
    __table_args__ = (
        UniqueConstraint('user_id', 'team_id', name='uq_user_team_membership'),
    )

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі TeamMembershipModel.
        """
        return f"<{self.__class__.__name__}(user_id='{self.user_id}', team_id='{self.team_id}')>"

# TODO: Перевірити відповідність `technical-task.md`.
# - "можливість об'єднувати користувачів у команди" - ця модель реалізує членство в командах.

# TODO: Узгодити назву таблиці `team_memberships` з `structure-claude-v3.md`. Відповідає.
# Використання `BaseModel` як основи.
# Ключові поля: `user_id`, `team_id`.
# Додаткове поле `role_in_team` для можливих специфічних ролей у команді.
# `ondelete="CASCADE"` для `user_id` та `team_id` (видалення членства при видаленні користувача або команди).
# `UniqueConstraint` для `(user_id, team_id)`.
# Зв'язки визначені.
# Все виглядає логічно.
# `created_at` використовується як дата приєднання до команди.
# Лідер команди визначається полем `leader_user_id` в `TeamModel`.
# Якщо користувач є лідером, він також повинен мати запис у `TeamMembershipModel` як член команди.
# Це потрібно буде забезпечити логікою на сервісному рівні.
# Або ж, якщо лідер не вважається звичайним членом, то це поле `role_in_team` може бути використане
# для позначення "лідер", але це дублювало б інформацію.
# Краще, щоб лідер був також членом команди.
# Поле `role_in_team` залишене для гнучкості, якщо виникне потреба в інших ролях всередині команди.
# Якщо таких ролей не передбачається, поле можна видалити.
# Поки що залишаємо `nullable=True`.
