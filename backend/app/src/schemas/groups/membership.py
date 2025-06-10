# backend/app/src/schemas/groups/membership.py
"""
Pydantic схеми для сутності "Членство в Групі" (GroupMembership).

Цей модуль визначає схеми для:
- Базового представлення членства (`GroupMembershipBaseSchema`).
- Створення нового запису про членство (`GroupMembershipCreateSchema`).
- Оновлення ролі в існуючому членстві (`GroupMembershipUpdateSchema`).
- Представлення даних про членство у відповідях API (`GroupMembershipSchema`).
"""
from datetime import datetime
from typing import Optional

from pydantic import Field, field_validator  # field_validator для валідації ролі

# Абсолютний імпорт базових схем та Enum
from backend.app.src.schemas.base import BaseSchema, TimestampedSchemaMixin
from backend.app.src.schemas.auth.user import UserPublicProfileSchema  # Для представлення користувача
from backend.app.src.core.dicts import GroupRole  # Enum для ролей в групі


class GroupMembershipBaseSchema(BaseSchema):
    """
    Базова схема для полів членства в групі.
    """
    user_id: int = Field(description="Ідентифікатор користувача.")
    group_id: int = Field(description="Ідентифікатор групи.")
    role: str = Field(
        default=GroupRole.MEMBER.value,
        description=f"Роль користувача в групі. Допустимі значення: {', '.join([r.value for r in GroupRole])}."
    )

    @field_validator('role')
    @classmethod
    def validate_role(cls, value: str) -> str:
        """Перевіряє, чи надане значення ролі є допустимим членом Enum GroupRole."""
        allowed_roles = {r.value for r in GroupRole}
        if value not in allowed_roles:
            # TODO i18n: Translatable error message
            raise ValueError(f"Недопустима роль '{value}'. Дозволені ролі: {', '.join(allowed_roles)}")
        return value

    # model_config успадковується з BaseSchema (from_attributes=True)


class GroupMembershipCreateSchema(
    BaseSchema):  # Не успадковує GroupMembershipBaseSchema напряму, щоб group_id не був у тілі запиту
    """
    Схема для створення нового запису про членство в групі.
    `group_id` зазвичай передається як параметр шляху (path parameter),
    `user_id` може бути в тілі запиту або визначатися інакше (наприклад, для запрошення).
    """
    user_id: int = Field(description="Ідентифікатор користувача, якого додають до групи.")
    role: str = Field(
        default=GroupRole.MEMBER.value,
        description=f"Роль, що призначається користувачеві в групі. За замовчуванням: '{GroupRole.MEMBER.value}'. Допустимі значення: {', '.join([r.value for r in GroupRole])}."
    )

    @field_validator('role')
    @classmethod
    def validate_role_on_create(cls, value: str) -> str:
        """Перевіряє роль при створенні (аналогічно до базової перевірки)."""
        allowed_roles = {r.value for r in GroupRole}
        if value not in allowed_roles:
            # TODO i18n: Translatable error message
            raise ValueError(f"Недопустима роль '{value}'. Дозволені ролі: {', '.join(allowed_roles)}")
        return value


class GroupMembershipUpdateSchema(BaseSchema):
    """
    Схема для оновлення ролі користувача в групі.
    Дозволяє оновлювати лише поле `role`.
    """
    role: str = Field(
        description=f"Нова роль користувача в групі. Допустимі значення: {', '.join([r.value for r in GroupRole])}.")

    @field_validator('role')
    @classmethod
    def validate_role_on_update(cls, value: str) -> str:
        """Перевіряє роль при оновленні."""
        allowed_roles = {r.value for r in GroupRole}
        if value not in allowed_roles:
            # TODO i18n: Translatable error message
            raise ValueError(f"Недопустима роль '{value}'. Дозволені ролі: {', '.join(allowed_roles)}")
        return value


class GroupMembershipSchema(GroupMembershipBaseSchema, TimestampedSchemaMixin):
    """
    Схема для представлення даних про членство у відповідях API.
    Включає інформацію про користувача та часові мітки.
    """
    # user_id, group_id, role успадковані з GroupMembershipBaseSchema
    # created_at, updated_at успадковані з TimestampedSchemaMixin

    user: Optional[UserPublicProfileSchema] = Field(None,
                                                    description="Публічний профіль користувача, що є членом групи.")
    # group: Optional[GroupSchema] = Field(None, description="Інформація про групу.") # Якщо потрібно показувати деталі групи


if __name__ == "__main__":
    # Демонстраційний блок для схем членства в групах.
    print("--- Pydantic Схеми для Членства в Групах (GroupMembership) ---")

    print("\nGroupMembershipBaseSchema (приклад):")
    base_data = {"user_id": 1, "group_id": 10, "role": GroupRole.ADMIN.value}
    base_instance = GroupMembershipBaseSchema(**base_data)
    print(base_instance.model_dump_json(indent=2))
    try:
        GroupMembershipBaseSchema(user_id=1, group_id=10, role="invalid_role")
    except Exception as e:
        print(f"Помилка валідації GroupMembershipBaseSchema (очікувано): {e}")

    print("\nGroupMembershipCreateSchema (приклад для створення):")
    create_data = {"user_id": 2, "role": GroupRole.MEMBER.value}
    create_instance = GroupMembershipCreateSchema(**create_data)
    print(create_instance.model_dump_json(indent=2))

    print("\nGroupMembershipUpdateSchema (приклад для оновлення):")
    update_data = {"role": GroupRole.ADMIN.value}
    update_instance = GroupMembershipUpdateSchema(**update_data)
    print(update_instance.model_dump_json(indent=2))

    print("\nGroupMembershipSchema (приклад відповіді API):")
    membership_response_data = {
        "user_id": 1,
        "group_id": 10,
        "role": GroupRole.ADMIN.value,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "user": {"id": 1, "name": "Адміністратор Групи"}  # TODO i18n (UserPublicProfileSchema)
    }
    membership_response_instance = GroupMembershipSchema(**membership_response_data)
    print(membership_response_instance.model_dump_json(indent=2, exclude_none=True))

    print("\nПримітка: Ці схеми використовуються для валідації та серіалізації даних членства в групах.")
    print(f"Використовується GroupRole Enum для поля 'role', наприклад: GroupRole.MEMBER = '{GroupRole.MEMBER.value}'")
