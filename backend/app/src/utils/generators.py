# backend/app/src/utils/generators.py

"""
Utility functions for generating various types of data, such as random codes or unique slugs.
"""

import logging
import random
import string
import secrets
import re
from typing import Optional, List # Added List

# Attempt to import a slugify library, fallback to basic implementation
try:
    from slugify import slugify as awesome_slugify
except ImportError:
    awesome_slugify = None

# Configure logger for this module
logger = logging.getLogger(__name__)

def generate_random_code(length: int = 6, type: str = "numeric") -> str:
    """
    Generates a random code of a specified length and type.

    Args:
        length: The desired length of the code. Defaults to 6.
        type: The type of characters to use in the code.
              Options: "numeric", "alphanumeric", "alpha_upper", "alpha_lower", "hex".
              Defaults to "numeric".

    Returns:
        A randomly generated code string.
    Raises:
        ValueError: if length is not positive or type is invalid.
    """
    if not isinstance(length, int) or length <= 0:
        logger.error(f"Invalid length for random code: {length}. Must be positive integer.")
        raise ValueError("Length must be a positive integer.")

    char_set = ""
    if type == "numeric":
        char_set = string.digits
    elif type == "alphanumeric":
        char_set = string.ascii_letters + string.digits
    elif type == "alpha_upper":
        char_set = string.ascii_uppercase
    elif type == "alpha_lower":
        char_set = string.ascii_lowercase
    elif type == "hex":
        char_set = string.hexdigits.lower()
    else:
        logger.error(f"Invalid type for random code: {type}.")
        raise ValueError("Invalid type specified. Choose from 'numeric', 'alphanumeric', 'alpha_upper', 'alpha_lower', 'hex'.")

    if not char_set:
        raise ValueError("Character set for code generation is empty.")

    try:
        code = ''.join(secrets.choice(char_set) for _ in range(length))
    except NameError:
        logger.warning("secrets module not available, falling back to random.SystemRandom for code generation.")
        try:
            sys_random = random.SystemRandom()
            code = ''.join(sys_random.choice(char_set) for _ in range(length))
        except AttributeError:
            logger.warning("random.SystemRandom not available, falling back to basic random.choice for code generation.")
            code = ''.join(random.choice(char_set) for _ in range(length))

    logger.debug(f"Generated random code of type '{type}' and length {length}: '{code[:3]}...'")
    return code

def generate_unique_slug(text: str, existing_slugs: Optional[List[str]] = None, max_length: int = 255) -> str:
    """
    Generates a URL-friendly slug from a given text string, ensuring uniqueness
    against an optional list of existing slugs by appending a counter if needed.

    Args:
        text: The input string to slugify (e.g., a title).
        existing_slugs: An optional list of already existing slugs to check against for uniqueness.
        max_length: The maximum allowed length for the slug.

    Returns:
        A unique, URL-friendly slug string.
    """
    if not text:
        return generate_random_code(length=8, type="alphanumeric").lower()

    if awesome_slugify:
        base_slug = awesome_slugify(text, max_length=max_length, word_boundary=True, save_order=True)
    else:
        text = re.sub(r'[^\w\s-]', '', text.lower().strip())
        text = re.sub(r'[-\s]+', '-', text)
        base_slug = text.strip('-')
        if len(base_slug) > max_length:
            trimmed_slug = base_slug[:max_length]
            last_hyphen = trimmed_slug.rfind('-')
            if last_hyphen > 0:
                base_slug = trimmed_slug[:last_hyphen]
            else:
                base_slug = trimmed_slug
        if not base_slug:
            return generate_random_code(length=8, type="alphanumeric").lower()

    if not existing_slugs:
        return base_slug

    slug = base_slug
    counter = 1
    while slug in existing_slugs:
        suffix = f"-{counter}"
        if len(base_slug) + len(suffix) > max_length:
            truncated_base_len = max_length - len(suffix)
            base_slug_for_suffix = base_slug[:truncated_base_len] if truncated_base_len > 0 else ""
            slug = f"{base_slug_for_suffix}{suffix}"
            if not base_slug_for_suffix:
                 slug = f"slug-{counter}"
        else:
            slug = f"{base_slug}{suffix}"
        counter += 1
        if counter > 1000:
            logger.warning(f"Could not generate a unique slug for '{text}' after 1000 attempts. Returning with random suffix.")
            return f"{base_slug}-{generate_random_code(5, 'alphanumeric')}"

    logger.debug(f"Generated slug '{slug}' for text '{text}'.")
    return slug

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Data Generation Utilities --- Demonstration")

    logger.info("\n--- Random Code Generation ---")
    logger.info(f"Numeric (6): {generate_random_code(6, 'numeric')}")
    logger.info(f"Alphanumeric (8): {generate_random_code(8, 'alphanumeric')}")
    logger.info(f"Alpha Upper (10): {generate_random_code(10, 'alpha_upper')}")
    logger.info(f"Alpha Lower (5): {generate_random_code(5, 'alpha_lower')}")
    logger.info(f"Hex (12): {generate_random_code(12, 'hex')}")
    try:
        generate_random_code(0)
    except ValueError as e:
        logger.info(f"Caught expected error for length 0: {e}")
    try:
        generate_random_code(6, "invalid_type")
    except ValueError as e:
        logger.info(f"Caught expected error for invalid type: {e}")

    logger.info("\n--- Unique Slug Generation ---")
    existing = ["my-first-post", "my-first-post-1", "another-title"]

    title1 = "My First Post!"
    slug1 = generate_unique_slug(title1, existing)
    logger.info(f"Title: '{title1}' -> Slug: '{slug1}'")
    assert slug1 not in existing
    existing.append(slug1)

    title2 = "Another Title"
    slug2 = generate_unique_slug(title2, existing)
    logger.info(f"Title: '{title2}' -> Slug: '{slug2}'")
    assert slug2 not in existing
    existing.append(slug2)

    title3 = "A Completely New Title"
    slug3 = generate_unique_slug(title3, existing)
    logger.info(f"Title: '{title3}' -> Slug: '{slug3}'")
    assert slug3 not in existing
    existing.append(slug3)

    title4 = "With special --- characters & stuff"
    slug4 = generate_unique_slug(title4, existing)
    logger.info(f"Title: '{title4}' -> Slug: '{slug4}'")
    assert slug4 not in existing
    existing.append(slug4)

    title5_long = "This is a very long title that will definitely exceed the maximum length for slugs and should be truncated gracefully"
    slug5 = generate_unique_slug(title5_long, existing, max_length=50)
    logger.info(f"Title: '{title5_long[:60]}...' -> Slug (max 50): '{slug5}' (Length: {len(slug5)})")
    assert len(slug5) <= 50
    assert slug5 not in existing
    existing.append(slug5)

    existing_for_trunc = ["short-title"]
    title6 = "Short Title"
    slug6 = generate_unique_slug(title6, existing_for_trunc, max_length=10)
    logger.info(f"Title: '{title6}' -> Slug (max 10, with existing 'short-title'): '{slug6}' (Length: {len(slug6)})")
    assert len(slug6) <= 10
    assert slug6 not in existing_for_trunc
    existing_for_trunc.append(slug6)

    slug7 = generate_unique_slug("", existing)
    logger.info(f"Title: '' -> Slug: '{slug7}'")
    assert len(slug7) == 8
    assert slug7 not in existing

    if awesome_slugify:
        logger.info("Using 'python-slugify' library for slug generation.")
    else:
        logger.warning("Optional 'python-slugify' library not found. Using basic internal slugify function.")
