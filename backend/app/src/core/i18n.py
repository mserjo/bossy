# backend/app/src/core/i18n.py
# -*- coding: utf-8 -*-
"""
Цей модуль призначений для налаштування інтернаціоналізації (i18n)
та локалізації (l10n) в додатку FastAPI.
"""

from fastapi import Request, Header
from typing import Optional, List, Dict, Any
import json
import os

# Імпорт налаштувань, де можуть бути визначені підтримувані мови та мова за замовчуванням.
from backend.app.src.config.settings import settings
from backend.app.src.config.logging import logger

# --- Налаштування мов ---
SUPPORTED_LOCALES: List[str] = getattr(settings.app, "SUPPORTED_LOCALES", ["uk", "en"])
DEFAULT_LOCALE: str = getattr(settings.app, "DEFAULT_LOCALE", "uk")
if DEFAULT_LOCALE not in SUPPORTED_LOCALES:
    logger.warning(f"Мова за замовчуванням '{DEFAULT_LOCALE}' не в списку підтримуваних: {SUPPORTED_LOCALES}. Використовується перша з списку: '{SUPPORTED_LOCALES[0] if SUPPORTED_LOCALES else 'en'}'")
    DEFAULT_LOCALE = SUPPORTED_LOCALES[0] if SUPPORTED_LOCALES else "en"


# Шлях до каталогів з файлами перекладів
# Припускаємо, що цей файл знаходиться в backend/app/src/core/
# А каталоги локалей в backend/app/src/locales/
APP_SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # backend/app/src/
LOCALES_DIR = os.path.join(APP_SRC_DIR, "locales")

# Кеш для завантажених перекладів
translations_cache: Dict[str, Dict[str, str]] = {}

