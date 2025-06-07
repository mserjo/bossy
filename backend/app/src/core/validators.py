# backend/app/src/core/validators.py

"""
This module provides reusable custom validator functions.
These validators can be used directly or integrated into Pydantic models
for data validation across the application.
"""

import re
from typing import Any, Optional, List

from backend.app.src.core.exceptions import ValidationException
from backend.app.src.core.constants import PASSWORD_REGEX, USERNAME_REGEX

# --- String Validators ---

def validate_not_empty(value: Optional[str], field_name: str) -> str:
    """Validates that a string value is not empty or None."""
    if value is None or not value.strip():
        raise ValidationException(f"{field_name} cannot be empty.", errors=[{
            "loc": (field_name,),
            "msg": "Cannot be empty or whitespace.",
            "type": "value_error.empty"
        }])
    return value

def validate_max_length(value: str, max_len: int, field_name: str) -> str:
    """Validates that a string value does not exceed a maximum length."""
    if len(value) > max_len:
        raise ValidationException(
            f"{field_name} exceeds maximum length of {max_len} characters.",
            errors=[{
                "loc": (field_name,),
                "msg": f"Length should not exceed {max_len} characters.",
                "type": "value_error.max_length"
            }]
        )
    return value

def validate_min_length(value: str, min_len: int, field_name: str) -> str:
    """Validates that a string value meets a minimum length."""
    if len(value) < min_len:
        raise ValidationException(
            f"{field_name} is shorter than minimum length of {min_len} characters.",
            errors=[{
                "loc": (field_name,),
                "msg": f"Length should be at least {min_len} characters.",
                "type": "value_error.min_length"
            }]
        )
    return value

def validate_allowed_characters(value: str, pattern: str, field_name: str, error_message: Optional[str] = None) -> str:
    """Validates that a string contains only characters allowed by a regex pattern."""
    if not re.fullmatch(pattern, value):
        default_msg = f"{field_name} contains invalid characters. Pattern: {pattern}"
        raise ValidationException(
            error_message or default_msg,
            errors=[{
                "loc": (field_name,),
                "msg": error_message or f"String does not match pattern: {pattern}",
                "type": "value_error.pattern_mismatch"
            }]
        )
    return value

# --- Specific Format Validators ---

def validate_username_format(username: str) -> str:
    """Validates the format of a username using USERNAME_REGEX from constants."""
    try:
        return validate_allowed_characters(
            username, USERNAME_REGEX, "username",
            error_message="Username must be 3-20 characters long and can only contain alphanumeric characters, underscores, and hyphens."
        )
    except ValidationException as e:
        # Augment the error details from ValidationException if needed, or just re-raise
        if e.errors and isinstance(e.errors, list) and e.errors[0]:
             e.errors[0]["type"] = "value_error.username_format"
        raise

def validate_password_strength(password: str) -> str:
    """Validates the strength of a password using PASSWORD_REGEX from constants."""
    try:
        return validate_allowed_characters(
            password, PASSWORD_REGEX, "password",
            error_message=(
                "Password must be 8-128 characters long and include at least one uppercase letter, "
                "one lowercase letter, one digit, and one special character (@$!%*?&_)."
            )
        )
    except ValidationException as e:
        if e.errors and isinstance(e.errors, list) and e.errors[0]:
             e.errors[0]["type"] = "value_error.password_strength"
        raise

def validate_phone_number(phone_number: str, default_region: Optional[str] = None) -> str:
    """
    Validates a phone number. This is a placeholder for a more robust validation.
    Consider using a library like 'phonenumbers' for comprehensive validation.
    Example: `pip install phonenumbers`
    """
    # Basic regex: allows for optional +, digits, spaces, hyphens, parentheses.
    # This is NOT comprehensive and should be replaced with a proper library for production.
    basic_phone_regex = r"^\+?[\d\s\-\(\)]+$"
    if not re.fullmatch(basic_phone_regex, phone_number) or len(phone_number) < 7:
        raise ValidationException(
            "Invalid phone number format.",
            errors=[{
                "loc": ("phone_number",),
                "msg": "Please enter a valid phone number.",
                "type": "value_error.phone_number_format"
            }]
        )
    # try:
    #     import phonenumbers
    #     parsed_number = phonenumbers.parse(phone_number, region=default_region)
    #     if not phonenumbers.is_valid_number(parsed_number):
    #         raise ValidationException("Invalid phone number.")
    #     return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
    # except ImportError:
    #     # Log that phonenumbers library is not installed and using basic validation
    #     pass # Falls back to basic regex check above if library not installed
    # except phonenumbers.phonenumberutil.NumberParseException as e:
    #     raise ValidationException(f"Invalid phone number: {e}")

    return phone_number # Return the original or formatted number

