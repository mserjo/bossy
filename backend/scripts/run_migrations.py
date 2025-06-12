# backend/scripts/run_migrations.py
# -*- coding: utf-8 -*-
"""
Скрипт для управління міграціями бази даних за допомогою Alembic.

Цей скрипт є обгорткою над командним інтерфейсом Alembic, дозволяючи
виконувати основні команди Alembic, такі як upgrade, downgrade, revision,
current, history, show.
"""
import os
import sys
import logging  # Стандартний модуль логування
import argparse

# --- Налаштування шляхів ---
# Переконуємося, що корінь проекту (директорія 'backend') є в sys.path
# для правильного завантаження alembic.ini та env.py, які можуть імпортувати з `backend.app`.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)  # Це 'backend/'
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)  # Вставляємо на початок, щоб мати пріоритет
    # Повідомлення про додавання шляху може бути виведене логером після його налаштування.

# --- Налаштування логування ---
try:
    from backend.app.src.config.logging import logger

    logger.info("Використовується логер додатку для скрипта run_migrations.")  # i18n
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.info("Логер додатку не знайдено, використовується базовий логер для run_migrations.")  # i18n

if BACKEND_DIR not in sys.path:  # Логуємо, якщо шлях було додано раніше
    logger.info(f"Додано '{BACKEND_DIR}' до sys.path для Alembic.")  # i18n

# --- Імпорт Alembic ---
try:
    from alembic.config import Config as AlembicConfig
    from alembic import command as alembic_command
except ImportError:
    logger.error("Alembic не встановлено. Будь ласка, встановіть його: pip install alembic")  # i18n
    sys.exit(1)

# --- Конфігурація ---
# Шлях до файлу alembic.ini відносно директорії 'backend/'
ALEMBIC_INI_PATH = os.path.join(BACKEND_DIR, 'alembic.ini')
# Шлях до директорії міграцій, також відносно 'backend/'
# Це значення також вказано в alembic.ini як script_location
# і використовується Alembic для знаходження міграцій.
# Тут воно може бути потрібне для перевірок або логування.
ALEMBIC_SCRIPT_LOCATION = os.path.join(BACKEND_DIR, "app", "src", "migrations")


# Базова функція-заглушка для інтернаціоналізації рядків
def _(text: str) -> str:
    return text