def load_translations(locale: str) -> Dict[str, str]:
    """
    Завантажує переклади для вказаної локалі з JSON файлу.
    Файли очікуються у форматі: locales/{locale}/translations.json
    """
    if locale in translations_cache:
        return translations_cache[locale]

    file_path = os.path.join(LOCALES_DIR, locale, "translations.json")
    try:
        # Переконуємося, що каталог локалей існує, якщо ні - то і файлу не буде
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            logger.info(f"Створено каталог для локалі: {os.path.dirname(file_path)}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            translations_cache[locale] = data
            logger.info(f"Переклади для локалі '{locale}' успішно завантажено з {file_path}")
            return data
    except FileNotFoundError:
        logger.warning(f"Файл перекладів не знайдено для локалі '{locale}' за шляхом: {file_path}. Використовуватимуться ключі.")
        translations_cache[locale] = {} # Порожній словник, якщо файл не знайдено
        return {}
    except json.JSONDecodeError:
        logger.error(f"Помилка декодування JSON у файлі перекладів для локалі '{locale}': {file_path}")
        translations_cache[locale] = {}
        return {}
    except Exception as e:
        logger.error(f"Невідома помилка при завантаженні перекладів для '{locale}': {e}")
        translations_cache[locale] = {}
        return {}

# Завантажуємо переклади для всіх підтримуваних мов при старті (або ліниво)
# for loc in SUPPORTED_LOCALES:
#    load_translations(loc) # Можна завантажити при старті додатку


async def get_locale(
    request: Optional[Request] = None,
    accept_language: Optional[str] = Header(None)
) -> str:
    """
    Визначає поточну локаль на основі заголовка Accept-Language або інших параметрів.
    """
    # 1. Query parameter (наприклад, ?lang=en) - якщо request передано
    if request:
        lang_query = request.query_params.get("lang")
        if lang_query and lang_query in SUPPORTED_LOCALES:
            return lang_query

    # 2. Cookie (наприклад, user_locale=uk) - якщо request передано
    if request:
        lang_cookie = request.cookies.get("locale")
        if lang_cookie and lang_cookie in SUPPORTED_LOCALES:
            return lang_cookie

    # 3. TODO: Налаштування мови з профілю користувача (потребує доступу до user)
    # if request and hasattr(request.state, "user") and request.state.user:
    #     user_profile_lang = getattr(request.state.user, "preferred_language", None)
    #     if user_profile_lang and user_profile_lang in SUPPORTED_LOCALES:
    #         return user_profile_lang

    # 4. Заголовок Accept-Language
    if accept_language:
        languages = [lang.split(';')[0].strip().lower() for lang in accept_language.split(',')]
        for lang_tag in languages:
            main_lang_code = lang_tag.split('-')[0]
            if lang_tag in SUPPORTED_LOCALES:
                return lang_tag
            if main_lang_code in SUPPORTED_LOCALES:
                return main_lang_code

    return DEFAULT_LOCALE

# Функція перекладу
def gettext(text_key: str, locale: Optional[str] = None, **kwargs: Any) -> str:
    """
    Перекладає рядок (ключ) на поточну або вказану локаль.
    Якщо переклад не знайдено, повертає сам ключ.
    """
    current_locale = locale
    if current_locale is None:
        # Якщо викликається поза контекстом запиту, де локаль невідома,
        # використовуємо мову за замовчуванням.
        # У контексті запиту FastAPI, локаль має бути встановлена в request.state.locale.
        # TODO: Потрібен кращий спосіб отримання локалі запиту тут, якщо locale=None.
        # Можливо, через contextvars або передачу request.
        current_locale = DEFAULT_LOCALE
        # logger.trace(f"gettext: локаль не передана, використовується дефолтна: {current_locale}")


    if current_locale not in SUPPORTED_LOCALES:
        # logger.warning(f"gettext: непідтримувана локаль '{current_locale}', використовується дефолтна: {DEFAULT_LOCALE}")
        current_locale = DEFAULT_LOCALE

    translations = load_translations(current_locale) # Ліниве завантаження
    translated_text = translations.get(text_key, text_key)

    try:
        return translated_text.format(**kwargs) if kwargs else translated_text
    except KeyError as e:
        logger.warning(f"gettext: ключ форматування '{e}' не знайдено в '{translated_text}' для ключа '{text_key}' (локаль: {current_locale})")
        return translated_text # Повертаємо без форматування при помилці

# Псевдонім для зручності
_ = gettext

# Middleware для встановлення локалі в стан запиту
async def set_request_locale_middleware(request: Request, call_next):
    """
    Middleware для визначення та встановлення поточної локалі (`request.state.locale`)
    та функції перекладу (`request.state.gettext`) для кожного запиту.
    """
    language_header = request.headers.get("accept-language")
    locale_code = await get_locale(request=request, accept_language=language_header)
    request.state.locale = locale_code

    # Робимо функцію gettext доступною через request.state для використання в ендпоінтах
    # Вона буде автоматично використовувати локаль з request.state.locale
    # Це потребує модифікації gettext для читання з request.state або передачі локалі.
    # Простіший варіант - передавати локаль явно в ендпоінтах.
    # Або ж, якщо використовувати FastAPI-Babel, він це робить автоматично.

    # Поки що, для простоти, gettext вище не залежить від request.state.
    # Якщо потрібно, щоб gettext в ендпоінтах автоматично використовував локаль запиту:
    # request.state.gettext = lambda text_key, **kwargs: gettext(text_key, locale=locale_code, **kwargs)

    logger.debug(f"Встановлено локаль для запиту: {locale_code}")
    response = await call_next(request)
    return response

# Приклад файлу backend/app/src/locales/uk/translations.json:
# {
#   "hello_world": "Привіт, світе!",
#   "greeting": "Вітаємо, {name}!",
#   "error_not_found": "Ресурс не знайдено."
# }

# Приклад файлу backend/app/src/locales/en/translations.json:
# {
#   "hello_world": "Hello, World!",
#   "greeting": "Welcome, {name}!",
#   "error_not_found": "Resource not found."
# }

# TODO: Створити ці файли з прикладами.
# TODO: Розглянути використання бібліотеки типу `python-babel` для компіляції .po файлів,
#       якщо переклади будуть зберігатися в такому форматі.
#       Для JSON файлів поточний підхід з `load_translations` є робочим.
# TODO: Інтегрувати `set_request_locale_middleware` в `main.py`.
#
# Все виглядає як хороша основа для i18n.
# `get_locale` реалізовано.
# `load_translations` та `gettext` (`_`) реалізовані для JSON файлів.
# Приклад middleware для встановлення локалі запиту.
# Шлях `LOCALES_DIR` визначено.
# Створення каталогів для локалей додано в `load_translations`.
#
# Все готово.
