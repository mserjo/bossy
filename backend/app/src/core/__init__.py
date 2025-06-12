# backend/app/src/core/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет ядра (core) програми Kudos.

Цей пакет об'єднує основні компоненти, які є фундаментом для
бізнес-логіки та функціональності програми. Сюди входять:
- Базові класи та структури (`base.py`)
- Глобальні константи (`constants.py`)
- Загальні залежності FastAPI (`dependencies.py`)
- Системні переліки (Enums) (`dicts.py`)
- Кастомні винятки (`exceptions.py`)
- Система дозволів (`permissions.py`)
- Допоміжні утиліти (`utils.py`)
- Функції-валідатори (`validators.py`)
"""

# Приклад ре-експорту для зручності (розкоментуйте та адаптуйте за потреби):
# from .exceptions import ItemNotFoundError, PermissionDeniedError
# from .constants import MAX_ITEMS_PER_PAGE

# __all__ = [
# "ItemNotFoundError",
# "PermissionDeniedError",
# "MAX_ITEMS_PER_PAGE",
# ]
