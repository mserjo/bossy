# backend/app/src/models/groups/membership.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `GroupMembershipModel`.
Ця модель представляє зв'язок "багато-до-багатьох" між користувачами (`UserModel`)
та групами (`GroupModel`), а також зберігає роль користувача в конкретній групі.
"""

from sqlalchemy import Column, ForeignKey, DateTime, UniqueConstraint, Text # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship # type: ignore
import uuid # Для роботи з UUID
from datetime import datetime # Для роботи з датами та часом

from backend.app.src.models.base import BaseModel # Використовуємо BaseModel для id, created_at, updated_at

class GroupMembershipModel(BaseModel):
    """
    Модель для представлення членства користувача в групі та його ролі в цій групі.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор запису про членство (успадковано).
        user_id (uuid.UUID): Ідентифікатор користувача.
        group_id (uuid.UUID): Ідентифікатор групи.
        user_role_id (uuid.UUID): Ідентифікатор ролі користувача в цій групі (з довідника UserRoleModel).
        joined_at (datetime): Дата та час приєднання користувача до групи (може бути `created_at`).

        # Додаткові поля, якщо потрібні
        status_in_group_id (uuid.UUID | None): Специфічний статус користувача в групі (наприклад, "активний", "тимчасово відсутній").
                                               Посилається на StatusModel.
        notes (str | None): Нотатки щодо членства цього користувача в групі.

        created_at (datetime): Дата та час створення запису (успадковано, відповідає `joined_at`).
        updated_at (datetime): Дата та час останнього оновлення запису (успадковано).

    Зв'язки:
        user (relationship): Зв'язок з UserModel.
        group (relationship): Зв'язок з GroupModel.
        role (relationship): Зв'язок з UserRoleModel.
        status_in_group (relationship): Зв'язок зі StatusModel.
    """
    __tablename__ = "group_memberships"

    user_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    group_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)

    # Роль користувача в цій конкретній групі.
    # TODO: Замінити "user_roles.id" на константу або імпорт моделі UserRoleModel.
    user_role_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("user_roles.id", name="fk_group_memberships_user_role_id"), nullable=False, index=True)

    # `created_at` з BaseModel може слугувати як `joined_at`.
    # Якщо потрібне окреме поле, можна додати:
    # joined_at: Column[DateTime] = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Статус користувача саме в цій групі (якщо відрізняється від його глобального статусу або ролі).
    # Наприклад, користувач може бути "активним" в системі, але "тимчасово відсутнім" в конкретній групі.
    # TODO: Замінити "statuses.id" на константу або імпорт моделі StatusModel.
    status_in_group_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("statuses.id", name="fk_group_memberships_status_id"), nullable=True, index=True)

    # Нотатки, специфічні для цього членства.
    notes: Column[str | None] = Column(Text, nullable=True)

    # --- Зв'язки (Relationships) ---
    user = relationship("UserModel", back_populates="group_memberships")
    group = relationship("GroupModel", back_populates="memberships") # memberships - назва зв'язку в GroupModel

    # Зв'язок з роллю користувача
    role = relationship("UserRoleModel", foreign_keys=[user_role_id]) # back_populates="group_memberships" буде в UserRoleModel

    # Зв'язок зі статусом членства в групі
    status_in_group = relationship("StatusModel", foreign_keys=[status_in_group_id]) # back_populates="group_member_statuses" буде в StatusModel

    # Обмеження унікальності: один користувач може мати лише одну роль в одній групі.
    __table_args__ = (
        UniqueConstraint('user_id', 'group_id', name='uq_user_group_membership'),
    )

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі GroupMembershipModel.
        """
        return f"<{self.__class__.__name__}(user_id='{self.user_id}', group_id='{self.group_id}', role_id='{self.user_role_id}')>"

# TODO: Перевірити відповідність `technical-task.md`:
# - "+ додаткова таблиця (користувач - група - роль)" - це ця модель.
# - "якщо адмін групи видалив користувача, то видаляється лише зв'язка "користувач - група"" - `ondelete="CASCADE"`
#   для `user_id` та `group_id` означає, що якщо користувач або група видаляються, то цей запис членства також видаляється.
#   Це відповідає логіці.
# - "користувач, який створив групу автоматично стає адміном групи" - логіка для сервісного шару при створенні групи.
# - "в різних групах може мати роль користувач/адмін групи" - реалізовано через `user_role_id`.

# TODO: Узгодити назву таблиці `group_memberships` з `structure-claude-v3.md`. Відповідає.
# Використання `BaseModel` як основи.
# Ключові поля `user_id`, `group_id`, `user_role_id` визначені з відповідними ForeignKey.
# `ondelete="CASCADE"` для `user_id` та `group_id`.
# `UniqueConstraint` для пари `(user_id, group_id)` забезпечує, що користувач не може бути членом однієї групи двічі.
# Додаткові поля `status_in_group_id` та `notes` для більшої гнучкості.
# Зв'язки з `UserModel`, `GroupModel`, `UserRoleModel`, `StatusModel` визначені.
# `created_at` може використовуватися як дата приєднання.
# Все виглядає логічно.
