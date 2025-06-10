# backend/app/src/utils/validators.py

"""
Custom data validation functions.
These can be used in Pydantic models, service layers, or other parts of the application
for validating specific data formats or rules.
"""

import logging
import re
from typing import Optional # Added Optional for region type hint

# Configure logger for this module
logger = logging.getLogger(__name__)

def is_strong_password(password: str, min_length: int = 8) -> bool:
    """
    Checks if a password meets common strength criteria.
    Criteria:
        - Minimum length (default 8 characters).
        - Contains at least one uppercase letter.
        - Contains at least one lowercase letter.
        - Contains at least one digit.
        - Contains at least one special character (from a predefined set).

    Args:
        password: The password string to validate.
        min_length: The minimum required length for the password.

    Returns:
        True if the password meets all criteria, False otherwise.
    """
    if not password:
        return False
    if len(password) < min_length:
        logger.debug(f"Password validation failed: Too short (length {len(password)}, required {min_length}).")
        return False
    if not re.search(r"[A-Z]", password):
        logger.debug("Password validation failed: No uppercase letter.")
        return False
    if not re.search(r"[a-z]", password):
        logger.debug("Password validation failed: No lowercase letter.")
        return False
    if not re.search(r"[0-9]", password):
        logger.debug("Password validation failed: No digit.")
        return False
    if not re.search(r"[!@#$%^&*()_+=\-\[\]{};':"\|,.<>\/?~`]", password):
        logger.debug("Password validation failed: No special character.")
        return False

    logger.debug("Password validation successful: Meets all criteria.")
    return True

def is_valid_phone_number(phone_number: str, region: Optional[str] = None) -> bool:
    """
    Validates a phone number.
    This is a basic placeholder implementation.
    For robust validation, consider using a dedicated library like 'phonenumbers'.

    Args:
        phone_number: The phone number string to validate.
        region: Optional. A region code (e.g., "US", "GB") for more specific validation if using a library.
                Not used in this basic version.

    Returns:
        True if the phone number format seems valid, False otherwise.
    """
    if not phone_number:
        return False

    num_digits = sum(c.isdigit() for c in phone_number)
    if not (7 <= num_digits <= 15):
        logger.debug(f"Phone number validation failed: Contains {num_digits} digits, expected 7-15.")
        return False

    allowed_chars_pattern = re.compile(r"^[0-9\s\-\(\)\+]*$")
    if not allowed_chars_pattern.match(phone_number):
        logger.debug(f"Phone number validation failed: Contains invalid characters.")
        return False

    if not (phone_number.startswith('+') or phone_number[0].isdigit()):
         logger.debug(f"Phone number validation failed: Does not start with '+' or digit.")
         return False
    if not phone_number[-1].isdigit():
         logger.debug(f"Phone number validation failed: Does not end with a digit.")
         return False

    logger.debug(f"Phone number '{phone_number}' passed basic format validation.")
    return True

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Validation Utilities --- Demonstration")

    logger.info("\n--- Password Strength Tests ---")
    passwords_to_test = {
        "Short1!": False,
        "nouppercase1!": False,
        "NOLOWERCASE1!": False,
        "NoDigit!Aa": False,
        "NoSpecialChar1Aa": False,
        "ValidPass123!": True,
        "Another_Good-One_123": True,
        "Weak": False
    }
    for pw, expected in passwords_to_test.items():
        is_valid = is_strong_password(pw)
        logger.info(f"Password '{pw}': Strong? {is_valid} (Expected: {expected})")
        assert is_valid == expected

    logger.info("\n--- Phone Number Basic Validation Tests ---")
    phones_to_test = {
        "+15551234567": True,
        "555-123-4567": True,
        "(555) 123 4567": True,
        "1234567": True,
        "12345": False,
        "1234567890123456": False,
        "123456789012345": True,
        "555-123-ABCD": False,
        "+1-555-123-4567 ext 9": False,
        "invalid phone": False,
        "": False,
        "+": False,
        "123-": False
    }
    for phone, expected in phones_to_test.items():
        is_valid = is_valid_phone_number(phone)
        logger.info(f"Phone '{phone}': Valid? {is_valid} (Expected: {expected})")
        assert is_valid == expected

    logger.info("Note: Phone number validation is very basic. Use a dedicated library for production.")
