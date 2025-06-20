# backend/app/src/schemas/groups/invitation.py
"""
Pydantic схеми для сутності "Запрошення до Групи" (GroupInvitation).

Цей модуль визначає схеми для:
- Базового представлення запрошення (`GroupInvitationBaseSchema`).
- Створення нового запрошення (`GroupInvitationCreateSchema`).
- Оновлення статусу запрошення (`GroupInvitationUpdateSchema`).
- Представлення даних про запрошення у відповідях API (`GroupInvitationSchema`).
- Прийняття запрошення за кодом (`GroupInvitationAcceptSchema`).
"""
from datetime import datetime
from typing import Optional

from pydantic import Field, EmailStr, field_validator

# Абсолютний імпорт базових схем та Enum
from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin, TimestampedSchemaMixin
from backend.app.src.core.dicts import GroupRole, InvitationStatus  # Enum для ролей в групі та статусу запрошення
from datetime import timedelta
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


class GroupInvitationBaseSchema(BaseSchema):
    """
    Базова схема для полів запрошення до групи.
    """
    email: Optional[EmailStr] = Field(None,
                                      description="Електронна пошта запрошеного користувача (якщо запрошення по email).")
    # TODO: Додати валідацію номера телефону, коли буде доступний валідатор.
    phone_number: Optional[str] = Field(None, max_length=30,
                                        description="Номер телефону запрошеного (якщо запрошення по SMS).")
    role_to_assign: GroupRole = Field(
        default=GroupRole.MEMBER,
        description=f"Роль, яка буде призначена користувачеві при прийнятті запрошення."
    )

    # Валідатор validate_role_to_assign більше не потрібен, Pydantic обробляє Enum

    # model_config успадковується з BaseSchema (from_attributes=True)


class GroupInvitationCreateSchema(GroupInvitationBaseSchema):
    """
    Схема для створення нового запрошення до групи.
    `group_id` зазвичай передається як параметр шляху.
    `expires_at` може бути встановлено сервісом за замовчуванням (наприклад, +7 днів).
    """
    # email або phone_number мають бути надані, або це має бути "загальне" запрошення з кодом.
    # Ця логіка валідації (хоча б одне з полів) може бути додана за допомогою root_validator.
    # Наразі поля опціональні, але це може бути посилено.
    expires_at: Optional[datetime] = Field(None,
                                           description="Час закінчення терміну дії запрошення (необов'язково, може встановлюватися сервером).")

    # @root_validator(pre=True) # Pydantic v1 style, for v2 use model_validator
    # @model_validator(mode='before') # Pydantic v2 style
    # def check_email_or_phone_present(cls, values):
    #     if not values.get('email') and not values.get('phone_number'):
    #         # TODO i18n: Translatable error message
    #         raise ValueError('Має бути надано email або номер телефону для запрошення.')
    #     return values
    pass


class GroupInvitationUpdateSchema(BaseSchema):
    """
    Схема для оновлення статусу запрошення (наприклад, скасування).
    """
    status: InvitationStatus = Field(description="Новий статус запрошення.")


class GroupInvitationSchema(GroupInvitationBaseSchema, IDSchemaMixin, TimestampedSchemaMixin):
    """
    Схема для представлення даних про запрошення у відповідях API.
    """
    # id, created_at, updated_at успадковані з міксинів.
    # email, phone_number, role_to_assign успадковані з GroupInvitationBaseSchema.

    group_id: int = Field(description="Ідентифікатор групи, до якої створено запрошення.")
    invitation_code: str = Field(description="Унікальний код запрошення.")
    expires_at: datetime = Field(description="Час закінчення терміну дії запрошення.")
    status: InvitationStatus = Field(description="Поточний статус запрошення.")
    created_by_user_id: Optional[int] = Field(None, description="Ідентифікатор користувача, який створив запрошення.")
    # Можна додати інформацію про користувача, що створив, якщо потрібно:
    # created_by: Optional[UserPublicProfileSchema] = None


class GroupInvitationAcceptSchema(BaseSchema):
    """
    Схема для прийняття запрошення до групи за допомогою коду.
    """
    invitation_code: str = Field(description="Унікальний код запрошення для приєднання до групи.")


if __name__ == "__main__":
    # Демонстраційний блок для схем запрошень до груп.
    logger.info("--- Pydantic Схеми для Запрошень до Груп (GroupInvitation) ---")

    logger.info("\nGroupInvitationBaseSchema (приклад):")
    base_invite_data = {"email": "invitee@example.com", "role_to_assign": GroupRole.MEMBER} # Використовуємо Enum
    base_invite_instance = GroupInvitationBaseSchema(**base_invite_data)
    logger.info(base_invite_instance.model_dump_json(indent=2))
    try:
        GroupInvitationBaseSchema(email="test@test.com", role_to_assign="invalid_role") # Pydantic автоматично валідує Enum
    except Exception as e:
        logger.info(f"Помилка валідації GroupInvitationBaseSchema (очікувано): {e}")

    logger.info("\nGroupInvitationCreateSchema (приклад для створення):")
    create_invite_data = {
        "email": "new_invite@example.com",
        "role_to_assign": GroupRole.ADMIN, # Використовуємо Enum
        "expires_at": datetime.now() + timedelta(days=3)
    }
    create_invite_instance = GroupInvitationCreateSchema(**create_invite_data)
    logger.info(create_invite_instance.model_dump_json(indent=2))

    logger.info("\nGroupInvitationUpdateSchema (приклад для оновлення статусу):")
    update_invite_data = {"status": InvitationStatus.CANCELLED}  # Використовуємо Enum
    update_invite_instance = GroupInvitationUpdateSchema(**update_invite_data)
    logger.info(update_invite_instance.model_dump_json(indent=2))

    logger.info("\nGroupInvitationSchema (приклад відповіді API):")
    invitation_response_data = {
        "id": 1,
        "group_id": 10,
        "email": "invited.user@example.com",
        "invitation_code": "XYZ123ABC",
        "role_to_assign": GroupRole.MEMBER, # Використовуємо Enum
        "expires_at": datetime.now() + timedelta(days=1),
        "status": InvitationStatus.PENDING, # Використовуємо Enum
        "created_by_user_id": 101,
        "created_at": datetime.now() - timedelta(hours=1),
        "updated_at": datetime.now() - timedelta(minutes=30)
    }
    invitation_response_instance = GroupInvitationSchema(**invitation_response_data)
    logger.info(invitation_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nGroupInvitationAcceptSchema (приклад для прийняття запрошення):")
    accept_data = {"invitation_code": "VALIDCODE789"}
    accept_instance = GroupInvitationAcceptSchema(**accept_data)
    logger.info(accept_instance.model_dump_json(indent=2))

    logger.info("\nПримітка: Ці схеми використовуються для валідації та серіалізації даних запрошень до груп.")
    logger.info("TODO: Валідацію 'phone_number'.") # TODO для InvitationStatus видалено
    logger.info(
        "TODO: Розглянути `model_validator` в `GroupInvitationCreateSchema` для перевірки наявності email або phone_number.")

# from pydantic import model_validator # Для Pydantic v2, якщо використовується root_validator
