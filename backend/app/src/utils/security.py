# backend/app/src/utils/security.py
# -*- coding: utf-8 -*-
"""
Модуль утиліт, пов'язаних з безпекою.

Цей модуль містить функції, що допомагають у реалізації аспектів безпеки додатку,
наприклад, генерація криптографічно стійких випадкових рядків для токенів,
ключів API або інших потреб, де важлива випадковість та непередбачуваність.
"""
import logging
import secrets
import string

# Configure logger for this module
logger = logging.getLogger(__name__)

def generate_secure_random_string(length: int = 32) -> str:
    """
    Генерує криптографічно безпечний, URL-безпечний випадковий рядок.

    Args:
        length: Бажана довжина випадкового рядка. За замовчуванням 32.

    Returns:
        Безпечно згенерований випадковий рядок.
    Raises:
        ValueError: якщо довжина не є додатним цілим числом.
    """
    if not isinstance(length, int) or length <= 0:
        logger.error(f"Вказано недійсну довжину для генерації випадкового рядка: {length}. Довжина повинна бути додатним цілим числом.")
        raise ValueError("Довжина повинна бути додатним цілим числом.")

    # Використовуємо літери (великі та малі) та цифри.
    # Можна розширити, якщо потрібні інші символи, але це хороший набір для URL-безпечних токенів.
    alphabet = string.ascii_letters + string.digits

    secure_string = ''.join(secrets.choice(alphabet) for _ in range(length))
    logger.debug(f"Згенеровано безпечний випадковий рядок довжиною {length}.")
    return secure_string

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Демонстрація Утиліт Безпеки ---")

    try:
        token16 = generate_secure_random_string(16)
        logger.info(f"Згенеровано 16-символьний токен: '{token16}' (довжина: {len(token16)})")
        assert len(token16) == 16

        token32 = generate_secure_random_string() # За замовчуванням 32
        logger.info(f"Згенеровано 32-символьний токен: '{token32}' (довжина: {len(token32)})")
        assert len(token32) == 32

        token64 = generate_secure_random_string(64)
        logger.info(f"Згенеровано 64-символьний токен: '{token64}' (довжина: {len(token64)})")
        assert len(token64) == 64

        another_token32 = generate_secure_random_string()
        logger.info(f"Інший 32-символьний токен: '{another_token32}'")
        assert token32 != another_token32 # Перевірка, що токени різні

        try:
            generate_secure_random_string(0)
        except ValueError as e:
            logger.info(f"Перехоплено очікувану помилку для довжини 0: {e}")

        try:
            generate_secure_random_string(-5)
        except ValueError as e:
            logger.info(f"Перехоплено очікувану помилку для від'ємної довжини: {e}")

    except Exception as e:
        logger.error(f"Під час демонстрації утиліт безпеки сталася неочікувана помилка: {e}", exc_info=True)
