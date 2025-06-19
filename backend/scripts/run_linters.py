# backend/scripts/run_linters.py
# -*- coding: utf-8 -*-
"""
Скрипт для запуску лінтерів та форматерів коду.

Підтримує запуск Black для форматування коду та Ruff для форматування і лінтингу.
Має опцію `--check` для запуску в режимі перевірки (без внесення змін),
що корисно для інтеграції з CI/CD системами.
Також дозволяє пропускати окремі інструменти за допомогою опцій --skip-*.
"""
import subprocess
import sys
import os
import logging  # Стандартний модуль логування
import argparse
from typing import List  # Для типізації

# --- Налаштування шляхів ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)  # Директорія 'backend/'
# Корінь проекту, де знаходиться pyproject.toml, зазвичай на один рівень вище 'backend'
PROJECT_ROOT_FOR_CONFIG = os.path.dirname(BACKEND_DIR)

# --- Налаштування логування ---
# Намагаємося імпортувати логер додатку.
try:
    from backend.app.src.config.logging import get_logger # Змінено імпорт
    logger = get_logger(__name__) # Отримуємо логер для цього скрипта
    logger.info("Використовується логер додатку для скрипта run_linters.")  # i18n
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.info("Логер додатку не знайдено (ImportError), використовується базовий логер для run_linters.")  # i18n

# --- Конфігурація ---
# Директорії та файли для перевірки/форматування відносно PROJECT_ROOT_FOR_CONFIG
# Зазвичай, це директорії з кодом додатка, тестами та самими скриптами.
TARGET_PATHS: List[str] = ["backend/app", "backend/tests", "backend/scripts"]


# Альтернативно, можна вказати "." для перевірки всього проекту з pyproject.toml,
# але явне перелічення дає більше контролю.

# Базова функція-заглушка для інтернаціоналізації рядків
def _(text: str) -> str:
    return text


def run_command(command: List[str], check_mode: bool, tool_name: str, project_root: str) -> bool:
    """
    Запускає команду лінтера/форматера і обробляє результат.

    Args:
        command: Список, що представляє команду та її аргументи (без шляхів).
        check_mode: True, якщо інструмент запущено в режимі перевірки (без змін).
        tool_name: Назва інструменту для логування.
        project_root: Коренева директорія проекту, звідки запускати команду.

    Returns:
        True, якщо команда успішна (або в режимі --check нічого не змінила/не знайшла),
        False в іншому випадку.
    """
    action_desc = _("Перевірка") if check_mode else _("Форматування/виправлення")  # i18n
    # i18n: Log message - Running tool for paths
    logger.info(_("{action_desc} за допомогою {tool_name} для шляхів: {paths}").format(
        action_desc=action_desc, tool_name=tool_name, paths=', '.join(TARGET_PATHS)
    ))

    # Додаємо цільові шляхи до команди. Шляхи мають бути відносними до project_root.
    full_command = command + TARGET_PATHS
    logger.debug(f"Повна команда: {' '.join(full_command)}")

    try:
        # Запускаємо команду з кореневої директорії проекту (де лежить pyproject.toml)
        result = subprocess.run(full_command, cwd=project_root, capture_output=True, text=True, check=False)

        if result.stdout:
            logger.info(_("Вивід {tool_name}:\n{stdout}").format(tool_name=tool_name, stdout=result.stdout))  # i18n

        # Обробка stderr: багато інструментів пишуть інформаційні повідомлення сюди
        if result.stderr:
            # Для Ruff, вивід в stderr про кількість змін/проблем є нормальним.
            # Для Black в режимі --check, stderr може містити "would reformat ...".
            if result.returncode == 0 or \
                    (tool_name == "Ruff format" and check_mode and result.returncode == 1) or \
                    (
                            tool_name == "Black" and check_mode and result.returncode == 1 and "would reformat" in result.stderr) or \
                    (tool_name == "Ruff check" and result.returncode == 1):  # Ruff check повертає 1, якщо є проблеми
                # i18n: Informational output from tool (stderr)
                logger.info(_("Інформаційний вивід {tool_name} (stderr):\n{stderr}").format(tool_name=tool_name,
                                                                                            stderr=result.stderr))
            else:
                # i18n: Error output from tool (stderr)
                logger.error(
                    _("Помилки {tool_name} (stderr):\n{stderr}").format(tool_name=tool_name, stderr=result.stderr))

        # Інтерпретація кодів повернення для режиму --check
        if check_mode:
            if tool_name == "Black":
                if result.returncode == 0:  # Файли вже відформатовані
                    logger.info(_("Black: Файли вже відформатовані."))  # i18n
                    return True
                # код 1 означає, що потрібне форматування
                logger.error(_("Black: Файли потребують форматування (код повернення {code}).").format(
                    code=result.returncode))  # i18n
                return False
            elif tool_name == "Ruff format":
                if result.returncode == 0:  # Файли вже відформатовані
                    logger.info(_("Ruff format: Файли вже відформатовані."))  # i18n
                    return True
                # код 1 означає, що потрібне форматування
                logger.error(_("Ruff format: Файли потребують форматування (код повернення {code}).").format(
                    code=result.returncode))  # i18n
                return False
            elif tool_name == "Ruff check":  # ruff check (lint)
                if result.returncode == 0:  # Проблем не знайдено
                    logger.info(_("Ruff check: Проблем не знайдено."))  # i18n
                    return True
                # код 1 означає, що знайдені проблеми
                logger.error(
                    _("Ruff check: Знайдено проблеми (код повернення {code}).").format(code=result.returncode))  # i18n
                return False
            # Для невідомих інструментів у режимі --check, будь-який ненульовий код - помилка
            if result.returncode != 0:
                logger.error(_("{tool_name} (--check) завершився з кодом помилки: {code}").format(tool_name=tool_name,
                                                                                                  code=result.returncode))  # i18n
                return False
            return True  # Якщо 0, то все добре

        # Режим застосування змін (не --check)
        else:
            if result.returncode == 0:
                logger.info(
                    _("{tool_name}: Успішно застосовано зміни (або змін не було).").format(tool_name=tool_name))  # i18n
                return True
            else:
                logger.error(
                    _("{tool_name}: Помилка виконання при застосуванні змін (код: {code}).").format(tool_name=tool_name,
                                                                                                    code=result.returncode))  # i18n
                return False

    except FileNotFoundError:
        # i18n: Error message - Tool not found
        logger.error(
            _("Помилка: {tool_name} не знайдено. Переконайтеся, що він встановлений та доступний в PATH.").format(
                tool_name=command[0]))
        return False
    except Exception as e:
        # i18n: Error message - Unexpected error running tool
        logger.error(_("Неочікувана помилка під час запуску {tool_name}: {error}").format(tool_name=tool_name, error=e),
                     exc_info=True)
        return False


