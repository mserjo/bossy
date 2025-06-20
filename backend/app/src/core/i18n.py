# backend/app/src/core/i18n.py
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
from contextvars import ContextVar

from backend.app.src.config.logging import get_logger

logger = get_logger(__name__)

# TODO: Replace this dummy _ function with a real i18n translation mechanism.
# This function will be the main one used by other modules.
# The actual translation logic is in the _internal_translate function below,
# which will be aliased as _ at the end of this file.
def translate_placeholder(key: str, **kwargs: Any) -> str:
    # This placeholder will be overwritten by the real function later.
    # It's here to satisfy linters if other modules import _ from here before full init.
    return f"PLACEHOLDER: {key}"

# TODO: Make current_language configurable (e.g., via request context, settings)
# For now, hardcode for demonstration or allow setting via a global/method.
DEFAULT_LANGUAGE = "uk" # Default to Ukrainian for now, can be changed
FALLBACK_LANGUAGE = "en"

current_request_language: ContextVar[str] = ContextVar("current_request_language", default=DEFAULT_LANGUAGE)

translations: Dict[str, Dict[str, Any]] = {}
# Path to the locales directory relative to this i18n.py file's parent directory (src)
# src -> locales
# core -> i18n.py
# So, Path(__file__).resolve().parent.parent / "locales"
BASE_LOCALE_PATH = Path(__file__).resolve().parent.parent / "locales"


def load_translations(lang_code: str) -> Optional[Dict[str, Any]]:
    """Loads translation strings from a JSON file for a given language code."""
    file_path = BASE_LOCALE_PATH / lang_code / "messages.json"
    if not file_path.exists() or not file_path.is_file():
        logger.warning(f"Translation file not found for language '{lang_code}' at {file_path}")
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.info(f"Successfully loaded translations for language '{lang_code}' from {file_path}")
            return data
    except Exception as e:
        logger.error(f"Failed to load or parse translation file for language '{lang_code}' from {file_path}: {e}", exc_info=True)
        return None

def _init_translations():
    """Initializes translations by loading default and fallback languages."""
    if not translations: # Load only if not already loaded
        logger.debug(f"Initializing translations. Base path: {BASE_LOCALE_PATH}")
        fallback_data = load_translations(FALLBACK_LANGUAGE)
        if fallback_data:
            translations[FALLBACK_LANGUAGE] = fallback_data

        if DEFAULT_LANGUAGE != FALLBACK_LANGUAGE:
            default_data = load_translations(DEFAULT_LANGUAGE)
            if default_data:
                translations[DEFAULT_LANGUAGE] = default_data

        if not translations.get(DEFAULT_LANGUAGE) and not translations.get(FALLBACK_LANGUAGE):
            logger.error("No translation files could be loaded. Localization will not work.")
        elif not translations.get(DEFAULT_LANGUAGE):
            logger.warning(f"Default language '{DEFAULT_LANGUAGE}' translations not loaded. Using fallback '{FALLBACK_LANGUAGE}' if available.")


# Initialize translations when the module is loaded.
# This is a simple approach; more sophisticated apps might load on demand or at app startup.
_init_translations()

def _internal_translate(key: str, lang: Optional[str] = None, **kwargs: Any) -> str:
    """
    Translates a given key using loaded translation files.
    Uses a dot-separated key to navigate nested JSON structure.
    Formats the string with kwargs if provided.
    Falls back to FALLBACK_LANGUAGE if key is not found in current language.
    If key is not found in fallback either, returns a placeholder string.
    """
    # Determine the language to use: explicit 'lang' param, or from ContextVar
    language_from_context = current_request_language.get()
    current_lang_to_use = lang or language_from_context

    # Ensure translations are loaded for the current language if not already
    if current_lang_to_use not in translations:
        logger.warning(f"Translations for language '{current_lang_to_use}' not loaded. Attempting to load now.")
        loaded_data = load_translations(current_lang_to_use)
        if loaded_data:
            translations[current_lang_to_use] = loaded_data
        else: # If dynamic load fails, try fallback or default based on context
            logger.error(f"Failed to load '{current_lang_to_use}' for key '{key}'. Trying fallbacks.")
            # If 'lang' was specified and failed, try the context language
            if lang and language_from_context != current_lang_to_use and language_from_context in translations:
                logger.debug(f"Falling back to context language '{language_from_context}' for key '{key}'.")
                current_lang_to_use = language_from_context
            # If context language also not loaded or 'lang' was not specified, try FALLBACK_LANGUAGE
            elif FALLBACK_LANGUAGE in translations and current_lang_to_use != FALLBACK_LANGUAGE :
                logger.debug(f"Falling back to FALLBACK_LANGUAGE '{FALLBACK_LANGUAGE}' for key '{key}'.")
                current_lang_to_use = FALLBACK_LANGUAGE
            # If fallback is also not available but DEFAULT_LANGUAGE is (e.g. context was something else)
            elif DEFAULT_LANGUAGE in translations and current_lang_to_use != DEFAULT_LANGUAGE:
                logger.debug(f"Falling back to DEFAULT_LANGUAGE '{DEFAULT_LANGUAGE}' for key '{key}'.")
                current_lang_to_use = DEFAULT_LANGUAGE
            # If no relevant translations are loaded at all
            elif translations:
                 current_lang_to_use = next(iter(translations))
                 logger.debug(f"Falling back to first available loaded language '{current_lang_to_use}' for key '{key}'.")
            else:
                 return f"NO_TRANSLATIONS_LOADED_FOR_KEY: {key}"

    keys = key.split('.')

    # Try current language
    current_dict_level = translations.get(current_lang_to_use)
    translation_found = False
    result_string = ""

    if current_dict_level:
        temp_result = current_dict_level
        for k_part in keys:
            if isinstance(temp_result, dict) and k_part in temp_result:
                temp_result = temp_result[k_part]
            else:
                temp_result = None
                break

        if isinstance(temp_result, str):
            result_string = temp_result
            translation_found = True

    # Try fallback language if key not found or not a string in current language
    if not translation_found and current_lang_to_use != FALLBACK_LANGUAGE and FALLBACK_LANGUAGE in translations:
        logger.debug(f"Key '{key}' not found in '{current_lang_to_use}', trying fallback '{FALLBACK_LANGUAGE}'.")
        fallback_dict_level = translations.get(FALLBACK_LANGUAGE)
        if fallback_dict_level:
            temp_result = fallback_dict_level
            for k_part in keys:
                if isinstance(temp_result, dict) and k_part in temp_result:
                    temp_result = temp_result[k_part]
                else:
                    temp_result = None
                    break

            if isinstance(temp_result, str):
                result_string = temp_result
                translation_found = True

    if translation_found:
        try:
            return result_string.format(**kwargs) if kwargs else result_string
        except KeyError as e:
            logger.warning(f"Missing keyword '{e}' for key '{key}' in language '{current_lang_to_use if translation_found else FALLBACK_LANGUAGE}'. Using raw string: '{result_string}'")
            return result_string # Return raw string if formatting fails

    logger.warning(f"Translation key '{key}' not found in language '{current_lang_to_use}' or fallback '{FALLBACK_LANGUAGE}'.")
    return f"UNTRANSLATED: {key}"

