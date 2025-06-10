# backend/app/src/repositories/system/__init__.py
"""
Репозиторії для системних моделей програми Kudos.

Цей пакет містить класи репозиторіїв для кожної моделі, що стосується
системних функцій: налаштувань, моніторингу (логи, метрики) та
стану здоров'я компонентів системи.

Кожен репозиторій успадковує `BaseRepository` та надає спеціалізований
інтерфейс для роботи з конкретною системною моделлю даних.
"""

from .settings_repository import SystemSettingRepository
from .monitoring_repository import SystemLogRepository, PerformanceMetricRepository
from .health_repository import ServiceHealthStatusRepository

__all__ = [
    "SystemSettingRepository",
    "SystemLogRepository",
    "PerformanceMetricRepository",
    "ServiceHealthStatusRepository",
]
