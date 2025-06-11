# backend/app/src/models/system/__init__.py
"""
Пакет моделей SQLAlchemy для системних сутностей.

Цей пакет містить моделі, що представляють системні налаштування,
записи моніторингу (логи, метрики продуктивності) та стан здоров'я
різних компонентів системи Kudos.

Моделі експортуються для зручного доступу з інших частин програми.
"""

from .settings import SystemSetting
from .monitoring import SystemLog, PerformanceMetric
from .health import ServiceHealthStatus

__all__ = [
    "SystemSetting",
    "SystemLog",
    "PerformanceMetric",
    "ServiceHealthStatus",
]

# Майбутні моделі, пов'язані з системними функціями (наприклад, AuditLog),
# також можуть бути додані сюди для експорту.