# --- Numeric Validators ---

def validate_positive_number(value: Any, field_name: str) -> Any:
    """Validates that a value is a positive number (int or float)."""
    if not isinstance(value, (int, float)) or value <= 0:
        raise ValidationException(
            f"{field_name} must be a positive number.",
            errors=[{
                "loc": (field_name,),
                "msg": "Must be a positive number.",
                "type": "value_error.positive_number"
            }]
        )
    return value

def validate_number_range(value: Any, min_val: Optional[Any] = None, max_val: Optional[Any] = None, field_name: str = "Number") -> Any:
    """Validates that a number is within a specified range (inclusive)."""
    if not isinstance(value, (int, float)):
        raise ValidationException(
            f"{field_name} must be a number.",
            errors=[{
                "loc": (field_name,),
                "msg": "Must be a valid number.",
                "type": "type_error.number"
            }]
        )
    if min_val is not None and value < min_val:
        raise ValidationException(
            f"{field_name} must be at least {min_val}.",
            errors=[{
                "loc": (field_name,),
                "msg": f"Must be {min_val} or greater.",
                "type": "value_error.number.min_value"
            }]
        )
    if max_val is not None and value > max_val:
        raise ValidationException(
            f"{field_name} must be no more than {max_val}.",
            errors=[{
                "loc": (field_name,),
                "msg": f"Must be {max_val} or less.",
                "type": "value_error.number.max_value"
            }]
        )
    return value

# --- List/Collection Validators ---

def validate_list_not_empty(value: Optional[List[Any]], field_name: str) -> List[Any]:
    """Validates that a list is not empty or None."""
    if value is None or len(value) == 0:
        raise ValidationException(
            f"{field_name} list cannot be empty.",
            errors=[{
                "loc": (field_name,),
                "msg": "List cannot be empty.",
                "type": "value_error.list.empty"
            }]
        )
    return value

# --- Pydantic Field Validators (Examples of how to use these in Pydantic models) ---
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
    print("--- Core Validators Demonstration ---")

    def test_validator(func, value, *args):
        field = args[-1] if args else "value"
        try:
            result = func(value, *args)
            print(f"SUCCESS: {func.__name__}('{value}') -> '{result}' for field '{field}'")
        except ValidationException as e:
            print(f"FAIL: {func.__name__}('{value}') for field '{field}': {e.message} (Details: {e.errors})")
        except Exception as e:
            print(f"UNEXPECTED FAIL: {func.__name__}('{value}') for field '{field}': {e}")

    # String validators
    test_validator(validate_not_empty, "Hello", "name")
    test_validator(validate_not_empty, "  ", "name")
    test_validator(validate_not_empty, None, "name")
    test_validator(validate_max_length, "abc", 5, "code")
    test_validator(validate_max_length, "abcdef", 5, "code")
    test_validator(validate_min_length, "abcde", 5, "token")
    test_validator(validate_min_length, "abc", 5, "token")

    # Specific format validators
    test_validator(validate_username_format, "test_user1")
    test_validator(validate_username_format, "tu") # Too short
    test_validator(validate_username_format, "test user") # Space
    test_validator(validate_username_format, "testuser!") # Invalid char

    test_validator(validate_password_strength, "ValidP@ss1")
    test_validator(validate_password_strength, "weak")
    test_validator(validate_password_strength, "NoSpecial1")
    test_validator(validate_password_strength, "nouppercase1@")

    test_validator(validate_phone_number, "+1234567890")
    test_validator(validate_phone_number, "(123) 456-7890")
    test_validator(validate_phone_number, "123") # Too short / invalid

    # Numeric validators
    test_validator(validate_positive_number, 10, "age")
    test_validator(validate_positive_number, 0, "count")
    test_validator(validate_positive_number, -5, "score")
    test_validator(validate_positive_number, "abc", "quantity")

    test_validator(validate_number_range, 5, 1, 10, "rating")
    test_validator(validate_number_range, 0, 1, 10, "rating")
    test_validator(validate_number_range, 11, 1, 10, "rating")
    test_validator(validate_number_range, 5, None, 10, "rating")
    test_validator(validate_number_range, 5, 1, None, "rating")

    # List validators
    test_validator(validate_list_not_empty, [1, 2], "items")
    test_validator(validate_list_not_empty, [], "items")
    test_validator(validate_list_not_empty, None, "items")

    print("\nNote: For Pydantic models, these validators are typically used with `pydantic.validator`.")
