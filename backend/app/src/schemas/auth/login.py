# backend/app/src/schemas/auth/login.py
# -*- coding: utf-8 -*-
"""
Pydantic схеми для процесів, пов'язаних з логіном та відновленням паролю.

Цей модуль визначає схеми для:
- `LoginRequest`: Запит на вхід до системи (автентифікація).
- `PasswordResetRequestSchema`: Запит на скидання паролю (зазвичай через email).
- `PasswordResetConfirmSchema`: Підтвердження скидання паролю з новим паролем та токеном.
"""

from pydantic import BaseModel, Field, EmailStr
from backend.app.src.core.i18n import _

# Абсолютний імпорт базової схеми
from backend.app.src.schemas.base import BaseSchema
from backend.app.src.config.logging import get_logger 
logger = get_logger(__name__)

# Імпорт констант для валідації, якщо потрібно (наприклад, PASSWORD_REGEX)
# from backend.app.src.core.constants import PASSWORD_REGEX

class LoginRequestSchema(BaseSchema): # Перейменовано з LoginRequest
    """
    Схема запиту для входу користувача в систему.
    Очікує email (як ім'я користувача) та пароль.
    """
    # Замість username: str, використовуємо email: EmailStr для логіну,
    # оскільки модель User використовує email як унікальний ідентифікатор для входу.
    # Якщо логін за нікнеймом також підтримується, можна додати поле username: str
    # або зробити це поле Union[EmailStr, str].
    username: EmailStr = Field(description=_("schemas.auth.login.username_description"), examples=["user@example.com"])
    password: str = Field(description=_("schemas.auth.login.password_description"))
    # model_config успадковується з BaseSchema


class PasswordResetRequestSchema(BaseSchema):
    """
    Схема запиту для ініціації процедури скидання пароля.
    Очікує email адресу користувача, для якого потрібно скинути пароль.
    """
    email: EmailStr = Field(description=_("schemas.auth.password_reset_request.email_description"))


class PasswordResetConfirmSchema(BaseSchema):
    """
    Схема для підтвердження скидання пароля.
    Очікує токен скидання (отриманий користувачем, наприклад, по email) та новий пароль.
    """
    token: str = Field(description=_("schemas.auth.password_reset_confirm.token_description"))
    # TODO: Додати валідацію надійного пароля за допомогою constr(pattern=PASSWORD_REGEX),
    #       коли PASSWORD_REGEX буде доступний з констант.
    new_password: str = Field(
        ...,
        min_length=8,
        description=_("schemas.auth.password_reset_confirm.new_password_description")
    )


if __name__ == "__main__":
    logger.info(_("schemas.auth.login.log_demo_header"))

    logger.info(_("schemas.auth.login.log_login_request_example"))
    login_data = {"username": "testlogin@example.com", "password": "securepassword123"}
    login_instance = LoginRequestSchema(**login_data)
    logger.info(login_instance.model_dump_json(indent=2))
    try:
        LoginRequestSchema(username="not-an-email", password="pw")
    except Exception as e:
        logger.info(_("schemas.auth.login.log_login_request_validation_error", error=str(e)))

    logger.info(_("schemas.auth.login.log_password_reset_request_example"))
    password_reset_request_data = {"email": "forgotpassword@example.com"}
    password_reset_request_instance = PasswordResetRequestSchema(**password_reset_request_data)
    logger.info(password_reset_request_instance.model_dump_json(indent=2))

    logger.info(_("schemas.auth.login.log_password_reset_confirm_example"))
    password_reset_confirm_data = {
        "token": "valid_reset_token_string_12345",
        "new_password": "NewStrongPassword123!"
    }
    password_reset_confirm_instance = PasswordResetConfirmSchema(**password_reset_confirm_data)
    logger.info(password_reset_confirm_instance.model_dump_json(indent=2))
    try:
        PasswordResetConfirmSchema(token="t", new_password="short")
    except Exception as e:
        logger.info(_("schemas.auth.login.log_password_reset_confirm_validation_error", error=str(e)))

    logger.info(_("schemas.auth.login.log_note_usage"))
    logger.info(_("schemas.auth.login.log_todo_password_validation"))
