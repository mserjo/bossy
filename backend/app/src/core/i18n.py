# backend/app/src/core/i18n.py
# -*- coding: utf-8 -*-
# # Модуль інтернаціоналізації (i18n) та локалізації (l10n) для програми Kudos (Virtus).
# #
# # Цей модуль відповідає за налаштування та надання інструментів для перекладу
# # текстових рядків програми (повідомлення, помилки, елементи UI) різними мовами
# # з використанням JSON файлів (`messages.json`), що зберігаються у відповідних
# # директоріях локалей (наприклад, `backend/app/src/locales/uk/messages.json`).
# # Передбачається підтримка англійської (en) та української (uk) мов.
# #
# # Основні компоненти:
# # - Конфігурація шляхів до файлів локалізації.
# # - Функція для визначення поточної локалі користувача.
# # - Функція-обгортка для перекладу рядків `_()`.
# # - Кешування завантажених файлів перекладів для ефективності.

import json # Для завантаження файлів перекладів у форматі JSON
from pathlib import Path
from typing import List, Optional, Dict, Any # Dict та Any для _translations_cache та **kwargs

from fastapi import Request # Для отримання локалі з запиту

# Імпорт налаштувань та логера з конфігураційного пакету
from backend.app.src.config.settings import settings # Для доступу до DEFAULT_LOCALE, SUPPORTED_LOCALES
from backend.app.src.config.logging import get_logger

# Ініціалізація логера для цього модуля
logger = get_logger(__name__)

# --- Конфігурація i18n ---

# Шлях до директорії з файлами локалізації.
# Очікується структура: backend/app/src/locales/{locale_code}/messages.json
BASE_DIR = Path(__file__).resolve().parent.parent # Директорія `src/`
LOCALES_DIR = BASE_DIR / "locales" # Шлях: `backend/app/src/locales/`

DEFAULT_LOCALE: str = getattr(settings, "DEFAULT_LOCALE", "uk")
SUPPORTED_LOCALES: List[str] = getattr(settings, "SUPPORTED_LOCALES", ["en", "uk"])

# --- Функції для роботи з локалями ---

def get_user_locale(request: Request) -> str:
    """
    Визначає локаль користувача на основі заголовка `Accept-Language` з HTTP запиту.
    Якщо заголовок відсутній або містить непідтримувану локаль,
    повертає локаль за замовчуванням (`DEFAULT_LOCALE`).

    TODO: Розширити логіку для врахування локалі з налаштувань профілю користувача,
          якщо така функціональність передбачена (наприклад, після автентифікації).
          Локаль з профілю користувача повинна мати вищий пріоритет.

    Args:
        request (Request): Об'єкт запиту FastAPI.

    Returns:
        str: Код локалі (наприклад, "en", "uk"), що буде використовуватися для користувача.
    """
    accept_language_header = request.headers.get("accept-language")
    if accept_language_header:
        preferred_locales_raw = [lang.split(';')[0].strip() for lang in accept_language_header.split(',')]

        for lang_tag in preferred_locales_raw:
            if lang_tag in SUPPORTED_LOCALES:
                logger.debug(f"Визначено підтримувану локаль '{lang_tag}' із заголовка Accept-Language.")
                return lang_tag

            lang_code = lang_tag.split('-')[0]
            if lang_code in SUPPORTED_LOCALES:
                logger.debug(f"Визначено підтримувану локаль '{lang_code}' (з '{lang_tag}') із заголовка Accept-Language.")
                return lang_code

    logger.debug(f"Заголовок Accept-Language не знайдено або не містить підтримуваної локалі. "
                 f"Використовується локаль за замовчуванням: {DEFAULT_LOCALE}")
    return DEFAULT_LOCALE


# --- Функція перекладу ---

# Кеш для завантажених файлів перекладів (JSON даних).
# Ключ - код локалі (наприклад, "uk"), значення - словник з перекладами.
_translations_cache: Dict[str, Dict[str, Any]] = {}

