# backend/app/src/utils/formatters.py
# -*- coding: utf-8 -*-
"""Модуль функцій форматування даних.

Цей модуль надає утиліти для перетворення даних у специфічні рядкові формати,
призначені для відображення користувачеві або для інших потреб виводу.
Включає функції для форматування дати/часу та грошових сум.
"""
import logging  # Для локального використання в __main__
from datetime import datetime, date, timezone
from decimal import Decimal, InvalidOperation
from typing import Union, Optional

# Імпорт централізованого логера проекту
from backend.app.src.config.logging_config import setup_logging # type: ignore
logger = setup_logging()


def format_datetime(
    dt_obj: Optional[Union[datetime, date]],
    format_str: str = "%Y-%m-%d %H:%M:%S %Z%z",
    default_if_none: str = "-"
) -> str:
    """Форматує об'єкт datetime або date у рядок.

    Args:
        dt_obj: Об'єкт datetime або date для форматування. Може бути `None`.
        format_str: Рядок формату, який буде використовуватися функцією `strftime`.
                    За замовчуванням: "%Y-%m-%d %H:%M:%S %Z%z".
        default_if_none: Рядок, що повертається, якщо `dt_obj` є `None`.
                         За замовчуванням "-".

    Returns:
        Відформатований рядок дати/часу, або `default_if_none`, якщо вхідний об'єкт `None`.
        У випадку помилки форматування повертає рядок, отриманий через `str(dt_obj)`.
    """
    if dt_obj is None:
        return default_if_none

    try:
        # Для об'єктів date, які не мають інформації про час/таймзону, деякі формати можуть спричинити помилку.
        # Наприклад, %H, %M, %S, %Z, %z. Краще використовувати відповідні формати для date.
        # Однак, загальний strftime повинен обробляти це коректно, якщо формат відповідний.
        return dt_obj.strftime(format_str)
    except ValueError as e:
        logger.error(
            "Помилка форматування об'єкта datetime '%s' за форматом '%s': %s",
            dt_obj, format_str, e, exc_info=True
        )
        return str(dt_obj)  # Повертаємо стандартне рядкове представлення у випадку помилки
    except Exception as e: # pylint: disable=broad-except
        logger.error(
            "Неочікувана помилка при форматуванні datetime '%s': %s",
            dt_obj, e, exc_info=True
        )
        return str(dt_obj)


def format_currency( # pylint: disable=too-many-arguments
    amount: Optional[Union[Decimal, float, int]],
    currency_code: str = "UAH", # Змінено значення за замовчуванням на UAH
    decimal_places: int = 2,
    default_if_none: str = "-",
    include_symbol: bool = True,
    symbol_before_amount: bool = False # Для UAH символ зазвичай після суми
) -> str:
    """Форматує числову суму як рядок валюти.

    Цей форматувальник є базовим. Для складних потреб локалізації (різні формати чисел,
    позиції символів для різних валют, множинні форми) рекомендується
    використовувати спеціалізовані бібліотеки, такі як `babel`.

    Args:
        amount: Числова сума для форматування (Decimal, float, int). Може бути `None`.
        currency_code: 3-літерний ISO код валюти (наприклад, "USD", "EUR", "UAH").
                       Використовується для вибору символу валюти. За замовчуванням "UAH".
        decimal_places: Кількість десяткових знаків для відображення.
        default_if_none: Рядок, що повертається, якщо `amount` є `None`.
        include_symbol: Чи включати символ валюти у відформатований рядок.
        symbol_before_amount: Визначає позицію символу валюти відносно суми
                              (True - перед сумою, False - після суми).
                              За замовчуванням `False` (наприклад, "100.00 ₴").

    Returns:
        Відформатований рядок валюти. У випадку помилки конвертації суми
        повертає рядок, отриманий через `str(amount)`.
    """
    if amount is None:
        return default_if_none

    try:
        # Переконуємося, що працюємо з Decimal для точності
        if not isinstance(amount, Decimal):
            # Конвертація через рядок для уникнення проблем точності float
            amount_decimal = Decimal(str(amount))
        else:
            amount_decimal = amount

        # Форматуємо число з роздільниками тисяч та вказаною кількістю десяткових знаків
        num_format_str = f"{{:,.{decimal_places}f}}"
        formatted_number = num_format_str.format(amount_decimal)

    except (InvalidOperation, ValueError, TypeError) as e:
        logger.error(
            "Недійсна сума '%s' для форматування валюти. Помилка: %s",
            amount, e, exc_info=True
        )
        return str(amount) # Повертаємо оригінальне значення (як рядок) у випадку помилки

    if not include_symbol:
        return formatted_number

    # Словник основних символів валют. Можна розширити.
    # Для більш повного рішення краще використовувати бібліотеку, як babel.
    symbols = {
        "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "UAH": "₴",
        # Додайте інші валюти за потреби
    }
    # Отримуємо символ валюти; якщо не знайдено, використовуємо сам код валюти.
    symbol = symbols.get(currency_code.upper(), currency_code + " ") # Додаємо пробіл для невідомих кодів

    if symbol_before_amount:
        return f"{symbol}{formatted_number}"
    return f"{formatted_number}{symbol}"


