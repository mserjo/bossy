# backend/scripts/run_tests.py
import pytest
import sys
import os
import logging
import argparse

# Налаштування базового логування для скрипта
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Визначаємо корінь проекту (директорію 'backend')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) # 'backend/'

def main():
    """
    Головна функція для запуску тестів Pytest.
    Дозволяє передавати додаткові аргументи до Pytest.
    Запускається з кореневої директорії проекту ('backend/').
    """
    parser = argparse.ArgumentParser(
        description="Скрипт для запуску тестів Pytest з кореневої директорії проекту.",
        # Дозволяє передавати невідомі аргументи далі до pytest
        # Однак, краще явно збирати їх і передавати.
        # Якщо використовувати REMAINDER, то всі аргументи після -- будуть зібрані.
        # Для простоти, ми зберемо всі невідомі аргументи.
        # prefix_chars='-' # Стандартний префікс
    )
    # Додаємо відомий аргумент, якщо потрібно (наприклад, шлях до тестів)
    # parser.add_argument(
    #     "--path",
    #     type=str,
    #     default="app/tests", # Припускаємо, що тести знаходяться тут
    #     help="Шлях до директорії з тестами або конкретного файлу/директорії тестів."
    # )

    # Збираємо відомі та невідомі аргументи. Невідомі будуть передані в pytest.
    args, unknown_args = parser.parse_known_args()

    logger.info(f"Зміна поточної робочої директорії на: {PROJECT_ROOT}")
    os.chdir(PROJECT_ROOT)
    logger.info(f"Поточна робоча директорія: {os.getcwd()}")

    # Формуємо список аргументів для pytest
    pytest_args = []
    # Якщо б у нас був аргумент --path:
    # pytest_args.append(args.path)

    # Додаємо всі нерозпізнані аргументи до списку аргументів pytest
    if unknown_args:
        logger.info(f"Передача наступних аргументів до Pytest: {unknown_args}")
        pytest_args.extend(unknown_args)
    else:
        logger.info("Запуск Pytest зі стандартними налаштуваннями (без додаткових аргументів).")
        # Можна додати стандартний шлях до тестів, якщо не передано жодних аргументів
        # pytest_args.append("app/tests") # Або залишити порожнім, щоб pytest сам шукав

    logger.info(f"Запуск Pytest з аргументами: {pytest_args}")

    # Запуск Pytest
    # pytest.main() повертає код виходу
    exit_code = pytest.main(pytest_args)

    if exit_code == 0:
        logger.info("Всі тести успішно пройшли.")
    elif exit_code == 1:
        logger.error("Один або більше тестів не пройшли.")
    elif exit_code == 2:
        logger.error("Запуск тестів було перервано користувачем.")
    elif exit_code == 3:
        logger.error("Внутрішня помилка під час виконання тестів.")
    elif exit_code == 4:
        logger.error("Помилка використання Pytest (неправильні опції).")
    elif exit_code == 5:
        logger.warning("Тести не знайдено.")
    else:
        logger.warning(f"Pytest завершився з невідомим кодом виходу: {exit_code}")

    # Повертаємо код виходу Pytest, щоб його можна було використовувати в CI/CD
    sys.exit(exit_code)

if __name__ == "__main__":
    # Приклади запуску:
    # python backend/scripts/run_tests.py
    # python backend/scripts/run_tests.py -v -s app/tests/auth/
    # python backend/scripts/run_tests.py app/tests/auth/test_login.py::test_user_login
    # python backend/scripts/run_tests.py -k "login" --cov=app
    main()
