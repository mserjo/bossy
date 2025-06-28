# backend/app/src/api/graphql/types/user.py
# -*- coding: utf-8 -*-
"""
GraphQL типи, пов'язані з користувачами.

Цей модуль визначає GraphQL типи для сутності "Користувач",
включаючи об'єктний тип `UserType`, вхідні типи для мутацій
(наприклад, `UserCreateInput`, `UserUpdateInput`), та будь-які
пов'язані Enum типи (наприклад, `UserRoleTypeEnum`).
"""

import strawberry
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
import uuid # Для ID, якщо використовується UUID

# Імпорт базових типів/інтерфейсів
from backend.app.src.api.graphql.types.base import Node, TimestampsInterface

# TODO: Імпортувати схеми Pydantic для легшого визначення полів або як орієнтир.
# from backend.app.src.schemas.auth.user import UserReadSchema
# from backend.app.src.schemas.dictionary.user_role import UserRoleSchema as UserRolePydanticSchema

if TYPE_CHECKING:
    # Уникнення циклічних залежностей для полів, що посилаються на інші GraphQL типи
    # Наприклад, якщо UserType має поле `groups` типу `List[GroupType]`.
    from backend.app.src.api.graphql.types.group import GroupType # Приклад
    from backend.app.src.api.graphql.types.auth import TokenType # Приклад для AuthPayload
    # from backend.app.src.api.graphql.types.gamification import UserLevelType, UserAchievementType # Приклад

# GraphQL Enum для ролей користувача (якщо вони визначені як Enum в системі)
# Або це може бути окремий GraphQL тип UserRoleType, якщо ролі - це довідник з БД.
# Припустимо, що ролі - це довідник, тому створимо UserRoleType.

@strawberry.type
class UserRoleType(Node, TimestampsInterface):
    """
    GraphQL тип для ролі користувача (з довідника).
    """
    id: strawberry.ID # Успадковано від Node
    name: str = strawberry.field(description="Назва ролі (наприклад, 'Адміністратор групи', 'Користувач').")
    code: str = strawberry.field(description="Унікальний код ролі (наприклад, 'group_admin', 'user').")
    description: Optional[str] = strawberry.field(description="Опис ролі.")
    created_at: datetime # Успадковано
    updated_at: datetime # Успадковано
    # TODO: Додати резолвери для полів, якщо вони не співпадають напряму з атрибутами моделі.


@strawberry.type
class UserType(Node, TimestampsInterface):
    """
    GraphQL тип, що представляє користувача системи.
    """
    id: strawberry.ID # Успадковано від Node
    email: strawberry.Email = strawberry.field(description="Електронна пошта користувача (логін).")
    username: Optional[str] = strawberry.field(description="Ім'я користувача (нікнейм).")
    first_name: Optional[str] = strawberry.field(description="Ім'я користувача.")
    last_name: Optional[str] = strawberry.field(description="Прізвище користувача.")
    is_active: bool = strawberry.field(description="Чи активний акаунт користувача.")
    is_superuser: bool = strawberry.field(description="Чи є користувач супер-адміністратором системи.")
    # TODO: Чи потрібне поле is_staff?

    created_at: datetime # Успадковано
    updated_at: datetime # Успадковано

    avatar_url: Optional[str] = strawberry.field(description="URL аватара користувача.")

    # Поле для ролі користувача (якщо роль одна глобальна)
    # role: Optional[UserRoleType] = strawberry.field(description="Роль користувача в системі.")
    # Або, якщо ролі залежать від групи, це поле може бути в GroupMembershipType.

    # Приклад поля, що потребує резолвера (якщо не співпадає з моделлю)
    @strawberry.field
    def full_name(self) -> Optional[str]:
        """Повне ім'я користувача (Ім'я + Прізвище)."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return None

    # TODO: Додати поля для зв'язків, наприклад, групи, в яких користувач є учасником,
    # його завдання, досягнення тощо. Для цього потрібні відповідні типи та резолвери.
    # Наприклад:
    # @strawberry.field
    # async def groups(self, info: strawberry.Info) -> List["GroupType"]:
    #     # `info.context` містить доступ до DataLoader'ів та сесії БД
    #     # return await info.context.dataloaders.groups_by_user_id.load(self.db_id) # db_id - це ID з БД
    #     pass # Заглушка

    # @strawberry.field
    # async def user_levels_in_groups(self, info: strawberry.Info) -> List["UserLevelType"]: # Приклад
    #     pass

    # @strawberry.field
    # async def achievements_in_group(self, info: strawberry.Info, group_id: strawberry.ID) -> List["UserAchievementType"]: # Приклад
    #     pass

    # Допоміжне поле для внутрішнього використання, не для GraphQL схеми, якщо не потрібно
    # db_id: strawberry.Private[int] # ID з бази даних, якщо strawberry.ID - це base64


# --- Вхідні типи (Input Types) для мутацій ---

@strawberry.input
class UserRegisterInput:
    """Вхідні дані для реєстрації нового користувача."""
    email: strawberry.Email
    password: str
    username: Optional[str] = strawberry.UNSET # Використовуємо UNSET для опціональних полів в інпутах
    first_name: Optional[str] = strawberry.UNSET
    last_name: Optional[str] = strawberry.UNSET
    # TODO: Додати інші поля, якщо вони потрібні при реєстрації (наприклад, код запрошення)

@strawberry.input
class UserLoginInput:
    """Вхідні дані для логіну користувача."""
    email: strawberry.Email # Або username
    password: str

@strawberry.input
class UserProfileUpdateInput:
    """Вхідні дані для оновлення профілю користувача."""
    username: Optional[str] = strawberry.UNSET
    first_name: Optional[str] = strawberry.UNSET
    last_name: Optional[str] = strawberry.UNSET
    # email та password зазвичай змінюються через окремі мутації/процеси
    # TODO: Додати поля для налаштувань сповіщень, якщо вони тут керуються

@strawberry.input
class PasswordChangeInput:
    """Вхідні дані для зміни пароля."""
    old_password: str
    new_password: str

@strawberry.input
class PasswordResetRequestInput:
    """Вхідні дані для запиту на скидання пароля."""
    email: strawberry.Email

@strawberry.input
class PasswordResetConfirmInput:
    """Вхідні дані для підтвердження скидання пароля."""
    token: str
    new_password: str

@strawberry.input
class UserAvatarUploadInput:
    """Вхідні дані для завантаження аватара."""
    # Strawberry підтримує Upload скаляр для файлів
    avatar_file: strawberry.scalars.Upload = strawberry.field(description="Файл аватара для завантаження.")


# Тип для відповіді при успішній автентифікації (логін, реєстрація, оновлення токена)
@strawberry.type
class AuthPayload:
    """Відповідь при успішній автентифікації."""
    user: UserType = strawberry.field(description="Інформація про аутентифікованого користувача.")
    token: "TokenType" = strawberry.field(description="JWT токени доступу та оновлення.")
    # Якщо реєстрація вимагає підтвердження, може бути інший Payload
    # message: Optional[str] = strawberry.field(description="Додаткове повідомлення, наприклад, про необхідність підтвердження email.")


# Експорт визначених типів
__all__ = [
    "UserRoleType",
    "UserType",
    "UserRegisterInput",
    "UserLoginInput",
    "UserProfileUpdateInput",
    "PasswordChangeInput",
    "PasswordResetRequestInput",
    "PasswordResetConfirmInput",
    "UserAvatarUploadInput",
    "AuthPayload",
]
