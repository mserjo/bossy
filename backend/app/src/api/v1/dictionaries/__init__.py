# backend/app/src/api/v1/dictionaries/__init__.py
# -*- coding: utf-8 -*-
"""
Підпакет для API ендпоінтів версії v1, що стосуються довідників.

Цей пакет містить всі компоненти, специфічні для управління
різноманітними довідниками системи (наприклад, типи завдань, статуси,
пріоритети, ролі користувачів тощо) через API v1.

Основний експорт (очікуваний):
- `dictionaries_router`: Головний роутер для ендпоінтів довідників v1,
                       визначений в `api.v1.dictionaries.router`.
                       Він агрегує всі ендпоінти цієї функціональної групи.
"""

import logging

# Головний роутер для ендпоінтів довідників v1 буде визначено в .router
# (тобто, api/v1/dictionaries/router.py) та імпортовано тут для
# можливого ре-експорту або просто для структурування.
# from .router import router as dictionaries_router # Або просто dictionaries_router, якщо ім'я не конфліктує

# __all__ = [
#     "dictionaries_router",
# ]

logger = logging.getLogger(__name__)
logger.info("Підпакет 'api.v1.dictionaries' ініціалізовано.")
