# backend/app/src/models/dictionaries/user_role.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `UserRoleModel` для довідника "Ролі користувачів".
Ролі користувачів використовуються для визначення прав доступу та повноважень користувачів
в системі або в межах конкретних груп. Наприклад, "superadmin", "admin" (адміністратор групи), "user" (звичайний користувач).

Модель `UserRoleModel` успадковує `BaseDictModel`, що надає їй стандартний набір полів
(id, name, description, code, state_id, group_id, created_at, updated_at, deleted_at, is_deleted, notes)
та функціональність.
"""

from sqlalchemy import UniqueConstraint # type: ignore # Для визначення обмежень унікальності
# from sqlalchemy.orm import relationship # type: ignore # Для визначення зв'язків (якщо потрібно)

from backend.app.src.models.dictionaries.base import BaseDictModel # Імпорт базової моделі для довідників

# TODO: Визначити, чи потрібні специфічні поля для моделі UserRoleModel, окрім успадкованих.
# Наприклад, рівень доступу (числовий), або список дозволів (якщо не реалізовано окремою системою дозволів).

class UserRoleModel(BaseDictModel):
    """
    Модель для довідника "Ролі користувачів".

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор ролі (успадковано).
        name (str): Назва ролі, що відображається (наприклад, "Супер Адміністратор", "Адміністратор Групи") (успадковано).
        description (str | None): Детальний опис ролі та її повноважень (успадковано).
        code (str): Унікальний символьний код ролі (наприклад, "superadmin", "group_admin", "user") (успадковано).
                    Використовується для програмної ідентифікації ролі.
        state_id (uuid.UUID | None): Ідентифікатор стану самого запису ролі (успадковано, використання під питанням для довідників).
        group_id (uuid.UUID | None): Ідентифікатор групи, якщо роль специфічна для групи (успадковано).
                                     Зазвичай ролі є глобальними, тому це поле буде NULL.
                                     Однак, можливий сценарій кастомних ролей в межах групи.
        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення запису (успадковано).
        deleted_at (datetime | None): Дата та час "м'якого" видалення запису (успадковано).
        is_deleted (bool): Прапорець, що вказує, чи запис "м'яко" видалено (успадковано).
        notes (str | None): Додаткові нотатки (успадковано).

    Ім'я таблиці в базі даних: `user_roles`.
    """
    __tablename__ = "user_roles"

    # Обмеження унікальності для поля `code`.
    # Гарантує, що кожен символьний код ролі є унікальним.
    # Ролі зазвичай глобальні, тому унікальність `code` є важливою.
    # Якщо передбачаються кастомні ролі на рівні груп, тоді `UniqueConstraint('group_id', 'code')`
    # TODO: Уточнити, чи ролі завжди глобальні, чи можуть бути специфічні для груп.
    # Поки що робимо `code` унікальним глобально.
    __table_args__ = (
        UniqueConstraint('code', name='uq_user_roles_code'),
        # Ролі зазвичай глобальні, тому group_id тут не використовується для унікальності.
        # Якщо б були кастомні ролі на рівні групи, то:
        # UniqueConstraint('group_id', 'code', name='uq_user_roles_group_code', postgresql_where=(Column('group_id').isnot(None))),
        # UniqueConstraint('code', name='uq_user_roles_global_code', postgresql_where=(Column('group_id').is_(None))),
    )

    # --- Зворотні зв'язки (Relationships) ---
    # Зв'язок з GroupMembershipModel (роль користувача в групі)
    # TODO: Узгодити back_populates="role" з GroupMembershipModel
    group_memberships_with_this_role = relationship("GroupMembershipModel", back_populates="role", foreign_keys="[GroupMembershipModel.user_role_id]")

    # Зв'язок з GroupInvitationModel (роль, що призначається при запрошенні)
    # TODO: Узгодити back_populates="role_to_assign" з GroupInvitationModel
    group_invitations_assigning_this_role = relationship("GroupInvitationModel", back_populates="role_to_assign", foreign_keys="[GroupInvitationModel.role_to_assign_id]")

    # Якщо UserModel матиме поле default_role_id або щось подібне для глобальної ролі користувача
    # (окрім user_type_code, який посилається на інший довідник або Enum):
    # users_with_this_as_default_role = relationship("UserModel", back_populates="default_role", foreign_keys="[UserModel.default_role_id]")

    # TODO: Розглянути можливість додавання поля `permissions` (наприклад, JSON або зв'язок
    # з окремою таблицею дозволів), якщо система дозволів буде базуватися безпосередньо на ролях.
    # Або ж логіка дозволів може бути реалізована в коді на основі `code` ролі.

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі UserRoleModel.
        Наприклад: <UserRoleModel(id='...', name='Адміністратор Групи', code='group_admin')>
        """
        return f"<{self.__class__.__name__}(id='{self.id}', name='{self.name}', code='{self.code}')>"

# Приклади початкових даних для довідника ролей (згідно technical-task.md):
# - superadmin (code: 'superadmin', name: 'Супер Адміністратор') - доступ до всієї системи.
# - admin (code: 'group_admin', name: 'Адміністратор Групи') - доступ до управління конкретною групою.
# - user (code: 'group_user', name: 'Користувач Групи') - звичайний користувач в межах групи.

# TODO: Перевірити відповідність `technical-task.md` та `structure-claude-v3.md`.
# `BaseDictModel` забезпечує необхідні поля. `group_id` успадковано, для ролей він,
# скоріш за все, буде `None`, оскільки ролі описані як глобальні (superadmin) або
# відносно групи (admin, user), але сам тип ролі визначається глобально.
# Назва таблиці `user_roles` відповідає структурі.
# Унікальність `code` встановлена.
# Подальші поля (наприклад, `permissions`) можуть бути додані, якщо це буде потрібно
# для реалізації системи прав доступу.
