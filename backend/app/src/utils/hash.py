# backend/app/src/utils/hash.py

"""
Utility functions for hashing and verifying passwords.
Uses passlib library for robust password hashing.
"""

import logging
from passlib.context import CryptContext

# Configure logger for this module
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """
    Hashes a plain text password using the configured CryptContext.

    Args:
        password: The plain text password to hash.

    Returns:
        The hashed password string.
    """
    try:
        hashed_password = pwd_context.hash(password)
        logger.debug(f"Password hashed successfully (length of hash: {len(hashed_password)}).")
        return hashed_password
    except Exception as e:
        logger.error(f"Error during password hashing: {e}", exc_info=True)
        raise ValueError("Password hashing failed.")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain text password against a stored hashed password.

    Args:
        plain_password: The plain text password to verify.
        hashed_password: The stored hashed password to compare against.

    Returns:
        True if the password matches the hash, False otherwise.
    """
    if not plain_password or not hashed_password:
        logger.warning("Attempt to verify password with empty plain_password or hashed_password.")
        return False
    try:
        is_verified, new_hash = pwd_context.verify_and_update(plain_password, hashed_password)
        if new_hash:
            logger.info(f"Password verified and hash was updated (old hash len: {len(hashed_password)}, new hash len: {len(new_hash)}). Consider updating stored hash.")

        if is_verified:
            logger.debug("Password verification successful.")
        else:
            logger.debug("Password verification failed (password mismatch).")
        return is_verified
    except Exception as e:
        logger.error(f"Error during password verification: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Password Hashing Utilities --- Demonstration")

    test_password = "MySecurePassword123!"
    logger.info(f"Plain password: '{test_password}'")

    try:
        hashed_pw = get_password_hash(test_password)
        logger.info(f"Hashed password: '{hashed_pw}' (length: {len(hashed_pw)})")

        is_correct = verify_password(test_password, hashed_pw)
        logger.info(f"Verification with correct password ('{test_password}'): {is_correct}")
        assert is_correct

        incorrect_password = "WrongPassword!"
        is_incorrect = verify_password(incorrect_password, hashed_pw)
        logger.info(f"Verification with incorrect password ('{incorrect_password}'): {is_incorrect}")
        assert not is_incorrect

        empty_plain_result = verify_password("", hashed_pw)
        logger.info(f"Verification with empty plain password: {empty_plain_result}")
        assert not empty_plain_result

        empty_hashed_result = verify_password(test_password, "")
        logger.info(f"Verification with empty hashed password: {empty_hashed_result}")
        assert not empty_hashed_result

    except ValueError as ve:
        logger.error(f"A ValueError occurred during hashing demo: {ve}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during hashing demo: {e}", exc_info=True)
