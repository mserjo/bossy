# backend/app/src/api/v1/system/__init__.py
# -*- coding: utf-8 -*-
"""
Підпакет для системних API ендпоінтів версії v1.

Цей пакет об'єднує ендпоінти, пов'язані з управлінням
загальними налаштуваннями системи, моніторингом, перевіркою стану
та іншими системними функціями для API v1.

Основні компоненти:
- `router.py`: Визначає `system_router`, який агрегує всі системні ендпоінти v1.
  Цей роутер потім підключається до `v1_router`.
- `settings_endpoints.py`: Ендпоінти для керування налаштуваннями системи.
- `monitoring_endpoints.py`: Ендпоінти для доступу до даних моніторингу.
- `health_endpoints.py`: Ендпоінти для перевірки стану системи.
- `init_data_endpoints.py`: Ендпоінт для ініціалізації початкових даних.
"""

import logging

# Головний роутер для системних ендпоінтів v1 буде визначено в backend.app.src.api.v1.system.router
# та імпортовано тут для можливого ре-експорту.
from backend.app.src.api.v1.system.router import system_router

__all__ = [
    "system_router",
]

logger = logging.getLogger(__name__)
logger.info("Підпакет 'api.v1.system' ініціалізовано.")  # i18n: Log message, potentially for translation if logs are multilingual
