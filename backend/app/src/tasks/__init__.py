# backend/app/src/tasks/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет для фонових завдань.

Цей пакет містить модулі, пов'язані з визначенням, конфігурацією та плануванням
фонових завдань, таких як періодичні операції, обробка черг та інші асинхронні процеси.

Модулі:
    base.py: Визначає базові класи та абстракції для фонових завдань.
    scheduler.py: Відповідає за конфігурацію та запуск планувальника завдань.
"""

import logging

# Імпорт основних компонентів з модулів пакету.
from .base import BaseTask
from .scheduler import scheduler

__all__ = [
    'BaseTask',
    'scheduler',
]

logger = logging.getLogger(__name__)
logger.info("Пакет 'tasks' ініціалізовано.")
