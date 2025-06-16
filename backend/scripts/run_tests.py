# backend/scripts/run_tests.py
# -*- coding: utf-8 -*-
"""
Скрипт для запуску тестів Pytest.

Цей скрипт є обгорткою для запуску `pytest`. Він дозволяє передавати
додаткові аргументи командного рядка безпосередньо до `pytest`.
Скрипт встановлює кореневу директорію проекту перед запуском тестів
для коректного виявлення тестів та конфігурації.
"""
import sys
import os
import logging  # Стандартний модуль логування
import argparse

# --- Налаштування шляхів ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)  # Директорія 'backend/'
# Корінь проекту, де знаходиться pyproject.toml, зазвичай на один рівень вище 'backend'
PROJECT_ROOT_FOR_CONFIG = os.path.dirname(BACKEND_DIR)

# --- Налаштування логування ---
try:
    from backend.app.src.config.logging import logger

    logger.info("Використовується логер додатку для скрипта run_tests.")  # i18n
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.info("Логер додатку не знайдено, використовується базовий логер для run_tests.")  # i18n

# --- Імпорт Pytest ---
try:
    import pytest
except ImportError:
    logger.error("Pytest не встановлено. Будь ласка, встановіть його: pip install pytest")  # i18n
    sys.exit(1)


# Базова функція-заглушка для інтернаціоналізації рядків
def _(text: str) -> str:
    return text


# Директорія з тестами відносно PROJECT_ROOT_FOR_CONFIG
DEFAULT_TEST_PATH = os.path.join("backend", "tests")


def main():
    """
    Головна функція для запуску тестів Pytest.
    Збирає всі невідомі аргументи командного рядка та передає їх до `pytest.main()`.
    Запускається з кореневої директорії проекту.
    """
    # i18n: Argparse description for the script
    parser = argparse.ArgumentParser(
        description=_("Скрипт для запуску тестів Pytest. Всі нерозпізнані аргументи передаються до pytest."),
        epilog=_("Приклад: python backend/scripts/run_tests.py -v -s backend/tests/auth/ --cov=backend/app")  # i18n
    )
    # Використовуємо parse_known_args(), щоб зібрати всі аргументи, які не визначені для цього парсера,
    # і передати їх до pytest.
    args, pytest_run_args = parser.parse_known_args()

    # Встановлюємо кореневу директорію проекту як поточну робочу директорію.
    # Це важливо для pytest, щоб він правильно знаходив конфігураційні файли (pyproject.toml, pytest.ini)
    # та тести, особливо якщо використовуються відносні шляхи в конфігурації.
    logger.info(_("Зміна поточної робочої директорії на: {path}").format(path=PROJECT_ROOT_FOR_CONFIG))  # i18n
    os.chdir(PROJECT_ROOT_FOR_CONFIG)
    logger.info(_("Поточна робоча директорія: {cwd}").format(cwd=os.getcwd()))  # i18n

    # Якщо користувач не передав жодних аргументів (наприклад, шляхів до тестів або опцій),
    # можна додати шлях до тестів за замовчуванням.
    if not pytest_run_args:
        logger.info(
            _("Жодних аргументів не передано до pytest, буде використано шлях за замовчуванням: '{path}'").format(
                path=DEFAULT_TEST_PATH))  # i18n
        pytest_run_args.append(DEFAULT_TEST_PATH)
    else:
        logger.info(_("Передача наступних аргументів до Pytest: {args}").format(args=pytest_run_args))  # i18n

    logger.info(_("Запуск Pytest..."))  # i18n

    # Запуск Pytest. pytest.main() повертає код виходу.
    # Він також може викликати sys.exit() сам, залежно від конфігурації.
    try:
        exit_code = pytest.main(pytest_run_args)
    except Exception as e:
        logger.error(_("Виникла помилка під час виклику pytest.main(): {error}").format(error=e), exc_info=True)  # i18n
        sys.exit(1)  # Завершуємо з помилкою

    # Інтерпретація кодів виходу pytest
    # (https://docs.pytest.org/en/stable/reference/exit-codes.html)
    if exit_code == 0:
        logger.info(_("Всі тести успішно пройшли."))  # i18n
    elif exit_code == 1:
        logger.error(_("Один або більше тестів не пройшли."))  # i18n
    elif exit_code == 2:
        # i18n: Error message - Test execution interrupted
        logger.error(_("Виконання тестів було перервано користувачем (наприклад, Ctrl+C)."))
    elif exit_code == 3:
        # i18n: Error message - Internal error during test execution
        logger.error(_("Внутрішня помилка під час виконання тестів Pytest."))
    elif exit_code == 4:
        # i18n: Error message - Pytest usage error
        logger.error(_("Помилка використання Pytest (наприклад, неправильні опції командного рядка)."))
    elif exit_code == 5:
        # i18n: Warning message - No tests found
        logger.warning(_("Тести не знайдено за вказаними шляхами/опціями."))
    else:
        # i18n: Warning message - Pytest finished with unknown exit code
        logger.warning(_("Pytest завершився з невідомим кодом виходу: {code}").format(code=exit_code))

    # Повертаємо код виходу Pytest, щоб його можна було використовувати в CI/CD системах
    sys.exit(exit_code)


if __name__ == "__main__":
    # Приклади запуску (з кореневої директорії проекту):
    # # Запустити всі тести в директорії backend/tests (за замовчуванням)
    # python backend/scripts/run_tests.py
    #
    # # Запустити тести з детальним виводом (-v) та показом stdout (-s) для конкретної директорії
    # python backend/scripts/run_tests.py -v -s backend/tests/auth/
    #
    # # Запустити конкретний тест у файлі
    # python backend/scripts/run_tests.py backend/tests/auth/test_login.py::test_user_login
    #
    # # Запустити тести, що містять "login" у назві, та зібрати покриття для backend/app
    # python backend/scripts/run_tests.py -k "login" --cov=backend/app
    #
    # Переконайтеся, що pytest встановлено та налаштовано (наприклад, через pyproject.toml).
    main()
