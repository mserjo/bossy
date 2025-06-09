# backend/app/src/utils/helpers.py

"""
General-purpose miscellaneous helper functions.
"""

import logging
from typing import Any, Optional, TypeVar, Callable
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def get_current_utc_timestamp() -> datetime:
    """
    Returns the current timestamp in UTC.

    Returns:
        A datetime object representing the current time in UTC.
    """
    return datetime.now(timezone.utc)

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Miscellaneous Helper Utilities --- Demonstration")

    logger.info("\n--- Current UTC Timestamp ---")
    current_time = get_current_utc_timestamp()
    logger.info(f"Current UTC time: {current_time.isoformat()}")
    assert current_time.tzinfo == timezone.utc

    logger.info("\nHelpers module is ready for more utility functions.")
