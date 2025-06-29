# backend/app/src/schemas/groups/invitation.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `GroupInvitationModel`.
Схеми використовуються для валідації даних при створенні, оновленні
та відображенні запрошень до груп.
"""

from pydantic import Field, EmailStr, field_validator
from typing import Optional, List, ForwardRef
import uuid
from datetime import datetime

from backend.app.src.schemas.base import BaseSchema, AuditDatesSchema # IdentifiedSchema, TimestampedSchema
# Потрібно буде імпортувати схеми для зв'язків:
# from backend.app.src.schemas.groups.group import GroupSimpleSchema
# from backend.app.src.schemas.auth.user import UserPublicSchema
# from backend.app.src.schemas.dictionaries.user_role import UserRoleSchema
# from backend.app.src.schemas.dictionaries.status import StatusSchema

from typing import TYPE_CHECKING # Додано TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.src.schemas.groups.group import GroupSimpleSchema
    from backend.app.src.schemas.auth.user import UserPublicSchema
    from backend.app.src.schemas.dictionaries.user_role import UserRoleSchema
    from backend.app.src.schemas.dictionaries.status import StatusSchema

# GroupSimpleSchema = ForwardRef('backend.app.src.schemas.groups.group.GroupSimpleSchema') # Перенесено
# UserPublicSchema = ForwardRef('backend.app.src.schemas.auth.user.UserPublicSchema') # Перенесено
# UserRoleSchema = ForwardRef('backend.app.src.schemas.dictionaries.user_role.UserRoleSchema') # Перенесено
# StatusSchema = ForwardRef('backend.app.src.schemas.dictionaries.status.StatusSchema') # Перенесено

# --- Схема для відображення інформації про запрошення (для читання) ---
class GroupInvitationSchema(AuditDatesSchema): # Успадковує id, created_at, updated_at
    """
    Схема для представлення запрошення до групи.
    """
    group_id: uuid.UUID = Field(..., description="ID групи, до якої надсилається запрошення")
    invitation_code: str = Field(..., description="Унікальний код запрошення")

    email_invited: Optional[EmailStr] = Field(None, description="Email користувача, якого запрошують (якщо іменне)")
    user_id_invited: Optional[uuid.UUID] = Field(None, description="ID існуючого користувача, якого запрошують")
    user_id_creator: uuid.UUID = Field(..., description="ID користувача (адміна групи), який створив запрошення")
    role_to_assign_id: uuid.UUID = Field(..., description="ID ролі, яка буде призначена користувачеві")

    expires_at: Optional[datetime] = Field(None, description="Дата та час закінчення терміну дії запрошення")
    max_uses: Optional[int] = Field(None, ge=1, description="Максимальна кількість використань (NULL - необмежено)")
    current_uses: int = Field(..., ge=0, description="Поточна кількість використань")
    is_active: bool = Field(..., description="Чи є запрошення активним")
    status_id: Optional[uuid.UUID] = Field(None, description="ID статусу запрошення (надіслано, прийнято, прострочено)")

    # --- Розгорнуті зв'язки (приклад) ---
    group: Optional['GroupSimpleSchema'] = Field(None, description="Інформація про групу, до якої запрошують") # Рядкове посилання
    creator: Optional['UserPublicSchema'] = Field(None, description="Інформація про користувача, який створив запрошення") # Рядкове посилання
    invited_user_info: Optional['UserPublicSchema'] = Field(None, alias="invited_user", description="Інформація про запрошеного користувача (якщо user_id_invited вказано)") # Рядкове посилання
    role_to_assign: Optional['UserRoleSchema'] = Field(None, description="Інформація про роль, яка буде призначена") # Рядкове посилання
    status: Optional['StatusSchema'] = Field(None, description="Інформація про статус запрошення") # Рядкове посилання


# --- Схема для створення нового запрошення до групи ---
class GroupInvitationCreateSchema(BaseSchema):
    """
    Схема для створення нового запрошення до групи.
    """
    # group_id: uuid.UUID # Зазвичай group_id відомий з контексту (ендпоінт /groups/{group_id}/invitations)

    # Або іменне запрошення, або загальне.
    email_invited: Optional[EmailStr] = Field(None, description="Email користувача для іменного запрошення")
    user_id_invited: Optional[uuid.UUID] = Field(None, description="ID існуючого користувача для іменного запрошення")
    # user_id_creator: uuid.UUID # Встановлюється автоматично з поточного користувача (адміна)

    role_to_assign_id: uuid.UUID = Field(..., description="ID ролі, яка буде призначена при прийнятті запрошення")

    expires_at: Optional[datetime] = Field(None, description="Термін дії запрошення (NULL - безстрокове)")
    max_uses: Optional[int] = Field(None, ge=1, description="Максимальна кількість використань (NULL - необмежено)")
    # is_active: bool = Field(default=True) # Зазвичай активне при створенні
    # status_id: Optional[uuid.UUID] # Початковий статус (наприклад, "активне" або "надіслано") - встановлюється сервісом

    # `invitation_code` генерується сервером.
    # `current_uses` починається з 0.

    @field_validator('expires_at')
    @classmethod
    def expires_at_must_be_in_future(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is not None and value <= datetime.utcnow().replace(tzinfo=None): # Порівнюємо naive datetimes або aware
            # Або, якщо value має tz, а utcnow() - ні: value.replace(tzinfo=None) <= datetime.utcnow()
            # Краще, щоб всі дати були aware (з timezone). Pydantic v2 підтримує це краще.
            # Поки що припускаємо, що datetime з моделі/запиту може бути naive.
            # TODO: Узгодити роботу з часовими зонами (всі дати в UTC).
            # Якщо datetime.utcnow() - це UTC, а value - теж, то все ОК.
            # Якщо value приходить без tz, а ми порівнюємо з UTC, це може бути неточно.
            # Поки що проста перевірка.
            raise ValueError("Термін дії запрошення не може бути в минулому.")
        return value

    # @model_validator(mode='before') # Або 'after'
    # def check_invitee_details(cls, data: Any) -> Any:
    #     # Можна додати валідацію, що email_invited та user_id_invited не заповнені одночасно,
    #     # або що хоча б одне з них заповнене, якщо запрошення завжди іменне.
    #     # Але якщо запрошення може бути і загальним (без email/user_id), то ця логіка інша.
    #     # Поки що ТЗ каже "відправити запрошення користувача", що натякає на іменне.
    #     # Але "за посиланням/QR-коду (унікальний в рамках групи)" може бути і загальним.
    #     # Залишаю обидва поля опціональними.
    #     return data

# --- Схема для оновлення існуючого запрошення (наприклад, деактивація) ---
class GroupInvitationUpdateSchema(BaseSchema):
    """
    Схема для оновлення існуючого запрошення до групи.
    Дозволяє, наприклад, деактивувати запрошення або змінити термін дії.
    """
    expires_at: Optional[datetime] = Field(None) # Можна оновити термін дії
    max_uses: Optional[int] = Field(None, ge=1)  # Можна змінити макс. кількість використань
    is_active: Optional[bool] = Field(None)      # Можна активувати/деактивувати
    status_id: Optional[uuid.UUID] = Field(None) # Можна змінити статус (наприклад, "скасовано")

    # Інші поля (role_to_assign_id, email_invited, user_id_invited) зазвичай не змінюються
    # для вже створеного запрошення. Якщо потрібно, це видалення старого і створення нового.

    @field_validator('expires_at')
    @classmethod
    def expires_at_must_be_in_future_optional(cls, value: Optional[datetime]) -> Optional[datetime]:
        # Такий же валідатор, як в CreateSchema, але для опціонального поля
        if value is not None and value <= datetime.utcnow().replace(tzinfo=None):
            raise ValueError("Термін дії запрошення не може бути в минулому.")
        return value

# GroupInvitationSchema.model_rebuild() # Для ForwardRef

# TODO: Переконатися, що схеми відповідають моделі `GroupInvitationModel`.
# `GroupInvitationModel` успадковує від `BaseModel`.
# `GroupInvitationSchema` успадковує від `AuditDatesSchema` і додає всі основні поля запрошення.
# Розгорнуті зв'язки закоментовані, але можуть бути додані.
#
# `GroupInvitationCreateSchema`:
#   - `group_id` та `user_id_creator` очікуються з контексту/сервісу.
#   - `invitation_code` генерується сервісом.
#   - `current_uses` починається з 0.
#   - `is_active` за замовчуванням True.
#   - `status_id` встановлюється сервісом.
#   - Валідатор для `expires_at`.
#
# `GroupInvitationUpdateSchema` дозволяє змінювати `expires_at`, `max_uses`, `is_active`, `status_id`.
#
# Все виглядає узгоджено.
# `EmailStr` для валідації `email_invited`.
# `ge=1` для `max_uses` (якщо встановлено, то хоча б 1).
# `ge=0` для `current_uses`.
# Робота з часовими зонами для `expires_at` потребує уваги (TODO).
# Поки що припускаємо UTC або naive datetime, що узгоджується на рівні системи.
#
# Логіка щодо того, чи є запрошення іменним (`email_invited` або `user_id_invited` заповнені)
# чи загальним (обидва `None`), буде на сервісному рівні.
# Схеми дозволяють обидва варіанти.
# `role_to_assign_id` - важливе поле, що визначає, яку роль отримає користувач.
# `AuditDatesSchema` надає `id, created_at, updated_at`.
# `created_at` - час створення запрошення.
# `updated_at` - при зміні статусу, `is_active` тощо.
# Все виглядає добре.