def _(text: str, locale: Optional[str] = None, **kwargs: Any) -> str:
    """
    Основна функція для перекладу рядків з використанням JSON файлів.
    Шукає ключ `text` у відповідному файлі `messages.json` для вказаної `locale`.
    Підтримує просту заміну плейсхолдерів через `**kwargs` та доступ до вкладених ключів через крапку.

    Args:
        text (str): Ключ для перекладу (наприклад, "greeting" або "errors.not_found").
                    Якщо переклад не знайдено, цей ключ буде повернуто (після форматування).
        locale (Optional[str]): Код локалі (наприклад, "uk", "en"). Якщо None,
                                використовується `DEFAULT_LOCALE`.
        **kwargs: Додаткові іменовані аргументи для форматування рядка перекладу
                  (наприклад, `_("welcome_message", user="Ім'я")`).

    Returns:
        str: Перекладений та відформатований рядок, або оригінальний `text` (відформатований, якщо є `kwargs`),
             якщо переклад або ключ не знайдено.
    """
    current_locale = locale or DEFAULT_LOCALE

    if current_locale not in SUPPORTED_LOCALES:
        logger.warning(f"Спроба перекладу для непідтримуваної локалі: '{current_locale}'. Використовується '{DEFAULT_LOCALE}'.")
        current_locale = DEFAULT_LOCALE

    if current_locale not in _translations_cache:
        translations_file = LOCALES_DIR / current_locale / "messages.json"
        try:
            with open(translations_file, "r", encoding="utf-8") as f:
                _translations_cache[current_locale] = json.load(f)
            logger.info(f"Завантажено переклади для локалі: '{current_locale}' з файлу '{translations_file}'.")
        except FileNotFoundError:
            _translations_cache[current_locale] = {} # Порожній словник, якщо файл не знайдено
            logger.warning(f"Файл перекладів '{translations_file}' для локалі '{current_locale}' не знайдено.")
        except json.JSONDecodeError:
            _translations_cache[current_locale] = {} # Порожній словник при помилці JSON
            logger.error(f"Помилка декодування JSON у файлі '{translations_file}' для локалі '{current_locale}'.")

    # Отримання перекладу. Дозволяємо вкладені ключі через крапку (наприклад, "errors.not_found").
    keys = text.split('.')
    translated_value_container = _translations_cache.get(current_locale, {}) # Починаємо з кореневого словника перекладів

    final_translated_string: Optional[str] = None

    try:
        temp_value = translated_value_container
        for key_part in keys:
            if not isinstance(temp_value, dict): # Якщо на якомусь етапі вкладеності це вже не словник
                temp_value = None # Ключ не знайдено
                break
            temp_value = temp_value.get(key_part) # Рухаємось по вкладеності

        if isinstance(temp_value, str): # Якщо кінцеве значення є рядком
            final_translated_string = temp_value
        elif temp_value is not None: # Якщо знайдено, але не рядок (наприклад, це все ще вкладений об'єкт/словник)
            logger.warning(f"Значення для ключа '{text}' (локаль: {current_locale}) не є рядком, а має тип {type(temp_value)}: {temp_value}")
            # Повертаємо рядкове представлення знайденого не-рядкового значення, але без форматування kwargs
            return str(temp_value)

    except Exception as e: # Загальний виняток при доступі до ключів (малоймовірно з .get())
        logger.error(f"Неочікувана помилка при отриманні перекладу для ключа '{text}' (локаль: {current_locale}): {e}")
        final_translated_string = None # Вважаємо, що переклад не знайдено

    # Якщо переклад знайдено і він є рядком, форматуємо його
    if final_translated_string is not None:
        if kwargs:
            try:
                final_translated_string = final_translated_string.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Ключ форматування '{e}' відсутній у перекладеному рядку '{final_translated_string}' для ключа '{text}' (локаль: {current_locale}).")
        # logger.debug(f"Переклад для '{text}' (локаль: {current_locale}): '{final_translated_string}'")
        return final_translated_string
    else:
        # Якщо переклад не знайдено, повертаємо оригінальний ключ (text),
        # але також намагаємося його відформатувати, якщо передано kwargs.
        # logger.warning(f"Переклад для ключа '{text}' (локаль: {current_locale}) не знайдено. Повертається ключ '{text}'.")
        original_text_formatted = text
        if kwargs:
            try:
                original_text_formatted = original_text_formatted.format(**kwargs)
            except KeyError as e:
                 logger.warning(f"Ключ форматування '{e}' відсутній в оригінальному ключі/тексті '{text}' при спробі форматування.")
        return original_text_formatted

