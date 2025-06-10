# backend/scripts/run_linters.py
import subprocess
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

# Директорії та файли для перевірки/форматування
TARGET_PATHS = ["app", "tests", "scripts"]

def run_command(command: list, check_mode: bool, tool_name: str) -> bool:
    """
    Запускає команду лінтера/форматера і обробляє результат.
    Повертає True, якщо команда успішна (або в режимі --check нічого не змінила), інакше False.
    """
    action_desc = "Перевірка" if check_mode else "Форматування/виправлення"
    logger.info(f"{action_desc} за допомогою {tool_name} для шляхів: {', '.join(TARGET_PATHS)}")

    full_command = command + TARGET_PATHS
    logger.debug(f"Повна команда: {' '.join(full_command)}")

    try:
        # Запускаємо команду з кореня проекту
        result = subprocess.run(full_command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

        if result.stdout:
            logger.info(f"Вивід {tool_name}:\n{result.stdout}")
        if result.stderr:
            # Ruff часто виводить інформацію про кількість знайдених проблем в stderr, навіть якщо виправляє
            # Тому логуємо як INFO, якщо код повернення 0 (або 1 в --check для Ruff, якщо є що міняти)
            if result.returncode == 0 or (tool_name == "Ruff" and check_mode and result.returncode == 1):
                 logger.info(f"Інформаційний вивід {tool_name} (stderr):\n{result.stderr}")
            else:
                logger.error(f"Помилки {tool_name} (stderr):\n{result.stderr}")

        if tool_name == "Black" and check_mode:
            if result.returncode == 0:
                logger.info(f"Black: Файли вже відформатовані.")
                return True
            elif result.returncode == 1: # Black повертає 1, якщо файли потребують форматування в режимі --check
                logger.error(f"Black: Файли потребують форматування.")
                return False
            else: # Інші помилки
                logger.error(f"Black: Помилка виконання (код: {result.returncode}).")
                return False
        elif tool_name == "Ruff" and command[1] == "check" and check_mode: # Ruff check --check
             if result.returncode == 0:
                logger.info(f"Ruff check: Проблем не знайдено.")
                return True
             elif result.returncode == 1: # Ruff check повертає 1, якщо знайдені проблеми, які можна виправити або ні
                logger.error(f"Ruff check: Знайдено проблеми.")
                return False # Вважаємо це помилкою для CI
             else:
                logger.error(f"Ruff check: Помилка виконання (код: {result.returncode}).")
                return False
        elif tool_name == "Ruff" and command[1] == "format" and check_mode: # Ruff format --check
            if result.returncode == 0:
                logger.info(f"Ruff format: Файли вже відформатовані.")
                return True
            elif result.returncode == 1: # Ruff format --check повертає 1, якщо файли потребують форматування
                logger.error(f"Ruff format: Файли потребують форматування.")
                return False
            else:
                logger.error(f"Ruff format: Помилка виконання (код: {result.returncode}).")
                return False
        elif not check_mode: # Режим застосування змін
            if result.returncode == 0:
                logger.info(f"{tool_name}: Успішно застосовано.")
                return True
            else:
                logger.error(f"{tool_name}: Помилка виконання при застосуванні змін (код: {result.returncode}).")
                return False

        # Для інших випадків (наприклад, ruff check без --check, що не є типовим для цього скрипта)
        if result.returncode != 0:
            logger.error(f"{tool_name} завершився з кодом помилки: {result.returncode}")
            return False
        return True

    except FileNotFoundError:
        logger.error(f"Помилка: {tool_name} не знайдено. Переконайтеся, що він встановлений та доступний в PATH.")
        return False
    except Exception as e:
        logger.error(f"Неочікувана помилка під час запуску {tool_name}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Скрипт для запуску лінтерів Black та Ruff.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Запустити лінтери в режимі перевірки (без внесення змін). Використовується для CI."
    )
    parser.add_argument(
        "--skip-black",
        action="store_true",
        help="Пропустити запуск Black."
    )
    parser.add_argument(
        "--skip-ruff-format",
        action="store_true",
        help="Пропустити запуск Ruff format."
    )
    parser.add_argument(
        "--skip-ruff-check",
        action="store_true",
        help="Пропустити запуск Ruff check."
    )

    args = parser.parse_args()

    logger.info(f"Зміна поточної робочої директорії на: {PROJECT_ROOT}")
    os.chdir(PROJECT_ROOT)
    logger.info(f"Поточна робоча директорія: {os.getcwd()}")

    all_successful = True

    # Запуск Black
    if not args.skip_black:
        black_command = ["black"]
        if args.check:
            black_command.append("--check")
            black_command.append("--diff") # Показати різницю в режимі перевірки
        if not run_command(black_command, args.check, "Black"):
            all_successful = False
    else:
        logger.info("Пропуск Black.")

    # Запуск Ruff Format
    if not args.skip_ruff_format:
        ruff_format_command = ["ruff", "format"]
        if args.check:
            ruff_format_command.append("--check")
            ruff_format_command.append("--diff")
        if not run_command(ruff_format_command, args.check, "Ruff format"):
            all_successful = False
    else:
        logger.info("Пропуск Ruff format.")

    # Запуск Ruff Check (Lint)
    if not args.skip_ruff_check:
        ruff_check_command = ["ruff", "check"]
        if not args.check: # Якщо не --check, то автоматично виправляємо (--fix)
            ruff_check_command.append("--fix")
            ruff_check_command.append("--show-fixes") # Показувати, що було виправлено
        # У режимі --check, ruff check сам по собі є перевіркою, --fix не потрібен.
        # Для CI важливо, щоб ruff check --check повертав помилку, якщо є проблеми.
        if not run_command(ruff_check_command, args.check, "Ruff check"):
            all_successful = False
    else:
        logger.info("Пропуск Ruff check.")


    if all_successful:
        logger.info("Всі лінтери успішно відпрацювали" + (" в режимі перевірки." if args.check else "."))
        sys.exit(0)
    else:
        logger.error("Один або більше лінтерів виявили проблеми" + (" або потребують змін." if args.check else " або не змогли їх застосувати."))
        sys.exit(1)

if __name__ == "__main__":
    # Приклади запуску:
    # python backend/scripts/run_linters.py (форматує та виправляє)
    # python backend/scripts/run_linters.py --check (тільки перевіряє)
    main()
