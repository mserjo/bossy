# backend/app/src/utils/security.py

"""
Security-related utility functions.
"""

import logging
import secrets
import string

# Configure logger for this module
logger = logging.getLogger(__name__)

def generate_secure_random_string(length: int = 32) -> str:
    """
    Generates a cryptographically secure, URL-safe random string.

    Args:
        length: The desired length of the random string. Defaults to 32.

    Returns:
        A securely generated random string.
    Raises:
        ValueError: if length is not a positive integer.
    """
    if not isinstance(length, int) or length <= 0:
        logger.error(f"Invalid length specified for random string generation: {length}. Must be a positive integer.")
        raise ValueError("Length must be a positive integer.")

    alphabet = string.ascii_letters + string.digits

    secure_string = ''.join(secrets.choice(alphabet) for _ in range(length))
    logger.debug(f"Generated secure random string of length {length}.")
    return secure_string

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Security Utilities --- Demonstration")

    try:
        token16 = generate_secure_random_string(16)
        logger.info(f"Generated 16-character token: '{token16}' (length: {len(token16)})")
        assert len(token16) == 16

        token32 = generate_secure_random_string()
        logger.info(f"Generated 32-character token: '{token32}' (length: {len(token32)})")
        assert len(token32) == 32

        token64 = generate_secure_random_string(64)
        logger.info(f"Generated 64-character token: '{token64}' (length: {len(token64)})")
        assert len(token64) == 64

        another_token32 = generate_secure_random_string()
        logger.info(f"Another 32-character token: '{another_token32}'")
        assert token32 != another_token32

        try:
            generate_secure_random_string(0)
        except ValueError as e:
            logger.info(f"Caught expected error for length 0: {e}")

        try:
            generate_secure_random_string(-5)
        except ValueError as e:
            logger.info(f"Caught expected error for negative length: {e}")

    except Exception as e:
        logger.error(f"An unexpected error occurred during security utils demo: {e}", exc_info=True)
