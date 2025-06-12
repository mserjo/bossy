# backend/app/src/core/__init__.py
# -*- coding: utf-8 -*-
"""Пакет ядра (core) додатку.

Цей пакет об'єднує основні компоненти, які є фундаментом для
бізнес-логіки та функціональності програми. Сюди можуть входити:
- Базові класи, моделі або схеми, що використовуються в усьому проекті (`base.py`).
- Глобальні константи та переліки (`constants.py`, `dicts.py`).
- Загальні залежності (dependencies) для FastAPI, що використовуються в обробниках запитів (`dependencies.py`).
- Кастомні класи винятків (exceptions), специфічні для домену програми (`exceptions.py`).
- Логіка системи дозволів (permissions) та авторизації (`permissions.py`).
- Інші допоміжні утиліти або валідатори, що мають широке застосування в ядрі системи (`utils.py`, `validators.py`).

Файл `__init__.py` може використовуватися для ре-експорту ключових компонентів
з модулів цього пакету, щоб спростити їх імпорт в інших частинах додатку.
Наприклад: `from backend.app.src.core import SomeCoreException`.
"""

from backend.app.src.config import logger

# Приклади ре-експорту (розкоментуйте та адаптуйте за потреби):
# from backend.app.src.core.exceptions import ItemNotFoundError, PermissionDeniedError
# from backend.app.src.core.constants import MAX_ITEMS_PER_PAGE, DEFAULT_LANGUAGE
# from backend.app.src.core.dependencies import get_current_active_user

# Список символів, які будуть експортовані при `from backend.app.src.core import *`.
# Рекомендується використовувати явні імпорти, але `__all__` визначає поведінку "зірочкового" імпорту.
# __all__ = [
#     # Exceptions
#     "ItemNotFoundError",
#     "PermissionDeniedError",
#     # Constants
#     "MAX_ITEMS_PER_PAGE",
#     "DEFAULT_LANGUAGE",
#     # Dependencies
#     "get_current_active_user",
# ]

logger.debug("Пакет ядра `core` ініціалізовано.")
