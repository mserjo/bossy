# backend/app/src/core/i18n.py
# -*- coding: utf-8 -*-
"""
Цей модуль призначений для налаштування інтернаціоналізації (i18n)
та локалізації (l10n) в додатку FastAPI.

Інтернаціоналізація - це процес проектування додатку таким чином,
щоб його можна було легко адаптувати до різних мов та регіональних налаштувань.
Локалізація - це процес адаптації інтернаціоналізованого додатку
для конкретного регіону або мови шляхом перекладу тексту та додавання
локаль-специфічних компонентів.

Для FastAPI можуть використовуватися бібліотеки типу `FastAPI- zowel` (на основі Babel)
або кастомні рішення для обробки мовних файлів (наприклад, JSON, YAML, .po/.mo).

На даному етапі створюється заглушка для цього модуля.
"""

from fastapi import Request, Depends, Header
from fastapi.middleware.locale import LocaleMiddleware # Приклад, якщо використовується Starlette/FastAPI LocaleMiddleware
# from babel import Locale # type: ignore # Приклад, якщо використовується Babel
# from speaklater import pengunjung_นิยม # type: ignore # Приклад для "лінивих" перекладів
from typing import Optional, List, Dict

# Імпорт налаштувань, де можуть бути визначені підтримувані мови та мова за замовчуванням.
from backend.app.src.config.settings import settings
from backend.app.src.config.logging import logger

# --- Налаштування мов ---
# Ці значення можуть братися з `settings.app`
# SUPPORTED_LOCALES: List[str] = getattr(settings.app, "SUPPORTED_LOCALES", ["uk", "en"])
# DEFAULT_LOCALE: str = getattr(settings.app, "DEFAULT_LOCALE", "uk")
# TODO: Додати ці налаштування в `AppSettings` в `config/settings.py`.
# Приклад в AppSettings:
# SUPPORTED_LOCALES: List[str] = Field(default=["uk", "en"], description="Список підтримуваних мов (коди ISO 639-1)")
# DEFAULT_LOCALE: str = Field(default="uk", description="Мова за замовчуванням")

# Поки що визначаю тут, якщо їх немає в settings
SUPPORTED_LOCALES: List[str] = ["uk", "en"] # Українська та англійська
DEFAULT_LOCALE: str = "uk"

# Шлях до каталогів з файлами перекладів (якщо використовуються .po/.mo файли)
# LOCALE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'locales')
# Цей шлях має вказувати на `backend/app/src/locales/`
# import os
# CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) # backend/app/src/core
# APP_SRC_DIR = os.path.dirname(CURRENT_DIR) # backend/app/src
# LOCALES_DIR = os.path.join(APP_SRC_DIR, "locales")
# print(f"DEBUG: Calculated locales_dir: {LOCALES_DIR}")

