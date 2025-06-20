# backend/app/src/utils/__init__.py
# -*- coding: utf-8 -*-
"""Пакет `utils` містить різноманітні допоміжні модулі та функції для додатку.

Модулі в цьому пакеті надають логіку для повторного використання у загальних задачах,
таких як хешування, операції безпеки, валідація даних, форматування, генерація даних,
перетворення типів та інші допоміжні операції.

Цей файл `__init__.py` ініціалізує пакет `utils` та використовується
для вибіркового імпорту та ре-експорту часто використовуваних утиліт.
Це дозволяє зробити їх доступними безпосередньо з простору імен `backend.app.src.utils`,
спрощуючи імпорти в інших частинах проекту. Наприклад, замість
`from backend.app.src.utils.hash import get_password_hash` можна буде
використовувати `from backend.app.src.utils import get_password_hash`.
"""

# Імпорт та ре-експорт корисних функцій з модулів цього пакету.
# Це формує публічний API пакету `utils`.
from backend.app.src.utils.converters import markdown_to_html
from backend.app.src.utils.formatters import format_currency, format_datetime
from backend.app.src.utils.generators import generate_random_code, generate_unique_slug
from backend.app.src.utils.hash import get_password_hash, verify_password
from backend.app.src.utils.helpers import get_current_utc_timestamp
from backend.app.src.utils.security import generate_secure_random_string
from backend.app.src.utils.validators import is_strong_password, is_valid_phone_number
from backend.app.src.config.logging import setup_logging
logger = setup_logging()


# Список символів, які експортуються при використанні `from backend.app.src.utils import *`.
# Рекомендується явно імпортувати необхідні функції, але `__all__` визначає поведінку "зірочкового" імпорту.
__all__ = [
    # З converters.py
    "markdown_to_html",
    # З formatters.py
    "format_currency",
    "format_datetime",
    # З generators.py
    "generate_random_code",
    "generate_unique_slug",
    # З hash.py
    "get_password_hash",
    "verify_password",
    # З helpers.py
    "get_current_utc_timestamp",
    # З security.py
    "generate_secure_random_string",
    # З validators.py
    "is_strong_password",
    "is_valid_phone_number",
]

logger.debug("Пакет допоміжних утиліт `utils` успішно ініціалізовано.")
