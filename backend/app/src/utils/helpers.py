# backend/app/src/utils/helpers.py
# -*- coding: utf-8 -*-
"""
Модуль загальних допоміжних функцій.

Цей модуль містить різноманітні невеликі утиліти та допоміжні функції,
які можуть використовуватися в різних частинах додатку та не належать
до більш спеціалізованих модулів утиліт.
"""
import logging
from typing import Any, Optional, TypeVar, Callable
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def get_current_utc_timestamp() -> datetime:
    """
    Повертає поточну мітку часу в UTC.

    Returns:
        Об'єкт datetime, що представляє поточний час в UTC.
    """
    return datetime.now(timezone.utc)

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Демонстрація Різних Допоміжних Утиліт ---")

    logger.info("\n--- Поточна мітка часу UTC ---")
    current_time = get_current_utc_timestamp()
    logger.info(f"Поточний час UTC: {current_time.isoformat()}")
    assert current_time.tzinfo == timezone.utc

    logger.info("\nМодуль helpers готовий до додавання нових допоміжних функцій.")