# --- Функція для отримання поточної локалі з запиту ---
# Це може бути залежність FastAPI.
async def get_locale(
    request: Optional[Request] = None, # Якщо використовується як залежність, Request буде передано
    accept_language: Optional[str] = Header(None) # Отримуємо заголовок Accept-Language
) -> str:
    """
    Визначає поточну локаль на основі заголовка Accept-Language або
    інших параметрів запиту (наприклад, query parameter, cookie, user profile setting).
    Повертає код мови (наприклад, "uk", "en").
    """
    # Пріоритети визначення мови:
    # 1. Query parameter (наприклад, ?lang=en)
    # 2. Cookie (наприклад, user_locale=uk)
    # 3. Налаштування мови з профілю користувача (якщо користувач автентифікований)
    # 4. Заголовок Accept-Language
    # 5. Мова за замовчуванням

    if request:
        # 1. Перевірка query parameter 'lang'
        lang_query = request.query_params.get("lang")
        if lang_query and lang_query in SUPPORTED_LOCALES:
            # logger.trace(f"Мова визначена з query parameter: {lang_query}")
            return lang_query

        # 2. Перевірка cookie 'locale' (або іншої назви)
        lang_cookie = request.cookies.get("locale") # Назва cookie може бути іншою
        if lang_cookie and lang_cookie in SUPPORTED_LOCALES:
            # logger.trace(f"Мова визначена з cookie: {lang_cookie}")
            return lang_cookie

        # 3. TODO: Перевірка налаштувань мови з профілю користувача
        # user = getattr(request.state, 'user', None) # Якщо користувач додається до request.state
        # if user and hasattr(user, 'preferred_language') and user.preferred_language in SUPPORTED_LOCALES:
        #     return user.preferred_language

    # 4. Обробка заголовка Accept-Language
    if accept_language:
        # Приклад простої обробки: беремо першу мову з Accept-Language, що підтримується.
        # Формат Accept-Language: "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7"
        # Потрібен парсер для правильної обробки ваг (q-factors).
        # Бібліотека `babel.negotiating` може допомогти.
        # Або простий парсинг:
        languages = [lang.split(';')[0].strip().lower() for lang in accept_language.split(',')]
        for lang_tag in languages:
            # Спроба знайти точне співпадіння (наприклад, "uk-ua" -> "uk")
            # або співпадіння основного коду мови (наприклад, "uk" з "uk-ua")
            main_lang_code = lang_tag.split('-')[0]
            if lang_tag in SUPPORTED_LOCALES:
                # logger.trace(f"Мова визначена з Accept-Language (точне співпадіння): {lang_tag}")
                return lang_tag
            if main_lang_code in SUPPORTED_LOCALES:
                # logger.trace(f"Мова визначена з Accept-Language (основний код): {main_lang_code}")
                return main_lang_code

    # 5. Мова за замовчуванням
    # logger.trace(f"Використовується мова за замовчуванням: {DEFAULT_LOCALE}")
    return DEFAULT_LOCALE

# --- Функція для перекладу рядків (транслятор) ---
# Це приклад, реальна функція залежатиме від обраної бібліотеки i18n.
# Вона може використовувати об'єкт перекладу, завантажений для поточної локалі.
#
# translations_cache: Dict[str, Dict[str, str]] = {} # Простий кеш для перекладів
#
# def load_translations(locale: str) -> Dict[str, str]:
#     """Завантажує переклади для вказаної локалі (наприклад, з JSON файлу)."""
#     if locale in translations_cache:
#         return translations_cache[locale]
#
#     # Припускаємо, що переклади зберігаються в backend/app/src/locales/{locale}/messages.json
#     # file_path = os.path.join(LOCALES_DIR, locale, "messages.json")
#     # try:
#     #     with open(file_path, "r", encoding="utf-8") as f:
#     #         data = json.load(f)
#     #         translations_cache[locale] = data
#     #         return data
#     # except FileNotFoundError:
#     #     logger.warning(f"Файл перекладів не знайдено для локалі '{locale}' за шляхом: {file_path}")
#     #     translations_cache[locale] = {} # Порожній словник, якщо файл не знайдено
#     #     return {}
#     # except json.JSONDecodeError:
#     #     logger.error(f"Помилка декодування JSON у файлі перекладів для локалі '{locale}': {file_path}")
#     #     translations_cache[locale] = {}
#     #     return {}
#     # Поки що повертаємо порожній словник, якщо немає реального завантаження
#     translations_cache[locale] = {}
#     logger.debug(f"Заглушка: переклади для локалі '{locale}' не завантажено (повернуто порожній словник).")
#     return {}
#
# def _(text: str, locale: Optional[str] = None, **kwargs: Any) -> str: # Або gettext
#     """
#     Функція для перекладу рядка на поточну або вказану локаль.
#     Використовує `text` як ключ для пошуку перекладу.
#     `kwargs` можуть використовуватися для підстановки змінних у перекладений рядок.
#     """
#     if locale is None:
#         # TODO: Потрібен спосіб отримати поточну локаль запиту тут.
#         # Це може бути через контекстну змінну, залежність або передачу явно.
#         # Якщо ця функція викликається поза контекстом запиту, використовується мова за замовчуванням.
#         # current_locale = get_current_request_locale_somehow() or DEFAULT_LOCALE
#         # Поки що, для прикладу, завжди DEFAULT_LOCALE, якщо не передано.
#         # Це НЕПРАВИЛЬНО для використання в реальному часі, потрібен контекст запиту.
#         current_locale = DEFAULT_LOCALE # ЗАГЛУШКА
#         # logger.warning(f"Функція перекладу викликана без явної локалі, використовується дефолтна: {current_locale}")
#     else:
#         current_locale = locale
#
#     if current_locale not in SUPPORTED_LOCALES:
#         current_locale = DEFAULT_LOCALE # Якщо передано непідтримувану локаль
#
#     translations = load_translations(current_locale)
#     translated_text = translations.get(text, text) # Повертаємо оригінальний текст, якщо переклад не знайдено
#
#     # Проста підстановка змінних (якщо є)
#     try:
#         return translated_text.format(**kwargs) if kwargs else translated_text
#     except KeyError as e:
#         logger.warning(f"Ключ '{e}' для форматування не знайдено в перекладеному рядку: '{translated_text}' для тексту '{text}'")
#         return translated_text # Повертаємо без форматування, якщо є помилка
#
# # Для "лінивих" перекладів (корисних для визначення перекладів на рівні модуля,
# # коли локаль ще невідома):
# # lazy_gettext = pengunjung_นิยม # З speaklater або аналогічної бібліотеки

