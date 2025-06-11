# backend/app/src/schemas/auth/login.py
"""
Pydantic схеми для процесів, пов'язаних з логіном та відновленням паролю.

Цей модуль визначає схеми для:
- `LoginRequest`: Запит на вхід до системи (автентифікація).
- `PasswordResetRequestSchema`: Запит на скидання паролю (зазвичай через email).
- `PasswordResetConfirmSchema`: Підтвердження скидання паролю з новим паролем та токеном.
"""

from pydantic import BaseModel, Field, EmailStr

# Абсолютний імпорт базової схеми
from backend.app.src.schemas.base import BaseSchema
from backend.app.src.config.logging import get_logger  # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

# Імпорт констант для валідації, якщо потрібно (наприклад, PASSWORD_REGEX)
# from backend.app.src.core.constants import PASSWORD_REGEX

class LoginRequest(BaseSchema):
    """
    Схема запиту для входу користувача в систему.
    Очікує email (як ім'я користувача) та пароль.
    """
    # Замість username: str, використовуємо email: EmailStr для логіну,
    # оскільки модель User використовує email як унікальний ідентифікатор для входу.
    # Якщо логін за нікнеймом також підтримується, можна додати поле username: str
    # або зробити це поле Union[EmailStr, str].
    username: EmailStr = Field(description="Електронна пошта користувача для входу.", examples=["user@example.com"])
    password: str = Field(description="Пароль користувача.")
    # model_config успадковується з BaseSchema


class PasswordResetRequestSchema(BaseSchema):
    """
    Схема запиту для ініціації процедури скидання пароля.
    Очікує email адресу користувача, для якого потрібно скинути пароль.
    """
    email: EmailStr = Field(description="Електронна пошта користувача, для якого запитується скидання пароля.")


class PasswordResetConfirmSchema(BaseSchema):
    """
    Схема для підтвердження скидання пароля.
    Очікує токен скидання (отриманий користувачем, наприклад, по email) та новий пароль.
    """
    token: str = Field(description="Токен скидання пароля, отриманий користувачем.")
    # TODO: Додати валідацію надійного пароля за допомогою constr(pattern=PASSWORD_REGEX),
    #       коли PASSWORD_REGEX буде доступний з констант.
    new_password: str = Field(
        ...,  # Обов'язкове поле
        min_length=8,  # Мінімальна довжина пароля
        description="Новий пароль користувача (мін. 8 символів, має відповідати політикам надійності)."
    )


if __name__ == "__main__":
    # Демонстраційний блок для схем логіну та відновлення пароля.
    logger.info("--- Pydantic Схеми для Логіну та Відновлення Паролю ---")

    logger.info("\nLoginRequest (приклад):")
    login_data = {"username": "testlogin@example.com", "password": "securepassword123"}
    login_instance = LoginRequest(**login_data)
    logger.info(login_instance.model_dump_json(indent=2))
    try:
        LoginRequest(username="not-an-email", password="pw")
    except Exception as e:
        logger.info(f"Помилка валідації LoginRequest (очікувано): {e}")

    logger.info("\nPasswordResetRequestSchema (приклад):")
    password_reset_request_data = {"email": "forgotpassword@example.com"}
    password_reset_request_instance = PasswordResetRequestSchema(**password_reset_request_data)
    logger.info(password_reset_request_instance.model_dump_json(indent=2))

    logger.info("\nPasswordResetConfirmSchema (приклад):")
    password_reset_confirm_data = {
        "token": "valid_reset_token_string_12345",
        "new_password": "NewStrongPassword123!"
    }
    password_reset_confirm_instance = PasswordResetConfirmSchema(**password_reset_confirm_data)
    logger.info(password_reset_confirm_instance.model_dump_json(indent=2))
    try:
        PasswordResetConfirmSchema(token="t", new_password="short")
    except Exception as e:
        logger.info(f"Помилка валідації PasswordResetConfirmSchema (очікувано): {e}")

    logger.info(
        "\nПримітка: Ці схеми використовуються для обробки запитів, пов'язаних з автентифікацією та відновленням доступу.")
    logger.info("TODO: Для поля 'new_password' в PasswordResetConfirmSchema додати валідацію надійності пароля.")
