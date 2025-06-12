# backend/app/src/utils/formatters.py
# -*- coding: utf-8 -*-
"""
Модуль функцій форматування даних.

Цей модуль надає утиліти для перетворення даних у специфічні рядкові формати,
призначені для відображення користувачеві або для інших потреб виводу.
Включає функції для форматування дати/часу та грошових сум.
"""
import logging
from datetime import datetime, date, timezone
from decimal import Decimal, InvalidOperation
from typing import Union, Optional

# Configure logger for this module
logger = logging.getLogger(__name__)

def format_datetime(
    dt_obj: Optional[Union[datetime, date]],
    format_str: str = "%Y-%m-%d %H:%M:%S %Z%z",
    default_if_none: str = "-"
) -> str:
    """
    Форматує об'єкт datetime або date у рядок.

    Args:
        dt_obj: Об'єкт datetime або date для форматування. Може бути None.
        format_str: Рядок формату для strftime.
        default_if_none: Рядок, що повертається, якщо dt_obj є None. За замовчуванням "-".

    Returns:
        Відформатований рядок datetime, або default_if_none, якщо вхідні дані None.
    """
    if dt_obj is None:
        return default_if_none

    try:
        return dt_obj.strftime(format_str)
    except ValueError as e:
        logger.error(f"Помилка форматування об'єкта datetime '{dt_obj}' за форматом '{format_str}': {e}", exc_info=True)
        return str(dt_obj)
    except Exception as e:
        logger.error(f"Неочікувана помилка при форматуванні datetime '{dt_obj}': {e}", exc_info=True)
        return str(dt_obj)

def format_currency(
    amount: Optional[Union[Decimal, float, int]],
    currency_code: str = "USD",
    decimal_places: int = 2,
    default_if_none: str = "-",
    include_symbol: bool = True,
    symbol_before_amount: bool = True
) -> str:
    """
    Форматує числову суму як рядок валюти.
    Базовий форматувальник; для складної локалізації використовуйте спеціалізовану бібліотеку.

    Args:
        amount: Числова сума. Може бути None.
        currency_code: 3-літерний ISO код валюти.
        decimal_places: Кількість десяткових знаків.
        default_if_none: Рядок, що повертається, якщо сума None.
        include_symbol: Чи включати символ валюти.
        symbol_before_amount: Позиція символу валюти.

    Returns:
        Відформатований рядок валюти.
    """
    if amount is None:
        return default_if_none

    try:
        if not isinstance(amount, Decimal):
            amount_decimal = Decimal(str(amount))
        else:
            amount_decimal = amount

        num_format_str = f"{{:,.{decimal_places}f}}"
        formatted_number = num_format_str.format(amount_decimal)

    except (InvalidOperation, ValueError, TypeError) as e:
        logger.error(f"Недійсна сума для форматування валюти: {amount}. Помилка: {e}", exc_info=True)
        return str(amount)

    if not include_symbol:
        return formatted_number

    symbols = {
        "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "UAH": "₴",
    }
    symbol = symbols.get(currency_code.upper(), currency_code + " ")

    if symbol_before_amount:
        return f"{symbol}{formatted_number}"
    else:
        return f"{formatted_number}{symbol}"


if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Демонстрація Утиліт Форматування ---")

    logger.info("\n--- Тести Форматування Дати/Часу ---")
    now_utc = datetime.now(timezone.utc)
    now_naive = datetime.now()
    today_date = date.today()

    logger.info(f"Формат за замовчуванням (UTC): {format_datetime(now_utc)}")
    logger.info(f"Формат за замовчуванням (наївний): {format_datetime(now_naive)}")
    logger.info(f"Спеціальний формат (РРРР-ММ-ДД): {format_datetime(now_utc, '%Y-%m-%d')}")
    logger.info(f"Спеціальний формат (об'єкт date, РРРР-ММ-ДД): {format_datetime(today_date, '%Y-%m-%d')}")
    logger.info(f"Читабельний формат: {format_datetime(now_utc, '%d %b %Y, %I:%M %p %Z')}")
    logger.info(f"Вхід None: {format_datetime(None)}")
    logger.info(f"Вхід None зі спеціальним значенням за замовчуванням: {format_datetime(None, default_if_none='Н/Д')}")

    logger.info("\n--- Тести Форматування Валюти ---")
    amount1 = Decimal("12345.6789")
    amount2 = 1500.50
    amount3 = 75
    amount_neg = Decimal("-250.75")

    logger.info(f"USD за замовчуванням: {format_currency(amount1)}")
    logger.info(f"EUR за замовчуванням: {format_currency(amount1, 'EUR')}")
    logger.info(f"UAH за замовчуванням: {format_currency(amount1, 'UAH')}")
    logger.info(f"GBP, 3 десяткових знаки: {format_currency(amount1, 'GBP', decimal_places=3)}")
    logger.info(f"USD, без символу: {format_currency(amount2, 'USD', include_symbol=False)}")
    logger.info(f"USD, символ після: {format_currency(amount3, 'USD', symbol_before_amount=False)}")
    logger.info(f"Цілочисельна сума JPY: {format_currency(amount3, 'JPY')}")
    logger.info(f"JPY, 0 десяткових знаків: {format_currency(amount3, 'JPY', decimal_places=0)}")
    logger.info(f"Від'ємна сума EUR: {format_currency(amount_neg, 'EUR')}")
    logger.info(f"Сума None: {format_currency(None)}")
    logger.info(f"Недійсна сума (рядок): {format_currency('abc')}")

    amount_float_precision = 0.1 + 0.2
    logger.info(f"Тест точності float (0.1 + 0.2 = {amount_float_precision}): {format_currency(amount_float_precision, 'USD', decimal_places=18)}")