# --- Реєстрація Middleware для локалізації (якщо використовується) ---
# Це робиться в `main.py` при налаштуванні FastAPI додатку.
#
# from fastapi import FastAPI
# from starlette.middleware.locale import LocaleMiddleware # Вбудований в Starlette
# # Або кастомний middleware, що використовує get_locale
#
# app = FastAPI()
#
# # Приклад використання LocaleMiddleware (він встановлює request.state.locale)
# # app.add_middleware(LocaleMiddleware, locales=SUPPORTED_LOCALES, default_locale=DEFAULT_LOCALE)
# #
# # Або кастомний middleware:
# # @app.middleware("http")
# # async def set_request_locale_middleware(request: Request, call_next):
# #     locale_code = await get_locale(request=request, accept_language=request.headers.get("accept-language"))
# #     request.state.locale = locale_code # Зберігаємо локаль в стані запиту
# #     # Можна також встановити поточну локаль для Babel, якщо використовується
# #     # from babel.support import Translations
# #     # translations = Translations.load(LOCALE_DIR, [locale_code], domain='messages')
# #     # request.state.gettext = translations.gettext
# #     # request.state.ngettext = translations.ngettext
# #     response = await call_next(request)
# #     return response
#
# # Тоді в ендпоінтах можна отримати локаль з `request.state.locale`
# # або функцію перекладу з `request.state.gettext`.

# TODO: Вибрати та налаштувати конкретну бібліотеку/підхід для i18n.
# Можливі варіанти:
# 1. `FastAPI-babel`: Інтеграція з Babel, підтримка .po/.mo файлів.
# 2. `FastAPI-i18n`: Інший підхід, часто з JSON/YAML файлами.
# 3. Кастомне рішення на основі `LocaleMiddleware` та ручного завантаження перекладів.
#
# TODO: Створити каталоги та файли для перекладів (наприклад, `backend/app/src/locales/uk/LC_MESSAGES/messages.po`).
#
# TODO: Інтегрувати функцію перекладу (наприклад, `_()`) у всі місця, де є текст,
# що потребує перекладу (повідомлення про помилки, відповіді API, можливо, дані з БД).
#
# На даному етапі цей файл є заглушкою з прикладами та основними концепціями.
# Функція `get_locale` реалізована для визначення мови.
# Функція перекладу `_()` є дуже спрощеною і потребує доопрацювання
# або заміни на рішення з обраної бібліотеки i18n.
#
# Все готово для базової структури.
# Фактична реалізація i18n буде залежати від обраних інструментів.
#
# Все готово.