# Alias _internal_translate to _ for external use.
_ = _internal_translate

if __name__ == "__main__":
    print(f"Base locale path: {BASE_LOCALE_PATH}")

    # Define more comprehensive dummy data
    dummy_en_data = {
        "test": {"greeting": "Hello, {name}!", "simple": "This is a test."},
        "user": {"errors": {"not_found": "User not found.", "email_exists": "Email '{email}' already exists."}},
        "only_in_en": "This message exists only in English.",
        "formatted_test": "Test with value: {value}"
    }
    dummy_uk_data = {
        "test": {"greeting": "Привіт, {name}!", "simple": "Це тест."},
        "user": {"errors": {"not_found": "Користувача не знайдено."}},
        "formatted_test": "Тест зі значенням: {value}"
        # "only_in_en" and "user.errors.email_exists" are missing for fallback testing
    }
    dummy_de_data = { # For testing dynamic load
        "test": {"greeting": "Hallo, {name}!"}
    }

    # Create/overwrite dummy files
    for lang_code, data in [("en", dummy_en_data), ("uk", dummy_uk_data), ("de", dummy_de_data)]:
        lang_dir = BASE_LOCALE_PATH / lang_code
        lang_dir.mkdir(parents=True, exist_ok=True)
        file_path = lang_dir / "messages.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Created/Overwritten dummy {lang_code}/messages.json")

    # Re-initialize translations to load the new dummy files
    translations.clear()
    # Set default language before init if it's not the hardcoded one, for testing _init_translations
    # For this test, DEFAULT_LANGUAGE is 'uk', FALLBACK_LANGUAGE is 'en'
    _init_translations()

    # current_request_language will default to DEFAULT_LANGUAGE ('uk')
    print(f"\n--- Testing with DEFAULT_LANGUAGE (from ContextVar default): {current_request_language.get()} ---")
    print(f"Greeting: {_('test.greeting', name='Світ')}")
    print(f"Simple: {_('test.simple')}")
    print(f"User not found: {_('user.errors.not_found')}")
    print(f"Formatted test: {_('formatted_test', value=123)}")
    print(f"Fallback (email_exists): {_('user.errors.email_exists', email='test@example.com')}")
    print(f"Fallback (only_in_en): {_('only_in_en')}")
    print(f"Missing key: {_('app.title_nonexistent')}")

    print(f"\n--- Testing with FALLBACK_LANGUAGE: en (setting ContextVar) ---")
    token_en = current_request_language.set("en")
    print(f"ContextVar current language: {current_request_language.get()}")
    print(f"Greeting: {_('test.greeting', name='World')}")
    print(f"Simple: {_('test.simple')}")
    print(f"User not found: {_('user.errors.not_found')}")
    print(f"Email exists: {_('user.errors.email_exists', email='test@example.com')}")
    print(f"Formatted test: {_('formatted_test', value=456)}")
    print(f"Only in en: {_('only_in_en')}")
    current_request_language.reset(token_en)

    print(f"\n--- Testing dynamic language load: 'de' (setting ContextVar) ---")
    token_de = current_request_language.set("de")
    print(f"ContextVar current language: {current_request_language.get()}")
    # Ensure 'de' is loaded if not already by _internal_translate's logic
    if "de" not in translations: # Simulate that it might not be loaded by _init_translations
        print(f"Attempting to load 'de' dynamically via _()...")

    print(f"Greeting (de): {_('test.greeting', name='Welt')}") # This will trigger load for 'de'

    if "de" in translations: # Check if 'de' was loaded
        print(f"Greeting (de) after ensuring load: {_('test.greeting', name='Welt')}")
        print(f"Simple (de - fallback to en): {_('test.simple')}")
        print(f"User not found (de - fallback to en): {_('user.errors.not_found')}")
    else:
        print("Could not switch to 'de' or load 'de' dynamically. Test for 'de' skipped/incomplete.")
    current_request_language.reset(token_de)

    # ContextVar should be back to 'uk' (its default)
    print(f"\n--- Switched back to DEFAULT_LANGUAGE (ContextVar default): {current_request_language.get()} ---")
    print(f"Greeting (uk again): {_('test.greeting', name='Україна')}")
