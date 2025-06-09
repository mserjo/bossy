# backend/app/src/core/validators.py

"""
Цей модуль надає багаторазові власні функції-валідатори.
Ці валідатори можна використовувати безпосередньо або інтегрувати в моделі Pydantic
для перевірки даних у всій програмі.
"""

import re
from typing import Any, Optional, List

from backend.app.src.core.exceptions import ValidationException
from backend.app.src.core.constants import PASSWORD_REGEX, USERNAME_REGEX

# --- Валідатори рядків ---

def validate_not_empty(value: Optional[str], field_name: str) -> str:
    """Перевіряє, що рядкове значення не є порожнім або None."""
    if value is None or not value.strip():
        raise ValidationException(f"{field_name} не може бути порожнім.", errors=[{
            "loc": (field_name,),
            "msg": "Не може бути порожнім або містити лише пробіли.",
            "type": "value_error.empty"
        }])
    return value

def validate_max_length(value: str, max_len: int, field_name: str) -> str:
    """Перевіряє, що довжина рядкового значення не перевищує максимальну."""
    if len(value) > max_len:
        raise ValidationException(
            f"{field_name} перевищує максимальну довжину {max_len} символів.",
            errors=[{
                "loc": (field_name,),
                "msg": f"Довжина не повинна перевищувати {max_len} символів.",
                "type": "value_error.max_length"
            }]
        )
    return value

def validate_min_length(value: str, min_len: int, field_name: str) -> str:
    """Перевіряє, що рядкове значення відповідає мінімальній довжині."""
    if len(value) < min_len:
        raise ValidationException(
            f"{field_name} коротший за мінімальну довжину {min_len} символів.",
            errors=[{
                "loc": (field_name,),
                "msg": f"Довжина повинна бути щонайменше {min_len} символів.",
                "type": "value_error.min_length"
            }]
        )
    return value

def validate_allowed_characters(value: str, pattern: str, field_name: str, error_message: Optional[str] = None) -> str:
    """Перевіряє, що рядок містить лише символи, дозволені регулярним виразом."""
    if not re.fullmatch(pattern, value):
        default_msg = f"{field_name} містить недійсні символи. Шаблон: {pattern}"
        raise ValidationException(
            error_message or default_msg,
            errors=[{
                "loc": (field_name,),
                "msg": error_message or f"Рядок не відповідає шаблону: {pattern}",
                "type": "value_error.pattern_mismatch"
            }]
        )
    return value

# --- Валідатори специфічних форматів ---

def validate_username_format(username: str) -> str:
    """Перевіряє формат імені користувача за допомогою USERNAME_REGEX з констант."""
    try:
        return validate_allowed_characters(
            username, USERNAME_REGEX, "username",
            error_message="Ім'я користувача повинно містити 3-20 символів і може містити лише буквено-цифрові символи, підкреслення та дефіси."
        )
    except ValidationException as e:
        # Доповнити деталі помилки з ValidationException, якщо потрібно, або просто повторно викликати
        if e.errors and isinstance(e.errors, list) and e.errors[0]:
             e.errors[0]["type"] = "value_error.username_format"
        raise

def validate_password_strength(password: str) -> str:
    """Перевіряє надійність пароля за допомогою PASSWORD_REGEX з констант."""
    try:
        return validate_allowed_characters(
            password, PASSWORD_REGEX, "password",
            error_message=(
                "Пароль повинен містити 8-128 символів і включати принаймні одну велику літеру, "
                "одну маленьку літеру, одну цифру та один спеціальний символ (@$!%*?&_)."
            )
        )
    except ValidationException as e:
        if e.errors and isinstance(e.errors, list) and e.errors[0]:
             e.errors[0]["type"] = "value_error.password_strength"
        raise

def validate_phone_number(phone_number: str, default_region: Optional[str] = None) -> str:
    """
    Перевіряє номер телефону. Це заповнювач для більш надійної валідації.
    Розгляньте можливість використання бібліотеки, такої як 'phonenumbers', для комплексної валідації.
    Приклад: `pip install phonenumbers`
    """
    # Базовий regex: дозволяє необов'язковий +, цифри, пробіли, дефіси, дужки.
    # Це НЕ є вичерпним і повинно бути замінено належною бібліотекою для продакшену.
    basic_phone_regex = r"^\+?[\d\s\-\(\)]+$"
    if not re.fullmatch(basic_phone_regex, phone_number) or len(phone_number) < 7:
        raise ValidationException(
            "Недійсний формат номера телефону.",
            errors=[{
                "loc": ("phone_number",),
                "msg": "Будь ласка, введіть дійсний номер телефону.",
                "type": "value_error.phone_number_format"
            }]
        )
    # try:
    #     import phonenumbers
    #     parsed_number = phonenumbers.parse(phone_number, region=default_region)
    #     if not phonenumbers.is_valid_number(parsed_number):
    #         raise ValidationException("Недійсний номер телефону.")
    #     return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
    # except ImportError:
    #     # Залогувати, що бібліотека phonenumbers не встановлена, і використовується базова валідація
    #     pass # Повертається до базової перевірки regex вище, якщо бібліотека не встановлена
    # except phonenumbers.phonenumberutil.NumberParseException as e:
    #     raise ValidationException(f"Недійсний номер телефону: {e}")

    return phone_number # Повернути оригінальний або відформатований номер

# --- Числові валідатори ---

