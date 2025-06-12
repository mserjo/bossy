# backend/app/src/utils/security.py
# -*- coding: utf-8 -*-
"""Модуль утиліт, пов'язаних з безпекою.

Цей модуль містить функції, що допомагають у реалізації аспектів безпеки додатку.
Наприклад, тут може бути генерація криптографічно стійких випадкових рядків
для токенів доступу, ключів API, кодів підтвердження або інших потреб,
де важлива висока випадковість та непередбачуваність генерованих значень.
"""
import logging  # Для локального використання в __main__
import secrets
import string

# Імпорт централізованого логера проекту
from backend.app.src.config.logging_config import setup_logging # type: ignore
logger = setup_logging()


def generate_secure_random_string(length: int = 32) -> str:
    """Генерує криптографічно безпечний, URL-безпечний випадковий рядок.

    Використовує модуль `secrets`, який призначений для генерації
    криптографічно стійких випадкових чисел, придатних для управління
    даними, такими як паролі, токени безпеки тощо.

    Args:
        length: Бажана довжина випадкового рядка. За замовчуванням 32 символи.

    Returns:
        Безпечно згенерований випадковий рядок, що складається з ASCII літер
        (великих та малих) та цифр.

    Raises:
        ValueError: Якщо вказана `length` не є додатним цілим числом.
    """
    if not isinstance(length, int) or length <= 0:
        logger.error(
            "Вказано недійсну довжину (%s) для генерації випадкового рядка. Довжина повинна бути додатним цілим числом.",
            length
        )
        raise ValueError("Довжина випадкового рядка повинна бути додатним цілим числом.")

    # Використовуємо комбінацію ASCII літер (великих та малих) та цифр.
    # Цей набір символів зазвичай є URL-безпечним.
    alphabet = string.ascii_letters + string.digits

    # Генеруємо рядок, вибираючи випадкові символи з алфавіту
    secure_string = "".join(secrets.choice(alphabet) for _ in range(length))
    logger.debug("Згенеровано безпечний випадковий рядок довжиною %d.", length)
    return secure_string


if __name__ == "__main__":
    # Налаштування базового логування для демонстрації, якщо ще не налаштовано.
    if not logging.getLogger().hasHandlers(): # Перевіряємо, чи є вже обробники у кореневого логера
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    # Використовуємо логер модуля для повідомлень в __main__
    main_logger = logging.getLogger(__name__) # Отримуємо логер для __main__ контексту
    main_logger.info("--- Демонстрація Утиліт Безпеки ---")

    try:
        token16 = generate_secure_random_string(16)
        main_logger.info("Згенеровано 16-символьний токен: '%s' (довжина: %d)", token16, len(token16))
        assert len(token16) == 16, "Довжина 16-символьного токена не відповідає очікуваній."

        token32 = generate_secure_random_string() # Використовує довжину за замовчуванням (32)
        main_logger.info("Згенеровано 32-символьний токен: '%s' (довжина: %d)", token32, len(token32))
        assert len(token32) == 32, "Довжина 32-символьного токена не відповідає очікуваній."

        token64 = generate_secure_random_string(64)
        main_logger.info("Згенеровано 64-символьний токен: '%s' (довжина: %d)", token64, len(token64))
        assert len(token64) == 64, "Довжина 64-символьного токена не відповідає очікуваній."

        # Перевірка унікальності (ймовірність колізії надзвичайно мала)
        another_token32 = generate_secure_random_string()
        main_logger.info("Інший 32-символьний токен: '%s'", another_token32)
        assert token32 != another_token32, "Два послідовно згенеровані токени не повинні співпадати."

        # Тестування недійсних значень довжини
        try:
            generate_secure_random_string(0)
            assert False, "Виклик generate_secure_random_string з довжиною 0 мав спричинити ValueError."
        except ValueError as e:
            main_logger.info("Перехоплено очікувану помилку для довжини 0: %s", e)

        try:
            generate_secure_random_string(-5)
            assert False, "Виклик generate_secure_random_string з від'ємною довжиною мав спричинити ValueError."
        except ValueError as e:
            main_logger.info("Перехоплено очікувану помилку для від'ємної довжини: %s", e)

        main_logger.info("Демонстрація генерації безпечних рядків пройшла успішно.")

    except Exception as e: # pylint: disable=broad-except
        main_logger.error(
            "Під час демонстрації утиліт безпеки сталася неочікувана помилка: %s",
            e,
            exc_info=True
        )
