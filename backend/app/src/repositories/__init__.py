# backend/app/src/repositories/__init__.py
# -*- coding: utf-8 -*-
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

from backend.app.src.repositories.base import BaseRepository # Оновлено на абсолютний шлях
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

__all__ = [
    "BaseRepository",
]

logger.debug("Пакет 'repositories' успішно ініціалізовано.")
