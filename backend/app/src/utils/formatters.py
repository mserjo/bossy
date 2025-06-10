# backend/app/src/utils/formatters.py

"""
Utility functions for formatting data for display or specific output requirements.
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
    Formats a datetime or date object into a string.

    Args:
        dt_obj: The datetime or date object to format. Can be None.
        format_str: The strftime format string.
        default_if_none: String to return if dt_obj is None. Defaults to "-".

    Returns:
        The formatted datetime string, or default_if_none if input is None.
    """
    if dt_obj is None:
        return default_if_none

    try:
        return dt_obj.strftime(format_str)
    except ValueError as e:
        logger.error(f"Error formatting datetime object '{dt_obj}' with format '{format_str}': {e}", exc_info=True)
        return str(dt_obj)
    except Exception as e:
        logger.error(f"Unexpected error formatting datetime '{dt_obj}': {e}", exc_info=True)
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
    Formats a numeric amount as a currency string.
    Basic formatter; for complex localization, use a dedicated library.

    Args:
        amount: The numeric amount. Can be None.
        currency_code: 3-letter ISO currency code.
        decimal_places: Number of decimal places.
        default_if_none: String to return if amount is None.
        include_symbol: Whether to include the currency symbol.
        symbol_before_amount: Position of the currency symbol.

    Returns:
        The formatted currency string.
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
        logger.error(f"Invalid amount for currency formatting: {amount}. Error: {e}", exc_info=True)
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

    logger.info("--- Formatting Utilities --- Demonstration")

    logger.info("\n--- Datetime Formatting Tests ---")
    now_utc = datetime.now(timezone.utc)
    now_naive = datetime.now()
    today_date = date.today()

    logger.info(f"Default format (UTC): {format_datetime(now_utc)}")
    logger.info(f"Default format (naive): {format_datetime(now_naive)}")
    logger.info(f"Custom format (YYYY-MM-DD): {format_datetime(now_utc, '%Y-%m-%d')}")
    logger.info(f"Custom format (date object, YYYY-MM-DD): {format_datetime(today_date, '%Y-%m-%d')}")
    logger.info(f"Readable format: {format_datetime(now_utc, '%d %b %Y, %I:%M %p %Z')}") # Corrected: %p without leading zero for AM/PM
    logger.info(f"None input: {format_datetime(None)}")
    logger.info(f"None input with custom default: {format_datetime(None, default_if_none='N/A')}")

    logger.info("\n--- Currency Formatting Tests ---")
    amount1 = Decimal("12345.6789")
    amount2 = 1500.50
    amount3 = 75
    amount_neg = Decimal("-250.75")

    logger.info(f"USD default: {format_currency(amount1)}")
    logger.info(f"EUR default: {format_currency(amount1, 'EUR')}")
    logger.info(f"UAH default: {format_currency(amount1, 'UAH')}")
    logger.info(f"GBP, 3 decimal places: {format_currency(amount1, 'GBP', decimal_places=3)}")
    logger.info(f"USD, no symbol: {format_currency(amount2, 'USD', include_symbol=False)}")
    logger.info(f"USD, symbol after: {format_currency(amount3, 'USD', symbol_before_amount=False)}")
    logger.info(f"Integer amount JPY: {format_currency(amount3, 'JPY')}")
    logger.info(f"JPY, 0 decimal places: {format_currency(amount3, 'JPY', decimal_places=0)}")
    logger.info(f"Negative amount EUR: {format_currency(amount_neg, 'EUR')}")
    logger.info(f"None amount: {format_currency(None)}")
    logger.info(f"Invalid amount (string): {format_currency('abc')}")

    amount_float_precision = 0.1 + 0.2
    logger.info(f"Float precision test (0.1 + 0.2 = {amount_float_precision}): {format_currency(amount_float_precision, 'USD', decimal_places=18)}")