# --- Приклад використання та тестування ---
if __name__ == "__main__":
    # Налаштування логування для тестування
    try:
        from backend.app.src.config.logging import setup_logging
        if settings.LOG_TO_FILE:
            log_file_path = settings.LOG_DIR / f"{Path(__file__).stem}_test.log"
            setup_logging(log_file_path=log_file_path)
        else:
            setup_logging()
    except ImportError:
        import logging as base_logging
        base_logging.basicConfig(level=logging.DEBUG)
        logger.warning("Не вдалося імпортувати setup_logging. Використовується базова конфігурація логування для тестів i18n.py.")

    logger.info(f"Модуль i18n налаштовано для роботи з JSON файлами.")
    logger.info(f"  Директорія локалей: {LOCALES_DIR}")
    logger.info(f"  Локаль за замовчуванням: {DEFAULT_LOCALE}")
    logger.info(f"  Підтримувані локалі: {SUPPORTED_LOCALES}")

    # Демонстрація функції перекладу (з порожніми messages.json на даний момент)
    logger.info(f"\nТест функції перекладу `_()` (файли messages.json наразі порожні):")

    # Ключі, яких немає у файлах
    logger.info(f"  Для 'greeting' (локаль uk): '{_('greeting', 'uk')}'") # Очікується: greeting
    logger.info(f"  Для 'greeting' (локаль en): '{_('greeting', 'en')}'") # Очікується: greeting

    # Тест з kwargs
    logger.info(f"  Для 'welcome_message' (локаль uk, user='Тарас'): '{_('welcome_message', 'uk', user='Тарас')}'") # Очікується: welcome_message
    logger.info(f"  Для 'welcome_message' (локаль en, user='John'): '{_('welcome_message', 'en', user='John')}'") # Очікується: welcome_message

    # Тест з вкладеним ключем
    logger.info(f"  Для 'errors.not_found' (локаль uk): '{_('errors.not_found', 'uk')}'") # Очікується: errors.not_found
    logger.info(f"  Для 'errors.authentication.invalid_credentials' (локаль en): '{_('errors.authentication.invalid_credentials', 'en')}'")

    # Тест форматування для ключа, що не існує
    logger.info(f"  Для 'non_existent_key_with_placeholder' (локаль uk, name='Гість'): '{_('non_existent_key_with_placeholder Hello, {name}!', 'uk', name='Гість')}'")


    # Демонстрація get_user_locale (залишається такою ж, як у попередньому запиті)
    class MockRequest: # Простий макет Request для тестування get_user_locale
        def __init__(self, headers: Dict[str, str]):
            self.headers = headers

    mock_requests = [
        MockRequest(headers={"accept-language": "uk-UA, uk;q=0.9, en;q=0.8"}),
        MockRequest(headers={"accept-language": "en-US, en;q=0.9, fr;q=0.8"}),
        MockRequest(headers={"accept-language": "fr-FR, fr;q=0.9, uk;q=0.8"}),
        MockRequest(headers={"accept-language": "de, es;q=0.9"}),
        MockRequest(headers={"accept-language": "en-GB;q=0.7, en;q=0.6"}),
        MockRequest(headers={"accept-language": ""}),
        MockRequest(headers={}),
    ]

    logger.info(f"\nТест функції get_user_locale (DEFAULT_LOCALE='{DEFAULT_LOCALE}', SUPPORTED_LOCALES={SUPPORTED_LOCALES}):")
    expected_locales = ["uk", "en", "uk", DEFAULT_LOCALE, "en", DEFAULT_LOCALE, DEFAULT_LOCALE]
    for i, req in enumerate(mock_requests):
        locale_header = req.headers.get('accept-language', 'N/A')
        detected_locale = get_user_locale(req)
        status = "\033[92mУСПІХ\033[0m" if detected_locale == expected_locales[i] else "\033[91mПОМИЛКА\033[0m"
        logger.info(f"  Запит {i+1} (Accept-Language: '{locale_header}'): Визначено='{detected_locale}', Очікувано='{expected_locales[i]}' - {status}")

    logger.info("\nДемонстрацію модуля i18n завершено.")
