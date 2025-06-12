# -*- coding: utf-8 -*-
# backend/app/src/repositories/__init__.py
"""
Модуль `repositories` (__init__.py).

Цей модуль слугує точкою входу для пакету репозиторіїв.
Він відповідає за ініціалізацію пакета та може використовуватися
для реекспорту ключових класів, таких як `BaseRepository`,
щоб зробити їх доступними для імпорту з `backend.app.src.repositories`.

Основні завдання:
- Ініціалізація логера для цього пакета.
- Реекспорт базового класу репозиторію (`BaseRepository`).
"""

from backend.app.src.config import logger
from .base import BaseRepository

__all__ = [
    "BaseRepository",
]

logger.debug("Пакет 'repositories' успішно ініціалізовано.")
