# backend/app/src/core/__init__.py
# -*- coding: utf-8 -*-
# # Ініціалізаційний файл для пакету ядра (`core`) програми Kudos (Virtus).
# #
# # Цей пакет агрегує фундаментальні компоненти, що слугують основою
# # для бізнес-логіки та загальної функціональності програми. До його складу
# # зазвичай входять: базові класи, глобальні константи, кастомні винятки,
# # загальні залежності FastAPI, система дозволів, допоміжні утиліти,
# # валідатори та інші ключові елементи, які використовуються в різних
# # частинах додатку.
# #
# # Цей файл робить директорію `core` пакетом Python.
# # Він може бути порожнім або містити імпорти для зручного доступу
# # до ключових об'єктів з інших частин програми.

# Приклади ре-експорту для зручного доступу до ключових об'єктів з цього пакету.
# Розкоментуйте та адаптуйте відповідно до реальних модулів та об'єктів у вашому пакеті `core`.
#
# Наприклад, якщо у вас є `core/exceptions.py` та `core/constants.py`:
#
# from .exceptions import ItemNotFoundError, PermissionDeniedError, CustomBaseException
# from .constants import MAX_ITEMS_PER_PAGE, DEFAULT_LANGUAGE
# from .dependencies import get_current_user # Приклад загальної залежності
# from .utils import format_date_time # Приклад утиліти

# Визначення `__all__` дозволяє контролювати, що буде імпортовано при використанні `from .core import *`.
# Це корисно для створення чіткого публічного API пакету `core`.
# __all__ = [
#     # З exceptions.py
#     "ItemNotFoundError",
#     "PermissionDeniedError",
#     "CustomBaseException",
#     # З constants.py
#     "MAX_ITEMS_PER_PAGE",
#     "DEFAULT_LANGUAGE",
#     # З dependencies.py
#     "get_current_user",
#     # З utils.py
#     "format_date_time",
#     # Додайте сюди інші об'єкти, які мають бути частиною публічного API пакету `core`.
# ]
