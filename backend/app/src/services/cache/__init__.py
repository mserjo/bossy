# backend/app/src/services/cache/__init__.py
"""
Ініціалізаційний файл для модуля сервісів кешування.

Цей модуль реекспортує базовий клас сервісу кешування (`BaseCacheService`)
та конкретні реалізації сервісів кешування, такі як Redis та InMemory.
"""

from backend.app.src.config import logger

# Явний імпорт сервісів для кращої читабельності та статичного аналізу
from backend.app.src.services.cache.base_cache import BaseCacheService
from backend.app.src.services.cache.redis_service import RedisCacheService
from backend.app.src.services.cache.memory_service import InMemoryCacheService

__all__ = [
    "BaseCacheService",
    "RedisCacheService",
    "InMemoryCacheService",
]

logger.info(f"Сервіси кешування експортують: {__all__}")
