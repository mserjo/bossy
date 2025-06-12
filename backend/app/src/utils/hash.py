# backend/app/src/utils/hash.py
# -*- coding: utf-8 -*-
"""
Модуль для хешування та перевірки паролів.

Цей модуль надає утиліти для безпечного хешування паролів користувачів
та перевірки наданих паролів відносно збережених хешів.
Використовує бібліотеку `passlib` з рекомендованою схемою `bcrypt`.
"""
import logging
from passlib.context import CryptContext

# Configure logger for this module
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """
    Хешує текстовий пароль за допомогою налаштованого CryptContext.

    Args:
        password: Текстовий пароль для хешування.

    Returns:
        Рядок хешованого пароля.
    """
    try:
        hashed_password = pwd_context.hash(password)
        logger.debug(f"Пароль успішно хешовано (довжина хешу: {len(hashed_password)}).")
        return hashed_password
    except Exception as e:
        logger.error(f"Помилка під час хешування пароля: {e}", exc_info=True)
        raise ValueError("Хешування пароля не вдалося.")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Перевіряє текстовий пароль відносно збереженого хешованого пароля.

    Args:
        plain_password: Текстовий пароль для перевірки.
        hashed_password: Збережений хешований пароль для порівняння.

    Returns:
        True, якщо пароль відповідає хешу, False в іншому випадку.
    """
    if not plain_password or not hashed_password:
        logger.warning("Спроба перевірити пароль з порожнім текстовим паролем або хешованим паролем.")
        return False
    try:
        is_verified, new_hash = pwd_context.verify_and_update(plain_password, hashed_password)
        if new_hash:
            # Цей лог важливий, оскільки passlib може оновити хеш, якщо використовується застаріла схема
            logger.info(f"Пароль перевірено, хеш оновлено (довжина старого хешу: {len(hashed_password)}, нового: {len(new_hash)}). Рекомендується оновити збережений хеш.")

        if is_verified:
            logger.debug("Перевірка пароля успішна.")
        else:
            logger.debug("Перевірка пароля не вдалася (паролі не співпадають).")
        return is_verified
    except Exception as e: # Наприклад, passlib.exc.UnknownHashError
        logger.error(f"Помилка під час перевірки пароля: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Демонстрація Утиліт Хешування Паролів ---")

    test_password = "МійБезпечнийПароль123!"
    logger.info(f"Текстовий пароль: '{test_password}'")

    try:
        hashed_pw = get_password_hash(test_password)
        logger.info(f"Хешований пароль: '{hashed_pw}' (довжина: {len(hashed_pw)})")

        is_correct = verify_password(test_password, hashed_pw)
        logger.info(f"Перевірка з правильним паролем ('{test_password}'): {is_correct}")
        assert is_correct

        incorrect_password = "НеправильнийПароль!"
        is_incorrect = verify_password(incorrect_password, hashed_pw)
        logger.info(f"Перевірка з неправильним паролем ('{incorrect_password}'): {is_incorrect}")
        assert not is_incorrect

        empty_plain_result = verify_password("", hashed_pw)
        logger.info(f"Перевірка з порожнім текстовим паролем: {empty_plain_result}")
        assert not empty_plain_result

        empty_hashed_result = verify_password(test_password, "")
        logger.info(f"Перевірка з порожнім хешованим паролем: {empty_hashed_result}")
        assert not empty_hashed_result

    except ValueError as ve:
        logger.error(f"Під час демонстрації хешування виникла помилка ValueError: {ve}")
    except Exception as e:
        logger.error(f"Під час демонстрації хешування виникла неочікувана помилка: {e}", exc_info=True)
