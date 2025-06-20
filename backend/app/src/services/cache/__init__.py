# backend/app/src/services/cache/__init__.py
"""
Ініціалізаційний файл для модуля сервісів кешування.

Цей модуль реекспортує базовий клас сервісу кешування (`BaseCacheService`)
та конкретні реалізації сервісів кешування, такі як Redis та InMemory.
"""

# Явний імпорт сервісів для кращої читабельності та статичного аналізу
from backend.app.src.services.cache.base_cache import BaseCacheService
from backend.app.src.services.cache.redis_service import RedisCacheService
from backend.app.src.services.cache.memory_service import InMemoryCacheService
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

__all__ = [
    "BaseCacheService",
    "RedisCacheService",
    "InMemoryCacheService",
]

logger.info(f"Сервіси кешування експортують: {__all__}")