def main():
    # i18n: Argparse description for the script
    parser = argparse.ArgumentParser(description=_("Скрипт для запуску лінтерів та форматерів коду (Black, Ruff)."))
    parser.add_argument(
        "--check", action="store_true",
        # i18n: Argparse help for --check argument
        help=_("Запустити інструменти в режимі перевірки (без внесення змін). Використовується для CI.")
    )
    parser.add_argument("--skip-black", action="store_true", help=_("Пропустити запуск Black."))  # i18n
    parser.add_argument("--skip-ruff-format", action="store_true", help=_("Пропустити запуск Ruff format."))  # i18n
    parser.add_argument("--skip-ruff-check", action="store_true",
                        help=_("Пропустити запуск Ruff check (lint)."))  # i18n
    # TODO: Додати аргумент для MyPy, якщо він буде використовуватися.
    # parser.add_argument("--skip-mypy", action="store_true", help=_("Пропустити запуск MyPy."))

    args = parser.parse_args()

    # Важливо: лінтери та форматери зазвичай очікують запуску з кореневої директорії проекту,
    # де знаходиться `pyproject.toml` або інші файли конфігурації.
    logger.info(_("Зміна поточної робочої директорії на: {path}").format(path=PROJECT_ROOT_FOR_CONFIG))  # i18n
    os.chdir(PROJECT_ROOT_FOR_CONFIG)
    logger.info(_("Поточна робоча директорія: {cwd}").format(cwd=os.getcwd()))  # i18n

    all_linters_passed = True  # Прапорець загального успіху

    # Запуск Black
    if not args.skip_black:
        black_command_base = ["black"]
        if args.check:
            black_command_base.extend(["--check", "--diff"])
        if not run_command(black_command_base, args.check, "Black", PROJECT_ROOT_FOR_CONFIG):
            all_linters_passed = False
    else:
        logger.info(_("Пропуск Black за вимогою користувача."))  # i18n

    # Запуск Ruff format
    if not args.skip_ruff_format:
        ruff_format_command_base = ["ruff", "format"]
        if args.check:
            ruff_format_command_base.extend(["--check", "--diff"])
        if not run_command(ruff_format_command_base, args.check, "Ruff format", PROJECT_ROOT_FOR_CONFIG):
            all_linters_passed = False
    else:
        logger.info(_("Пропуск Ruff format за вимогою користувача."))  # i18n

    # Запуск Ruff check (lint)
    if not args.skip_ruff_check:
        ruff_check_command_base = ["ruff", "check"]
        if not args.check:  # Якщо НЕ --check (тобто, режим виправлення)
            ruff_check_command_base.append("--fix")
            ruff_check_command_base.append("--show-fixes")  # Показати, що було виправлено
        # У режимі --check, ruff check сам по собі є перевіркою, додаткові прапори не потрібні для цього.
        if not run_command(ruff_check_command_base, args.check, "Ruff check", PROJECT_ROOT_FOR_CONFIG):
            all_linters_passed = False
    else:
        logger.info(_("Пропуск Ruff check (lint) за вимогою користувача."))  # i18n

    # Результати
    if all_linters_passed:
        # i18n: Success message - All linters passed
        logger.info(_("Всі лінтери успішно відпрацювали{check_mode_suffix}.").format(
            check_mode_suffix=_(" в режимі перевірки") if args.check else ""  # i18n
        ))
        sys.exit(0)
    else:
        # i18n: Error message - Linters found issues
        logger.error(_("Один або більше лінтерів виявили проблеми{check_mode_suffix}.").format(
            check_mode_suffix=_(" або потребують змін для відповідності стилю") if args.check else _(
                " або не змогли їх застосувати")  # i18n
        ))
        sys.exit(1)


if __name__ == "__main__":
    # Приклади запуску:
    # # Застосувати форматування та виправлення:
    # python backend/scripts/run_linters.py
    #
    # # Тільки перевірити, без внесення змін (для CI):
    # python backend/scripts/run_linters.py --check
    #
    # # Пропустити Black:
    # python backend/scripts/run_linters.py --skip-black
    main()
