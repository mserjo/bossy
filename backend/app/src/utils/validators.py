# backend/app/src/utils/validators.py
# -*- coding: utf-8 -*-
"""
Модуль кастомних функцій валідації даних.

Цей модуль надає функції для перевірки даних на відповідність певним критеріям
або форматам. Ці валідатори можуть використовуватися в моделях Pydantic,
сервісному шарі або інших частинах додатку, де потрібна специфічна
перевірка даних перед їх обробкою або збереженням.
"""
import logging
import re
from typing import Optional # Added Optional for region type hint

# Configure logger for this module
logger = logging.getLogger(__name__)

def is_strong_password(password: str, min_length: int = 8) -> bool:
    """
    Перевіряє, чи відповідає пароль загальним критеріям надійності.
    Критерії:
        - Мінімальна довжина (за замовчуванням 8 символів).
        - Містить принаймні одну велику літеру.
        - Містить принаймні одну малу літеру.
        - Містить принаймні одну цифру.
        - Містить принаймні один спеціальний символ (із попередньо визначеного набору).

    Args:
        password: Рядок пароля для перевірки.
        min_length: Мінімальна необхідна довжина пароля.

    Returns:
        True, якщо пароль відповідає всім критеріям, False в іншому випадку.
    """
    if not password:
        return False
    if len(password) < min_length:
        logger.debug(f"Перевірка пароля не вдалася: Занадто короткий (довжина {len(password)}, вимагається {min_length}).")
        return False
    if not re.search(r"[A-Z]", password):
        logger.debug("Перевірка пароля не вдалася: Немає великої літери.")
        return False
    if not re.search(r"[a-z]", password):
        logger.debug("Перевірка пароля не вдалася: Немає малої літери.")
        return False
    if not re.search(r"[0-9]", password):
        logger.debug("Перевірка пароля не вдалася: Немає цифри.")
        return False
    if not re.search(r"[!@#$%^&*()_+=\-\[\]{};':\"\\|,.<>\/?~`]", password): # Екрановано зворотний слеш
        logger.debug("Перевірка пароля не вдалася: Немає спеціального символу.")
        return False

    logger.debug("Перевірка пароля успішна: Відповідає всім критеріям.")
    return True

def is_valid_phone_number(phone_number: str, region: Optional[str] = None) -> bool:
    """
    Перевіряє номер телефону.
    Це базова реалізація-заглушка.
    Для надійної валідації розгляньте можливість використання спеціалізованої бібліотеки, наприклад 'phonenumbers'.

    Args:
        phone_number: Рядок номера телефону для перевірки.
        region: Необов'язково. Код регіону (наприклад, "UA", "GB") для більш конкретної валідації
                при використанні бібліотеки. У цій базовій версії не використовується.

    Returns:
        True, якщо формат номера телефону виглядає дійсним, False в іншому випадку.
    """
    if not phone_number:
        return False

    # Підрахунок лише цифр
    num_digits = sum(c.isdigit() for c in phone_number)
    if not (7 <= num_digits <= 15): # Дуже загальне правило, реальні номери можуть варіюватися
        logger.debug(f"Перевірка номера телефону не вдалася: Містить {num_digits} цифр, очікується 7-15.")
        return False

    # Дозволені символи: цифри, пробіли, дефіси, круглі дужки, плюс
    allowed_chars_pattern = re.compile(r"^[0-9\s\-\(\)\+]*$")
    if not allowed_chars_pattern.match(phone_number):
        logger.debug("Перевірка номера телефону не вдалася: Містить недійсні символи.")
        return False

    # Прості перевірки початку та кінця
    if not (phone_number.startswith('+') or phone_number[0].isdigit()):
         logger.debug("Перевірка номера телефону не вдалася: Не починається з '+' або цифри.")
         return False
    if not phone_number[-1].isdigit(): # Має закінчуватися цифрою після видалення можливих пробілів або спецсимволів, але тут перевіряємо як є
         logger.debug("Перевірка номера телефону не вдалася: Не закінчується цифрою.")
         return False

    logger.debug(f"Номер телефону '{phone_number}' пройшов базову перевірку формату.")
    return True

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Демонстрація Утиліт Валідації ---")

    logger.info("\n--- Тести Надійності Пароля ---")
    passwords_to_test = {
        "Короткий1!": False,
        "безвеликої1!": False,
        "БЕЗМАЛОЇ1!": False,
        "БезЦифри!Аа": False,
        "БезСпецСимволу1Аа": False,
        "ВаліднийПароль123!": True,
        "Інший_Хороший-Пароль_123": True,
        "Слабкий": False
    }
    for pw, expected in passwords_to_test.items():
        is_valid = is_strong_password(pw)
        logger.info(f"Пароль '{pw}': Надійний? {is_valid} (Очікується: {expected})")
        assert is_valid == expected

    logger.info("\n--- Базові Тести Валідації Номера Телефону ---")
    phones_to_test = {
        "+380501234567": True,
        "050-123-45-67": True,
        "(097) 123 4567": True,
        "1234567": True,  # Мінімальна кількість цифр
        "12345": False, # Занадто мало цифр
        "1234567890123456": False, # Занадто багато цифр
        "0441234567": True, # Київський міський
        "050-123-АБВГ": False, # Недійсні символи
        "+1-555-123-4567 ext 9": False, # Непідтримувані розширення в базовій версії
        "невірний номер": False,
        "": False,
        "+": False,
        "123-": False
    }
    for phone, expected in phones_to_test.items():
        is_valid = is_valid_phone_number(phone)
        logger.info(f"Телефон '{phone}': Дійсний? {is_valid} (Очікується: {expected})")
        assert is_valid == expected

    logger.info("Примітка: Перевірка номера телефону є дуже базовою. Використовуйте спеціалізовану бібліотеку для продуктивного середовища.")
