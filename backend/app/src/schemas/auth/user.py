# backend/app/src/schemas/auth/user.py
# -*- coding: utf-8 -*-
"""
Pydantic схеми для сутності "Користувач" (User).

Цей модуль визначає схеми для:
- Базового представлення користувача (`UserBaseSchema`).
- Створення нового користувача (`UserCreateSchema`).
- Оновлення існуючого користувача (`UserUpdateSchema`).
- Представлення користувача у відповідях API (`UserSchema`).
- Представлення публічного профілю користувача (`UserPublicProfileSchema`).
"""
from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field, EmailStr, AnyHttpUrl

# Абсолютний імпорт базових схем та міксинів
from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin, TimestampedSchemaMixin
from backend.app.src.core.dicts import UserState  # Для значення за замовчуванням
# TODO: Імпортувати StatusResponseSchema після його визначення в schemas.dictionaries.statuses
# from backend.app.src.schemas.dictionaries.statuses import StatusResponseSchema
from backend.app.src.schemas.dictionaries.statuses import StatusResponseSchema
from backend.app.src.schemas.dictionaries.user_types import UserTypeResponseSchema # Added import
from backend.app.src.schemas.dictionaries.user_roles import UserRoleResponseSchema # Added import
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Placeholder assignments removed


class UserBaseSchema(BaseSchema):
    """
    Базова схема для полів користувача, що використовуються як для створення, так і для читання.
    """
    username: str = Field(..., max_length=100, description="Унікальне ім'я користувача (логін).", examples=["john_doe"])
    email: EmailStr = Field(description="Електронна пошта користувача (унікальна).")
    first_name: Optional[str] = Field(None, max_length=100, description="Ім'я користувача.", examples=["Іван"])
    last_name: Optional[str] = Field(None, max_length=100, description="Прізвище користувача.", examples=["Франко"])
    middle_name: Optional[str] = Field(None, max_length=100, description="По батькові користувача (необов'язково).",
                                       examples=["Якович"])
    # TODO: Додати валідацію номера телефону, коли відповідний валідатор буде доступний
    #       і бібліотека phonenumbers буде інтегрована. Наприклад, з використанням Annotated.
    phone_number: Optional[str] = Field(None, max_length=30,
                                        description="Номер телефону користувача (необов'язково, унікальний, якщо вказано).",
                                        examples=["+380501234567"])

    name: str = Field(max_length=255,
                                description="Відображуване ім'я користувача (може бути ПІБ або нікнейм).",
                                examples=["Іван Франко"])
    description: Optional[str] = Field(None, description="Додатковий опис або біографія користувача.")
    notes: Optional[str] = Field(None, description="Приватні нотатки про користувача.")


# UserCreateSchema, UserUpdateSchema, UserResponseSchema, UserPublicProfileSchema
# Схеми для створення, оновлення, відповіді API та публічного профілю користувача.

class UserCreateSchema(UserBaseSchema):
    """
    Схема для створення нового користувача.
    Успадковує базові поля та додає пароль та інші поля, необхідні при реєстрації.
    """
    password: str = Field(..., min_length=8, description="Пароль користувача (мін. 8 символів).")
    # Коди для зв'язку з довідниками. Сервіс має перевіряти їх існування.
    user_type_code: Optional[str] = Field(None, description="Код типу користувача з довідника (напр., 'REGULAR_USER').")
    system_role_code: Optional[str] = Field(None,
                                            description="Код системної ролі користувача з довідника (напр., 'USER').")
    state_code: Optional[str] = Field(None, description="Код стану користувача з довідника dict_statuses.")


class UserUpdateSchema(UserBaseSchema):
    """
    Схема для оновлення даних існуючого користувача.
    Всі поля є опціональними.
    """
    username: Optional[str] = Field(None, max_length=100, description="Нове унікальне ім'я користувача (логін).")
    email: Optional[EmailStr] = Field(None, description="Нова електронна пошта користувача.")
    # first_name, last_name, etc. успадковані та вже Optional[str] = None
    password: Optional[str] = Field(None, min_length=8,
                                    description="Новий пароль користувача (якщо змінюється, мін. 8 символів).")

    is_active: Optional[bool] = Field(None, description="Статус активності облікового запису.")
    is_superuser: Optional[bool] = Field(None, description="Статус суперкористувача.")

    user_type_code: Optional[str] = Field(None, description="Новий код типу користувача з довідника.")
    system_role_code: Optional[str] = Field(None, description="Новий код системної ролі користувача з довідника.")
    state_code: Optional[str] = Field(None, description="Новий код стану користувача з довідника dict_statuses.")

    # Перевизначення успадкованих полів, щоб зробити їх Optional[str] = None, якщо вони були обов'язковими в UserBaseSchema
    # Однак, у UserBaseSchema вони вже Optional, тому це не строго необхідно, але для ясності:
    first_name: Optional[str] = Field(None, max_length=100, description="Нове ім'я користувача.")
    last_name: Optional[str] = Field(None, max_length=100, description="Нове прізвище користувача.")
    middle_name: Optional[str] = Field(None, max_length=100, description="Нове по батькові користувача.")
    phone_number: Optional[str] = Field(None, max_length=30, description="Новий номер телефону користувача.")
    name: Optional[str] = Field(None, max_length=255, description="Нове відображуване ім'я користувача.")
    description: Optional[str] = Field(None, description="Новий опис або біографія користувача.")
    notes: Optional[str] = Field(None, description="Нові приватні нотатки про користувача.")