def main():
    """
    Головна функція для розбору аргументів командного рядка та запуску команд Alembic.
    """
    # i18n: Argparse description for the script
    parser = argparse.ArgumentParser(description=_("Скрипт для управління міграціями бази даних за допомогою Alembic."))

    # Створюємо підпарсери для кожної команди Alembic
    subparsers = parser.add_subparsers(dest="alembic_command", title=_("Команди Alembic"), required=True)  # i18n

    # Команда upgrade
    # i18n: Argparse help for 'upgrade' command
    upgrade_parser = subparsers.add_parser("upgrade", help=_("Застосувати міграції до вказаної ревізії (або 'head')."))
    # i18n: Argparse help for 'revision' argument in 'upgrade'
    upgrade_parser.add_argument("revision", nargs="?", default="head",
                                help=_("ID ревізії або 'head' (за замовчуванням: 'head')."))

    # Команда downgrade
    # i18n: Argparse help for 'downgrade' command
    downgrade_parser = subparsers.add_parser("downgrade",
                                             help=_("Відкотити міграції до вказаної ревізії (або на одну вниз)."))
    # i18n: Argparse help for 'revision' argument in 'downgrade'
    downgrade_parser.add_argument("revision", nargs="?", default="-1",
                                  help=_("ID ревізії або '-1' для відкату на одну (за замовчуванням: '-1')."))

    # Команда revision (для створення нової міграції)
    # i18n: Argparse help for 'revision' command (noun)
    revision_parser = subparsers.add_parser("revision", help=_("Створити новий файл міграції."))
    # i18n: Argparse help for '-m' or '--message' argument
    revision_parser.add_argument("-m", "--message", type=str, required=False,
                                 help=_("Короткий опис міграції (для назви файлу)."))
    revision_parser.add_argument("--autogenerate", action="store_true", help=_(
        "Спробувати автогенерувати міграцію на основі змін у моделях (потребує налаштованого `env.py`)."))  # i18n

    # Команда current
    # i18n: Argparse help for 'current' command
    current_parser = subparsers.add_parser("current", help=_("Показати поточну ревізію бази даних."))
    current_parser.add_argument("--verbose", "-v", action="store_true", help=_("Показати повну інформацію."))  # i18n

    # Команда history
    # i18n: Argparse help for 'history' command
    history_parser = subparsers.add_parser("history", help=_("Показати історію міграцій."))
    # i18n: Argparse help for 'range' argument in 'history'
    history_parser.add_argument("--rev-range", "-r", type=str, default=None,
                                help=_("Діапазон ревізій для показу (наприклад, 'base:head' або 'ID1:ID2')."))
    history_parser.add_argument("--verbose", "-v", action="store_true", help=_("Показати повну інформацію."))  # i18n

    # Команда show
    # i18n: Argparse help for 'show' command
    show_parser = subparsers.add_parser("show", help=_("Показати деталі вказаної ревізії(й)."))
    # i18n: Argparse help for 'revisions' argument in 'show'
    show_parser.add_argument("revisions", nargs="+", help=_("Одна або декілька ID ревізій для показу."))

    args = parser.parse_args()

    # i18n: Log message - Loading Alembic configuration
    logger.info(_("Завантаження конфігурації Alembic з: {path}").format(path=ALEMBIC_INI_PATH))
    if not os.path.exists(ALEMBIC_INI_PATH):
        # i18n: Error message - Alembic config file not found
        logger.error(_("Файл конфігурації alembic.ini не знайдено за шляхом: {path}").format(path=ALEMBIC_INI_PATH))
        logger.error(
            _("Переконайтеся, що скрипт запускається з правильної директорії або alembic.ini існує та шлях до нього вірний."))  # i18n
        sys.exit(1)

    try:
        alembic_cfg = AlembicConfig(ALEMBIC_INI_PATH)
        # Переконуємося, що Alembic знає, де шукати env.py та міграції.
        # script_location вже має бути правильно вказаний в alembic.ini (наприклад, backend/alembic)
        # Якщо alembic.ini знаходиться в `backend/`, а script_location = `alembic`,
        # то шлях буде `backend/alembic`.
        # `main_path` в Config використовується для визначення базового шляху для відносних шляхів у alembic.ini.
        # За замовчуванням `main_path` - це директорія, де знаходиться alembic.ini.
        # У нашому випадку це `backend/`.

        # Виконання команди
        # i18n: Log message - Executing Alembic command
        logger.info(_("Виконання команди Alembic: {command_name} ...").format(command_name=args.alembic_command))

        if args.alembic_command == "upgrade":
            alembic_command.upgrade(alembic_cfg, args.revision)
        elif args.alembic_command == "downgrade":
            alembic_command.downgrade(alembic_cfg, args.revision)
        elif args.alembic_command == "revision":
            alembic_command.revision(alembic_cfg, message=args.message, autogenerate=args.autogenerate)
        elif args.alembic_command == "current":
            alembic_command.current(alembic_cfg, verbose=args.verbose)
        elif args.alembic_command == "history":
            alembic_command.history(alembic_cfg, rev_range=args.rev_range, verbose=args.verbose)
        elif args.alembic_command == "show":
            alembic_command.show(alembic_cfg, args.revisions)

        # i18n: Log message - Alembic command finished successfully
        logger.info(_("Команда Alembic '{command_name}' успішно виконана.").format(command_name=args.alembic_command))

    except Exception as e:
        # i18n: Error message - Error during Alembic command execution
        logger.error(_("Помилка під час виконання команди Alembic '{command_name}': {error}").format(
            command_name=args.alembic_command, error=e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Приклади запуску:
    # python backend/scripts/run_migrations.py upgrade head
    # python backend/scripts/run_migrations.py downgrade -1
    # python backend/scripts/run_migrations.py revision -m "create_new_table" --autogenerate
    # python backend/scripts/run_migrations.py current -v
    # python backend/scripts/run_migrations.py history -r base:head
    # python backend/scripts/run_migrations.py show <revision_id>
    #
    # Передумови:
    # 1. Встановлений Alembic.
    # 2. Існує файл alembic.ini в директорії `backend/`.
    # 3. Існує директорія міграцій (зазвичай `backend/alembic`), налаштована в alembic.ini.
    # 4. Файл `env.py` в директорії міграцій правильно налаштований для підключення до БД
    #    (зазвичай використовує DATABASE_URL з налаштувань додатка).
    main()