def validate_positive_number(value: Any, field_name: str) -> Any:
    """Перевіряє, що значення є додатним числом (int або float)."""
    if not isinstance(value, (int, float)) or value <= 0:
        raise ValidationException(
            f"{field_name} має бути додатним числом.",
            errors=[{
                "loc": (field_name,),
                "msg": "Має бути додатним числом.",
                "type": "value_error.positive_number"
            }]
        )
    return value

def validate_number_range(value: Any, min_val: Optional[Any] = None, max_val: Optional[Any] = None, field_name: str = "Число") -> Any:
    """Перевіряє, що число знаходиться у вказаному діапазоні (включно)."""
    if not isinstance(value, (int, float)):
        raise ValidationException(
            f"{field_name} має бути числом.",
            errors=[{
                "loc": (field_name,),
                "msg": "Має бути дійсним числом.",
                "type": "type_error.number"
            }]
        )
    if min_val is not None and value < min_val:
        raise ValidationException(
            f"{field_name} має бути щонайменше {min_val}.",
            errors=[{
                "loc": (field_name,),
                "msg": f"Має бути {min_val} або більше.",
                "type": "value_error.number.min_value"
            }]
        )
    if max_val is not None and value > max_val:
        raise ValidationException(
            f"{field_name} має бути не більше ніж {max_val}.",
            errors=[{
                "loc": (field_name,),
                "msg": f"Має бути {max_val} або менше.",
                "type": "value_error.number.max_value"
            }]
        )
    return value

# --- Валідатори списків/колекцій ---

def validate_list_not_empty(value: Optional[List[Any]], field_name: str) -> List[Any]:
    """Перевіряє, що список не є порожнім або None."""
    if value is None or len(value) == 0:
        raise ValidationException(
            f"Список {field_name} не може бути порожнім.",
            errors=[{
                "loc": (field_name,),
                "msg": "Список не може бути порожнім.",
                "type": "value_error.list.empty"
            }]
        )
    return value

# --- Валідатори полів Pydantic (приклади використання в моделях Pydantic) ---
# from pydantic import validator
# class MyModel(BaseModel):
#     name: str
#     age: int
#     username: str
#     password: str
#     phone: Optional[str]
#
#     _validate_name_not_empty = validator("name", allow_reuse=True)(lambda v: validate_not_empty(v, "name"))
#     _validate_name_max_length = validator("name", allow_reuse=True)(lambda v: validate_max_length(v, 50, "name"))
#     _validate_age_positive = validator("age", allow_reuse=True)(lambda v: validate_positive_number(v, "age"))
#     _validate_username = validator("username", allow_reuse=True)(validate_username_format)
#     _validate_password = validator("password", allow_reuse=True)(validate_password_strength)
#     _validate_phone = validator("phone", allow_reuse=True)(lambda v: validate_phone_number(v) if v else v)

if __name__ == "__main__":
    print("--- Демонстрація основних валідаторів ---")

    def test_validator(func, value, *args):
        field = args[-1] if args else "value"
        try:
            result = func(value, *args)
            print(f"УСПІХ: {func.__name__}('{value}') -> '{result}' для поля '{field}'")
        except ValidationException as e:
            print(f"ПОМИЛКА: {func.__name__}('{value}') для поля '{field}': {e.message} (Деталі: {e.errors})")
        except Exception as e:
            print(f"НЕОЧІКУВАНА ПОМИЛКА: {func.__name__}('{value}') для поля '{field}': {e}")

    # Валідатори рядків
    test_validator(validate_not_empty, "Привіт", "name")
    test_validator(validate_not_empty, "  ", "name")
    test_validator(validate_not_empty, None, "name")
    test_validator(validate_max_length, "abc", 5, "code")
    test_validator(validate_max_length, "abcdef", 5, "code")
    test_validator(validate_min_length, "abcde", 5, "token")
    test_validator(validate_min_length, "abc", 5, "token")

    # Валідатори специфічних форматів
    test_validator(validate_username_format, "test_user1")
    test_validator(validate_username_format, "tu") # Занадто короткий
    test_validator(validate_username_format, "test user") # Пробіл
    test_validator(validate_username_format, "testuser!") # Недійсний символ

    test_validator(validate_password_strength, "ValidP@ss1")
    test_validator(validate_password_strength, "weak")
    test_validator(validate_password_strength, "NoSpecial1")
    test_validator(validate_password_strength, "nouppercase1@")

    test_validator(validate_phone_number, "+1234567890")
    test_validator(validate_phone_number, "(123) 456-7890")
    test_validator(validate_phone_number, "123") # Занадто короткий / недійсний

    # Числові валідатори
    test_validator(validate_positive_number, 10, "age")
    test_validator(validate_positive_number, 0, "count")
    test_validator(validate_positive_number, -5, "score")
    test_validator(validate_positive_number, "abc", "quantity")

    test_validator(validate_number_range, 5, 1, 10, "rating")
    test_validator(validate_number_range, 0, 1, 10, "rating")
    test_validator(validate_number_range, 11, 1, 10, "rating")
    test_validator(validate_number_range, 5, None, 10, "rating")
    test_validator(validate_number_range, 5, 1, None, "rating")

    # Валідатори списків
    test_validator(validate_list_not_empty, [1, 2], "items")
    test_validator(validate_list_not_empty, [], "items")
    test_validator(validate_list_not_empty, None, "items")

    print("\nПримітка: Для моделей Pydantic ці валідатори зазвичай використовуються з `pydantic.validator`.")