class UserResponseSchema(UserBaseSchema, IDSchemaMixin, TimestampedSchemaMixin):
    """
    Схема для представлення даних користувача у відповідях API.
    Включає `id`, часові мітки та інші поля, безпечні для відображення.
    """
    # id, created_at, updated_at успадковані з міксинів
    username: str = Field(description="Унікальне ім'я користувача (логін).") # Added username
    is_active: bool = Field(description="Чи активний обліковий запис користувача.")
    is_superuser: bool = Field(description="Чи має користувач права суперкористувача.")
    last_login_at: Optional[datetime] = Field(None, description="Час останнього входу користувача в систему.")
    state: Optional[StatusResponseSchema] = Field(None, description="Об'єкт стану користувача.")

    # Ці поля будуть заповнюватися на основі user_type_id та system_role_id з моделі User.
    user_type: Optional[UserTypeResponseSchema] = Field(None, description="Об'єкт типу користувача.")
    system_role: Optional[UserRoleResponseSchema] = Field(None, description="Об'єкт системної ролі користувача.")

    # TODO: Визначити, як отримувати URL аватара. Це може бути окреме поле в моделі User,
    #       або властивість, що генерується на основі зв'язку з UserAvatar та FileRecord.
    avatar_url: Optional[AnyHttpUrl] = Field(None, description="URL аватара користувача.",
                                             examples=["https://example.com/avatars/user1.jpg"])
    # model_config успадковується з UserBaseSchema -> BaseSchema (from_attributes=True)


# UserPublicProfileSchema вже визначено нижче, тому цей коментар не потрібен.
# class UserPublicProfileSchema(BaseSchema, IDSchemaMixin):

class UserPublicProfileSchema(BaseSchema, IDSchemaMixin):
    """
    Схема для представлення публічного профілю користувача.
    Містить лише обмежений набір полів, безпечних для публічного показу.
    """
    # id успадковано
    username: Optional[str] = Field(None, description="Унікальне ім'я користувача.") # Added username
    name: Optional[str] = Field(None, description="Відображуване ім'я користувача.", examples=["Іван Ф."])
    # TODO: Визначити, як отримувати URL аватара (аналогічно до UserSchema).
    avatar_url: Optional[AnyHttpUrl] = Field(None, description="URL аватара користувача.")
    # last_login_at: Optional[datetime] = None # Розглянути, чи є ця інформація публічною. Зазвичай ні.
    # Можна додати інші публічні поля, наприклад, 'bio' або 'user_level', якщо є.


if __name__ == "__main__":
    from datetime import timedelta
    # Демонстраційний блок для схем користувача.
    logger.info("--- Pydantic Схеми для Користувача (User) ---")

    logger.info("\nUserBaseSchema (приклад):")
    base_data = {"username": "baseuser", "email": "base@example.com", "name": "Базовий Користувач", "first_name": "Базовий", "last_name": "Користувач"}
    base_instance = UserBaseSchema(**base_data)
    logger.info(base_instance.model_dump_json(indent=2))

    logger.info("\nUserCreateSchema (приклад):")
    create_data = {
        "username": "newbie",
        "email": "newuser@example.com",
        "password": "HardPassword123!",
        "name": "Новий Користувач",
        "first_name": "Новий",
        "last_name": "Користувач",
        "user_type_code": "REGULAR_USER",
        "system_role_code": "USER",
        "state_code": "ACTIVE" # Changed from state: UserState.ACTIVE.value
    }
    create_instance = UserCreateSchema(**create_data)
    logger.info(create_instance.model_dump_json(indent=2))

    # Приклад з помилкою (наприклад, відсутній username, якщо він обов'язковий в UserBaseSchema)
    # try:
    #     UserCreateSchema(email="test@test.com", password="password123", name="Test Name")
    # except Exception as e:
    #     logger.info(f"Помилка валідації UserCreateSchema (очікувано, якщо username обов'язковий): {e}")


    logger.info("\nUserUpdateSchema (приклад):")
    update_data = {"username": "updated_user", "first_name": "Оновлене Ім'я", "phone_number": "+380509876543"}
    update_instance = UserUpdateSchema(**update_data)
    logger.info(update_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nUserSchema (приклад відповіді API):")
    user_response_data = {
        "id": 1,
        "username": "apiuser",
        "email": "api.user@example.com",
        "name": "API Користувач",
        "first_name": "API", "last_name": "Користувач",
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "last_login_at": datetime.now() - timedelta(hours=1),
        "state": {"id": 1, "name": "Активний", "code": "ACTIVE", "description": "Стан активного користувача"},
        "user_type": {"id": 1, "name": "Звичайний", "code": "REGULAR_USER", "description": "Стандартний тип користувача"},
        "system_role": {"id": 1, "name": "Користувач", "code": "USER", "description": "Базова системна роль"},
        "avatar_url": "https://example.com/path/to/avatar.png"
    }
    user_response_instance = UserResponseSchema(**user_response_data)
    logger.info(user_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nUserPublicProfileSchema (приклад публічного профілю):")
    public_profile_data = {
        "id": 2,
        "username": "public_user_name",
        "name": "Публічний Юзер",
        "avatar_url": "https://example.com/path/to/public_avatar.png"
    }
    public_profile_instance = UserPublicProfileSchema(**public_profile_data)
    logger.info(public_profile_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Схеми `UserTypeResponseSchema` та `UserRoleResponseSchema` тепер імпортовані.")
    logger.info("Поле `state` тепер використовує `StatusResponseSchema`.")
    logger.info("Також, поле `avatar_url` потребує визначення логіки його заповнення.")
    logger.info("Валідація номера телефону (`phone_number`) потребує інтеграції з `phonenumbers`.")
