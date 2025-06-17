# backend/app/src/utils/hash.py
# -*- coding: utf-8 -*-
"""Модуль для хешування та перевірки паролів.

Цей модуль надає утиліти для безпечного хешування паролів користувачів
та перевірки наданих паролів відносно збережених хешів.
Використовує бібліотеку `passlib` з рекомендованою схемою `bcrypt`
для забезпечення надійного та сучасного захисту паролів.
"""
import logging  # Для локального використання в __main__
from passlib.context import CryptContext
from passlib.exc import UnknownHashError, MalformedHashError

from backend.app.src.config.logging_config import setup_logging
logger = setup_logging()

# Налаштування контексту passlib.
# Використовуємо bcrypt як основну схему хешування.
# `deprecated="auto"` дозволяє автоматично оновлювати хеші, якщо вони
# були створені за допомогою застарілої схеми, під час успішної перевірки пароля.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Хешує текстовий пароль за допомогою налаштованого CryptContext.

    Args:
        password: Текстовий пароль для хешування.

    Returns:
        Рядок, що містить хешований пароль.

    Raises:
        ValueError: Якщо під час хешування виникає помилка.
    """
    if not password:
        logger.error("Спроба хешувати порожній пароль.")
        raise ValueError("Пароль не може бути порожнім для хешування.")
    try:
        hashed_password = pwd_context.hash(password)
        logger.debug("Пароль успішно хешовано (довжина хешу: %d).", len(hashed_password))
        return hashed_password
    except Exception as e: # pylint: disable=broad-except
        logger.error("Помилка під час хешування пароля: %s", e, exc_info=True)
        # Не передаємо деталі помилки passlib назовні, щоб уникнути витоку інформації.
        raise ValueError("Хешування пароля не вдалося з невідомої причини.")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Перевіряє текстовий пароль відносно збереженого хешованого пароля.

    Також автоматично оновлює хеш, якщо він використовує застарілу схему,
    визначену в `pwd_context`.

    Args:
        plain_password: Текстовий пароль, наданий користувачем для перевірки.
        hashed_password: Збережений хешований пароль для порівняння.

    Returns:
        `True`, якщо наданий текстовий пароль відповідає збереженому хешу,
        `False` в іншому випадку (неправильний пароль, помилка формату хешу тощо).
    """
    if not plain_password or not hashed_password:
        logger.warning(
            "Спроба перевірити пароль з порожнім текстовим паролем або порожнім хешованим паролем."
        )
        return False
    try:
        is_verified, new_hash = pwd_context.verify_and_update(plain_password, hashed_password)
        if new_hash:
            # Цей лог важливий, оскільки passlib може оновити хеш,
            # якщо використовується застаріла схема.
            # У реальному додатку тут може бути логіка для оновлення хешу в базі даних.
            logger.info(
                "Пароль перевірено, і хеш було оновлено до новішої схеми "
                "(довжина старого хешу: %d, нового: %d). "
                "Рекомендується оновити збережений хеш у базі даних.",
                len(hashed_password), len(new_hash)
            )
            # Примітка: оновлення хешу в БД тут не відбувається, це має робити викликаючий код.

        if is_verified:
            logger.debug("Перевірка пароля успішна.")
        else:
            # Не логуємо сам пароль, лише факт невдалої перевірки.
            logger.debug("Перевірка пароля не вдалася (наданий пароль не відповідає хешу).")
        return is_verified
    except (UnknownHashError, MalformedHashError) as e:
        logger.warning(
            "Помилка під час перевірки пароля: надано невірний формат хешу. Помилка: %s", e
        )
        return False
    except Exception as e: # pylint: disable=broad-except
        logger.error("Неочікувана помилка під час перевірки пароля: %s", e, exc_info=True)
        return False


if __name__ == "__main__":
    # Налаштування базового логування для демонстрації, якщо ще не налаштовано.
    if not logging.getLogger().hasHandlers(): # Перевіряємо, чи є вже обробники у кореневого логера
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    # Використовуємо логер модуля для повідомлень в __main__
    main_logger = logging.getLogger(__name__) # Отримуємо логер для __main__ контексту
    main_logger.info("--- Демонстрація Утиліт Хешування Паролів ---")

    test_password = "МійБезпечнийПароль123!"
    main_logger.info("Текстовий пароль: '%s'", test_password)

    try:
        hashed_pw = get_password_hash(test_password)
        main_logger.info("Хешований пароль: '%s' (довжина: %d)", hashed_pw, len(hashed_pw))

        is_correct = verify_password(test_password, hashed_pw)
        main_logger.info("Перевірка з правильним паролем ('%s'): %s", test_password, is_correct)
        assert is_correct, "Перевірка правильного пароля не вдалася."

        incorrect_password = "НеправильнийПароль!"
        is_incorrect = verify_password(incorrect_password, hashed_pw)
        main_logger.info("Перевірка з неправильним паролем ('%s'): %s", incorrect_password, is_incorrect)
        assert not is_incorrect, "Перевірка неправильного пароля помилково пройшла."

        # Тест з порожнім текстовим паролем
        empty_plain_result = verify_password("", hashed_pw)
        main_logger.info("Перевірка з порожнім текстовим паролем: %s", empty_plain_result)
        assert not empty_plain_result, "Перевірка порожнього текстового пароля помилково пройшла."

        # Тест з порожнім хешованим паролем
        empty_hashed_result = verify_password(test_password, "")
        main_logger.info("Перевірка з порожнім хешованим паролем: %s", empty_hashed_result)
        assert not empty_hashed_result, "Перевірка порожнього хешованого пароля помилково пройшла."

        # Тест хешування порожнього пароля
        try:
            get_password_hash("")
            assert False, "Хешування порожнього пароля мало спричинити ValueError."
        except ValueError as ve_empty:
            main_logger.info("Перехоплено очікувану помилку для хешування порожнього пароля: %s", ve_empty)


    except ValueError as ve:
        main_logger.error("Під час демонстрації хешування виникла помилка ValueError: %s", ve)
    except Exception as e: # pylint: disable=broad-except
        main_logger.error("Під час демонстрації хешування виникла неочікувана помилка: %s", e, exc_info=True)
