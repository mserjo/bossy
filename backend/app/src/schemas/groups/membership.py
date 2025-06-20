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

from pydantic import Field  # field_validator видалено, оскільки більше не використовується

# Абсолютний імпорт базових схем та Enum
from backend.app.src.schemas.base import BaseSchema, TimestampedSchemaMixin
from backend.app.src.schemas.auth.user import UserPublicProfileSchema  # Для представлення користувача
from backend.app.src.core.dicts import GroupRole  # Enum для ролей в групі
from backend.app.src.config.logging import get_logger 
logger = get_logger(__name__)


class GroupMembershipBaseSchema(BaseSchema):
    """
    Базова схема для полів членства в групі.
    """
    user_id: int = Field(description="Ідентифікатор користувача.")
    group_id: int = Field(description="Ідентифікатор групи.")
    role: GroupRole = Field(
        default=GroupRole.MEMBER,
        description="Роль користувача в групі."
    )

    # Валідатор validate_role більше не потрібен, Pydantic обробляє Enum

    # model_config успадковується з BaseSchema (from_attributes=True)


class GroupMembershipCreateSchema(
    BaseSchema):  # Не успадковує GroupMembershipBaseSchema напряму, щоб group_id не був у тілі запиту
    """
    Схема для створення нового запису про членство в групі.
    `group_id` зазвичай передається як параметр шляху (path parameter),
    `user_id` може бути в тілі запиту або визначатися інакше (наприклад, для запрошення).
    """
    user_id: int = Field(description="Ідентифікатор користувача, якого додають до групи.")
    role: GroupRole = Field(
        default=GroupRole.MEMBER,
        description="Роль, що призначається користувачеві в групі."
    )

    # Валідатор validate_role_on_create більше не потрібен


class GroupMembershipUpdateSchema(BaseSchema):
    """
    Схема для оновлення ролі користувача в групі.
    Дозволяє оновлювати лише поле `role`.
    """
    role: GroupRole = Field(description="Нова роль користувача в групі.")

    # Валідатор validate_role_on_update більше не потрібен


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
    logger.info("--- Pydantic Схеми для Членства в Групах (GroupMembership) ---")

    logger.info("\nGroupMembershipBaseSchema (приклад):")
    base_data = {"user_id": 1, "group_id": 10, "role": GroupRole.ADMIN} # Використовуємо Enum
    base_instance = GroupMembershipBaseSchema(**base_data)
    logger.info(base_instance.model_dump_json(indent=2))
    try:
        GroupMembershipBaseSchema(user_id=1, group_id=10, role="invalid_role") # Pydantic валідує Enum
    except Exception as e:
        logger.info(f"Помилка валідації GroupMembershipBaseSchema (очікувано): {e}")

    logger.info("\nGroupMembershipCreateSchema (приклад для створення):")
    create_data = {"user_id": 2, "role": GroupRole.MEMBER} # Використовуємо Enum
    create_instance = GroupMembershipCreateSchema(**create_data)
    logger.info(create_instance.model_dump_json(indent=2))

    logger.info("\nGroupMembershipUpdateSchema (приклад для оновлення):")
    update_data = {"role": GroupRole.ADMIN} # Використовуємо Enum
    update_instance = GroupMembershipUpdateSchema(**update_data)
    logger.info(update_instance.model_dump_json(indent=2))

    logger.info("\nGroupMembershipSchema (приклад відповіді API):")
    membership_response_data = {
        "user_id": 1,
        "group_id": 10,
        "role": GroupRole.ADMIN, # Використовуємо Enum
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "user": {"id": 1, "name": "Адміністратор Групи"}  # TODO i18n (UserPublicProfileSchema)
    }
    membership_response_instance = GroupMembershipSchema(**membership_response_data)
    logger.info(membership_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Ці схеми використовуються для валідації та серіалізації даних членства в групах.")
    logger.info(f"Використовується GroupRole Enum для поля 'role', наприклад: GroupRole.MEMBER = '{GroupRole.MEMBER.value}'")
