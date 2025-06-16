# backend/app/src/tasks/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет для фонових завдань.

Цей пакет містить модулі, пов'язані з визначенням, конфігурацією та плануванням
фонових завдань, таких як періодичні операції, обробка черг та інші асинхронні процеси.

Модулі:
    base.py: Визначає базові класи та абстракції для фонових завдань.
    scheduler.py: Відповідає за конфігурацію та запуск планувальника завдань.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""

# import logging # Видалено для використання централізованого логера
from backend.app.src.config import logger # Централізований логер

# Імпорт основних компонентів з модулів пакету.
from backend.app.src.tasks.base import BaseTask
from backend.app.src.tasks.scheduler import scheduler

__all__ = [
    'BaseTask',
    'scheduler',
]

# logger = logging.getLogger(__name__) # Видалено
logger.info("Пакет 'tasks' ініціалізовано та експортує 'BaseTask', 'scheduler'.")