if __name__ == "__main__":
    # Налаштування базового логування для демонстрації, якщо ще не налаштовано.
    if not logging.getLogger().hasHandlers(): # Перевіряємо, чи є вже обробники у кореневого логера
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    # Використовуємо логер модуля для повідомлень в __main__
    main_logger = logging.getLogger(__name__) # Отримуємо логер для __main__ контексту
    main_logger.info("--- Демонстрація Утиліт Форматування ---")

    main_logger.info("\n--- Тести Форматування Дати/Часу ---")
    now_utc = datetime.now(timezone.utc)
    now_naive = datetime.now()
    today_date = date.today()

    main_logger.info("Формат за замовчуванням (UTC): %s", format_datetime(now_utc))
    main_logger.info("Формат за замовчуванням (наївний, без таймзони): %s", format_datetime(now_naive))
    main_logger.info("Спеціальний формат (РРРР-ММ-ДД): %s", format_datetime(now_utc, '%Y-%m-%d'))
    main_logger.info("Спеціальний формат (об'єкт date, РРРР-ММ-ДД): %s", format_datetime(today_date, '%Y-%m-%d'))
    main_logger.info("Читабельний формат дати і часу: %s", format_datetime(now_utc, '%d %B %Y, %H:%M:%S %Z'))
    main_logger.info("Вхід None для дати/часу: %s", format_datetime(None))
    main_logger.info("Вхід None для дати/часу зі спеціальним значенням за замовчуванням: %s", format_datetime(None, default_if_none='Н/Д'))

    main_logger.info("\n--- Тести Форматування Валюти ---")
    amount1 = Decimal("12345.6789")
    amount2 = 1500.50
    amount3 = 75
    amount_neg = Decimal("-250.75")

    main_logger.info("UAH за замовчуванням (символ після): %s", format_currency(amount1)) # UAH типово після
    main_logger.info("USD (символ перед): %s", format_currency(amount1, 'USD', symbol_before_amount=True))
    main_logger.info("EUR (символ перед): %s", format_currency(amount1, 'EUR', symbol_before_amount=True))
    main_logger.info("GBP, 3 десяткових знаки (символ перед): %s", format_currency(amount1, 'GBP', decimal_places=3, symbol_before_amount=True))
    main_logger.info("UAH, без символу: %s", format_currency(amount2, 'UAH', include_symbol=False))
    main_logger.info("USD, символ після (нетипово для USD): %s", format_currency(amount3, 'USD', symbol_before_amount=False))
    main_logger.info("Цілочисельна сума JPY (символ перед): %s", format_currency(amount3, 'JPY', symbol_before_amount=True))
    main_logger.info("JPY, 0 десяткових знаків (символ перед): %s", format_currency(amount3, 'JPY', decimal_places=0, symbol_before_amount=True))
    main_logger.info("Від'ємна сума EUR (символ перед): %s", format_currency(amount_neg, 'EUR', symbol_before_amount=True))
    main_logger.info("Сума None для валюти: %s", format_currency(None))
    main_logger.info("Недійсна сума (наприклад, рядок 'abc'): %s", format_currency('abc')) # Повинно повернути 'abc'

    amount_float_precision = 0.1 + 0.2 # Сума з відомою проблемою точності float
    main_logger.info(
        "Тест точності float (0.1 + 0.2 = %s): %s",
        amount_float_precision,
        format_currency(amount_float_precision, 'USD', decimal_places=18, symbol_before_amount=True)
    )
    # Очікуваний результат для 0.1 + 0.2 при конвертації в Decimal(str(0.30000000000000004))
    # буде $0.300000000000000040, що демонструє правильну обробку Decimal.
