# backend/app/src/utils/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет `utils` містить різноманітні допоміжні модулі та функції для додатку.

Модулі в цьому пакеті надають логіку для повторного використання у загальних задачах,
таких як хешування, операції безпеки, валідація даних, форматування, генерація даних,
перетворення типів та інші допоміжні операції.

Цей файл `__init__.py` ініціалізує пакет `utils` та може використовуватися
для вибіркового імпорту та ре-експорту часто використовуваних утиліт,
щоб зробити їх доступними безпосередньо з `backend.app.src.utils`.
Наприклад, замість `from backend.app.src.utils.hash import get_password_hash`
можна буде використовувати `from backend.app.src.utils import get_password_hash`.
"""
import logging

# Приклад: Якщо ви хочете експонувати конкретні функції безпосередньо з `backend.app.src.utils`,
# ви можете розкоментувати та налаштувати наступні рядки після створення модулів:

from backend.app.src.utils.hash import get_password_hash, verify_password
from backend.app.src.utils.security import generate_secure_random_string
from backend.app.src.utils.validators import is_strong_password, is_valid_phone_number
from backend.app.src.utils.formatters import format_datetime, format_currency
from backend.app.src.utils.generators import generate_random_code, generate_unique_slug
from backend.app.src.utils.converters import markdown_to_html
from backend.app.src.utils.helpers import get_current_utc_timestamp


__all__ = [
    "get_password_hash",
    "verify_password",
    "generate_secure_random_string",
    "is_strong_password",
    "is_valid_phone_number",
    "format_datetime",
    "format_currency",
    "generate_random_code",
    "generate_unique_slug",
    "markdown_to_html",
    "get_current_utc_timestamp",
]

logger = logging.getLogger(__name__)
logger.debug("Пакет утиліт ініціалізовано.")
