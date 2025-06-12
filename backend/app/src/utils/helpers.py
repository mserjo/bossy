# backend/app/src/utils/helpers.py
# -*- coding: utf-8 -*-
"""Модуль загальних допоміжних функцій.

Цей модуль призначений для розміщення різноманітних невеликих утиліт
та допоміжних функцій, які можуть використовуватися в різних частинах додатку
і не належать до більш спеціалізованих модулів утиліт (наприклад, форматерів чи генераторів).
Такі функції зазвичай виконують одну конкретну, часто використовувану операцію.
"""
import logging  # Для локального використання в __main__
from datetime import datetime, timezone
# from typing import Any, Optional, TypeVar, Callable # Залишено для майбутніх функцій

# Імпорт централізованого логера проекту
from backend.app.src.config.logging_config import setup_logging # type: ignore
logger = setup_logging()


def get_current_utc_timestamp() -> datetime:
    """Повертає поточну мітку часу в часовій зоні UTC.

    Використання UTC є рекомендованою практикою для зберігання міток часу
    в базах даних та для внутрішніх операцій, щоб уникнути проблем
    з різними часовими зонами та переходом на літній/зимовий час.

    Returns:
        Об'єкт `datetime`, що представляє поточний момент часу в UTC.
    """
    now_utc = datetime.now(timezone.utc)
    logger.debug("Згенеровано поточну мітку часу UTC: %s", now_utc.isoformat())
    return now_utc


# Приклади інших можливих допоміжних функцій (закоментовано):
# T = TypeVar('T')
# def get_optional_value(value: Optional[T], default_value: T) -> T:
#     """Повертає значення, якщо воно не None, інакше значення за замовчуванням."""
#     return value if value is not None else default_value

# def retry_operation(operation: Callable[..., Any], max_retries: int = 3, *args: Any, **kwargs: Any) -> Any:
#     """Намагається виконати операцію кілька разів у випадку помилки."""
#     last_exception = None
#     for attempt in range(max_retries):
#         try:
#             return operation(*args, **kwargs)
#         except Exception as e:
#             logger.warning(f"Спроба {attempt + 1} операції {operation.__name__} не вдалася: {e}")
#             last_exception = e
#     if last_exception:
#         raise last_exception # Піднімаємо останню помилку, якщо всі спроби невдалі
#     return None # Мало б не дійти сюди, якщо max_retries > 0


if __name__ == "__main__":
    # Налаштування базового логування для демонстрації, якщо ще не налаштовано.
    if not logging.getLogger().hasHandlers(): # Перевіряємо, чи є вже обробники у кореневого логера
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    # Використовуємо логер модуля для повідомлень в __main__
    main_logger = logging.getLogger(__name__) # Отримуємо логер для __main__ контексту
    main_logger.info("--- Демонстрація Різних Допоміжних Утиліт ---")

    main_logger.info("\n--- Тест функції get_current_utc_timestamp ---")
    current_time = get_current_utc_timestamp()
    main_logger.info("Поточний час UTC (ISO формат): %s", current_time.isoformat())
    main_logger.info("Інформація про часову зону об'єкта datetime: %s", current_time.tzinfo)
    assert current_time.tzinfo == timezone.utc, \
        f"Часова зона повинна бути UTC, але отримано: {current_time.tzinfo}"

    main_logger.info("\nМодуль `helpers` готовий до додавання нових допоміжних функцій.")
    main_logger.info("Демонстраційні виклики завершено.")
