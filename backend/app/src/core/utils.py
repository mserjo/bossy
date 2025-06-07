# backend/app/src/core/utils.py

"""
This module provides miscellaneous utility functions that are reusable
across different parts of the application and don't fit into more
specific utility modules (like validators.py or security.py from config).
"""

import random
import string
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Optional, List, Dict, Union
from decimal import Decimal, ROUND_HALF_UP

# --- String Utilities ---

def generate_random_string(length: int, chars: str = string.ascii_letters + string.digits) -> str:
    """
    Generates a random string of a specified length from a given set of characters.

    Args:
        length (int): The desired length of the random string.
        chars (str): A string containing characters to choose from.
                     Defaults to alphanumeric characters (letters + digits).

    Returns:
        str: The generated random string.
    """
    if length <= 0:
        return ""
    return "".join(random.choice(chars) for _ in range(length))

def generate_random_numeric_string(length: int) -> str:
    """
    Generates a random string consisting only of digits.
    """
    return generate_random_string(length, string.digits)

def slugify(text: str, separator: str = "-") -> str:
    """
    Generates a URL-friendly slug from a given text.
    Converts to lowercase, removes non-alphanumeric characters (except spaces and hyphens),
    replaces spaces and repeated hyphens with a single specified separator.
    """
    if not text:
        return ""
    text = text.lower()
    # Remove special characters, keeping spaces and hyphens for now
    text = re.sub(r"[^a-z0-9\s-]", "", text, flags=re.UNICODE)
    # Replace spaces and multiple hyphens with a single separator
    text = re.sub(r"[\s-]+|-", separator, text).strip(separator)
    return text

def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncates a string to a maximum length, adding a suffix if truncated.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

# --- Datetime Utilities ---

def get_current_utc_timestamp() -> datetime:
    """Returns the current datetime in UTC with timezone information."""
    return datetime.now(timezone.utc)

def format_datetime_for_display(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S %Z%z") -> str:
    """
    Formats a datetime object into a string for display purposes.
    Defaults to a common ISO-like format with timezone.
    """
    if not dt:
        return ""
    return dt.strftime(fmt)

def human_readable_timedelta(delta: timedelta) -> str:
    """
    Converts a timedelta object into a human-readable string (e.g., "2 days, 3 hours").
    """
    seconds = int(delta.total_seconds())
    if seconds < 0:
        return "(negative duration)"
    if seconds == 0:
        return "0 seconds"

    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds > 0 or not parts: # Show seconds if it's the only unit or if non-zero
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")

    return ", ".join(parts)

# --- Numeric Utilities ---

def round_decimal(number: Union[float, Decimal, str], decimal_places: int = 2) -> Decimal:
    """
    Rounds a number to a specified number of decimal places using Decimal for precision.
    Uses ROUND_HALF_UP rounding method.
    """
    if not isinstance(number, Decimal):
        number = Decimal(str(number))
    quantizer = Decimal("1e-" + str(decimal_places)) # e.g., Decimal('0.01') for 2 places
    return number.quantize(quantizer, rounding=ROUND_HALF_UP)

# --- Collection Utilities ---

def chunk_list(data: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Splits a list into smaller chunks of a specified size.
    Example: chunk_list([1,2,3,4,5], 2) -> [[1,2], [3,4], [5]]
    """
    if chunk_size <= 0:
        raise ValueError("Chunk size must be a positive integer.")
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

def get_from_dict_or_object(data: Union[Dict[str, Any], object], key: str, default: Optional[Any] = None) -> Any:
    """
    Safely retrieves a value from a dictionary or an attribute from an object.

    Args:
        data: The dictionary or object to retrieve from.
        key: The key or attribute name.
        default: The default value to return if the key/attribute is not found.

    Returns:
        The value if found, otherwise the default.
    """
    if isinstance(data, dict):
        return data.get(key, default)
    else:
        return getattr(data, key, default)

# --- Other Utilities ---

def generate_unique_code(length: int = 6, prefix: str = "") -> str:
    """
    Generates a unique code, typically for things like invitation codes or short IDs.
    Combines a prefix with a random string. For true uniqueness in a distributed system,
    more robust mechanisms (e.g., UUIDs, database sequences) are needed.
    This is more for human-readable, relatively short codes.
    """
    random_part = generate_random_string(length, string.ascii_uppercase + string.digits)
    return f"{prefix}{random_part}".upper()


if __name__ == "__main__":
    print("--- Core Utilities Demonstration ---")

    # String utils
    print(f"\nRandom string (10 chars): {generate_random_string(10)}")
    print(f"Random numeric string (8 chars): {generate_random_numeric_string(8)}")
    print(f"Slugify 'Hello World! 123': {slugify('Hello World! 123')}")
    print(f"Slugify '  --Extra--Hyphens--  ': {slugify('  --Extra--Hyphens--  ')}")
    print(f"Truncate 'This is a long string' (max 10): {truncate_string('This is a long string', 10)}")
    print(f"Truncate 'Short' (max 10): {truncate_string('Short', 10)}")

    # Datetime utils
    utc_now = get_current_utc_timestamp()
    print(f"\nCurrent UTC Timestamp: {utc_now}")
    print(f"Formatted UTC Timestamp: {format_datetime_for_display(utc_now)}")
    delta_example = timedelta(days=2, hours=3, minutes=30, seconds=5)
    print(f"Human readable timedelta ({delta_example}): {human_readable_timedelta(delta_example)}")
    print(f"Human readable timedelta (0 seconds): {human_readable_timedelta(timedelta(seconds=0))}")

    # Numeric utils
    print(f"\nRound 123.456 (2 places): {round_decimal(123.456, 2)}")
    print(f"Round 123.454 (2 places): {round_decimal(123.454, 2)}")
    print(f"Round 123.45 (0 places): {round_decimal(123.45, 0)}")

    # Collection utils
    my_list = list(range(10))
    print(f"\nChunk list {my_list} (size 3): {chunk_list(my_list, 3)}")
    my_dict = {"name": "Alice", "age": 30}
    print(f"Get 'name' from dict: {get_from_dict_or_object(my_dict, 'name')}")
    print(f"Get 'city' from dict (default 'N/A'): {get_from_dict_or_object(my_dict, 'city', 'N/A')}")

    class MyObj:
        def __init__(self):
            self.title = "Test Object"
    my_obj_instance = MyObj()
    print(f"Get 'title' from object: {get_from_dict_or_object(my_obj_instance, 'title')}")

    # Other utils
    print(f"\nUnique code (prefix 'INV-'): {generate_unique_code(6, 'INV-')}")
    print(f"Unique code (default): {generate_unique_code()}")
