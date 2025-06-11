# backend/scripts/db_restore.py
# -*- coding: utf-8 -*-
"""
Скрипт для відновлення бази даних PostgreSQL з резервної копії.

Використовує утиліти `pg_restore` (для форматів custom, directory, tar)
або `psql` (для формату plain SQL).
Дозволяє налаштовувати параметри підключення до БД, шлях до файлу/директорії бекапу,
та опції відновлення.
"""
import subprocess
import os
import sys
import logging  # Стандартний модуль логування
import argparse
from getpass import getpass  # Для безпечного введення пароля, якщо потрібно
from typing import Optional, List, Union, Any  # Для типізації

# --- Налаштування шляхів для імпорту модулів додатку ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)  # Директорія 'backend'
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

# --- Імпорт компонентів додатку ---
try:
    from backend.app.src.config.logging import logger

    logger.info("Використовується логер додатку для скрипта db_restore.")  # i18n
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.info("Логер додатку не знайдено, використовується базовий логер для db_restore.")  # i18n

try:
    from backend.app.src.core.config import settings as app_settings

    logger.debug("Налаштування додатка успішно імпортовано для db_restore.")  # i18n
except ImportError:
    app_settings = None
    logger.warning(
        "Не вдалося імпортувати налаштування додатка ('settings' з 'backend.app.src.core.config') для db_restore. "  # i18n
        "Скрипт буде покладатися на аргументи командного рядка та змінні середовища.")


# Базова функція-заглушка для інтернаціоналізації рядків
def _(text: str) -> str:
    return text


def get_db_param(
        arg_value: Optional[Any],  # Може бути int з argparse
        env_var_name: str,
        app_setting_attr: Optional[str] = None,
        default_value: Optional[Union[str, int]] = None,
        is_int: bool = False
) -> Optional[Union[str, int]]:
    """
    Визначає параметр БД, надаючи пріоритет:
    1. Аргументу командного рядка.
    2. Змінній середовища.
    3. Налаштуванню з `app_settings`.
    4. Значенню за замовчуванням.
    """
    value: Any = None

    if arg_value is not None:
        value = arg_value
        logger.debug(f"Використано значення з аргументу командного рядка для {env_var_name}: '{value}'")
    elif os.getenv(env_var_name) is not None:
        value = os.getenv(env_var_name)
        logger.debug(f"Використано значення зі змінної середовища {env_var_name}: '{value}'")
    elif app_settings and app_setting_attr and hasattr(app_settings, app_setting_attr):
        value = getattr(app_settings, app_setting_attr, None)
        logger.debug(f"Використано значення з налаштувань додатка {app_setting_attr}: '{value}'")
    elif default_value is not None:
        value = default_value
        logger.debug(f"Використано значення за замовчуванням для {env_var_name}: '{value}'")

    if value is None:
        # Для пароля це нормально, якщо він не встановлений і буде запитаний пізніше
        if env_var_name != "PGPASSWORD":
            logger.warning(_("Параметр '{param_name}' не визначено.").format(param_name=env_var_name))  # i18n
        return None

    if is_int:
        try:
            return int(value)
        except ValueError:
            logger.error(
                _("Не вдалося перетворити значення '{value}' параметра '{param_name}' на ціле число. Повертається None.").format(
                    value=value, param_name=env_var_name))  # i18n
            return None
    return str(value)


def confirm_action(prompt: str) -> bool:
    """Запитує підтвердження дії від користувача."""
    while True:
        try:
            # i18n: User confirmation prompt
            response = input(f"{prompt} [{_('так')}/{_('ні')}]: ").strip().lower()
        except KeyboardInterrupt:
            logger.warning(_("\nДію скасовано користувачем (Ctrl+C)."))  # i18n
            return False
        if response == _("так"):  # i18n
            return True
        elif response == _("ні"):  # i18n
            return False
        else:
            # i18n: Invalid input for confirmation
            print(_("Будь ласка, введіть 'так' або 'ні'."))


def main():
    # i18n: Argparse description
    parser = argparse.ArgumentParser(description=_("Скрипт для відновлення бази даних PostgreSQL з резервної копії."))

    parser.add_argument(
        "backup_file",
        help=_(
            "Шлях до файлу резервної копії (наприклад, my_backup.dump, my_backup.sql, my_backup.tar) або директорії (для формату 'directory').")
        # i18n
    )
    parser.add_argument("--db-user", type=str, default=None, help=_(
        "Ім'я користувача БД. Пріоритет: аргумент > PGUSER > налаштування > 'postgres'."))  # i18n
    parser.add_argument("--db-password", type=str, default=None, help=_(
        "Пароль користувача БД. Пріоритет: аргумент > PGPASSWORD > запит. (Не рекомендовано передавати як аргумент)"))  # i18n
    parser.add_argument("--db-host", type=str, default=None,
                        help=_("Хост БД. Пріоритет: аргумент > PGHOST > налаштування > 'localhost'."))  # i18n
    parser.add_argument("--db-port", type=int, default=None,
                        help=_("Порт БД. Пріоритет: аргумент > PGPORT > налаштування > 5432."))  # i18n
    parser.add_argument("--db-name", type=str, default=None, help=_(
        "Назва БД для відновлення. Пріоритет: аргумент > PGDATABASE > налаштування > 'kudos_dev_db'."))  # i18n

    parser.add_argument("--pgrestore-path", type=str, default=None, help=_(
        "Шлях до утиліти pg_restore. За замовчуванням: 'pg_restore' або PGRESTORE_PATH."))  # i18n
    parser.add_argument("--psql-path", type=str, default=None,
                        help=_("Шлях до утиліти psql. За замовчуванням: 'psql' або PSQL_PATH."))  # i18n

    parser.add_argument(
        "--format", choices=['c', 'd', 't', 'p', 'auto'], default='auto',
        help=_(
            "Формат файлу резервної копії: c (custom), d (directory), t (tar), p (plain SQL), auto (спробувати визначити). За замовчуванням: 'auto'.")
        # i18n
    )
    parser.add_argument("--clean", action="store_true",
                        help=_("Додати опцію --clean до pg_restore (видалити об'єкти БД перед відновленням)."))  # i18n
    parser.add_argument("--create-db", action="store_true", help=_(
        "Додати опцію --create до pg_restore (створити БД перед відновленням; БД не повинна існувати)."))  # i18n
    parser.add_argument("-j", "--jobs", type=int, default=None,
                        help=_("Кількість паралельних завдань для pg_restore (опціонально)."))  # i18n
    parser.add_argument("--force", action="store_true",
                        help=_("Пропустити запит на підтвердження (НЕ РЕКОМЕНДУЄТЬСЯ!)."))  # i18n

    args = parser.parse_args()

    # Визначення параметрів
    db_user = get_db_param(args.db_user, "PGUSER", "POSTGRES_USER", "postgres")
    db_password_arg = get_db_param(args.db_password, "PGPASSWORD", "POSTGRES_PASSWORD", None)  # Пароль з аргументів/env
    db_host = get_db_param(args.db_host, "PGHOST", "POSTGRES_HOST", "localhost")
    db_port = get_db_param(args.db_port, "PGPORT", "POSTGRES_PORT", 5432, is_int=True)
    db_name = get_db_param(args.db_name, "PGDATABASE", "POSTGRES_DB", "kudos_dev_db")

    pgrestore_path = get_db_param(args.pgrestore_path, "PGRESTORE_PATH", None, "pg_restore")
    psql_path = get_db_param(args.psql_path, "PSQL_PATH", None, "psql")

    if not all([db_user, db_host, db_port is not None, db_name, pgrestore_path, psql_path]):
        logger.error(_("Один або декілька критичних параметрів не визначено. Перевірте налаштування."))  # i18n
        sys.exit(1)

    if not os.path.exists(args.backup_file):
        logger.error(
            _("Файл або директорія резервної копії '{path}' не знайдено.").format(path=args.backup_file))  # i18n
        sys.exit(1)

    # Визначення формату, якщо 'auto'
    backup_format = args.format
    if backup_format == 'auto':
        if os.path.isdir(args.backup_file):
            backup_format = 'd'
        elif args.backup_file.endswith(".sql"):
            backup_format = 'p'
        elif args.backup_file.endswith(".tar"):
            backup_format = 't'
        elif args.backup_file.endswith((".dump", ".backup")):
            backup_format = 'c'
        else:
            logger.error(
                _("Не вдалося автоматично визначити формат резервної копії. Вкажіть його через --format."))  # i18n
            sys.exit(1)
        logger.info(_("Автоматично визначено формат резервної копії: '{format}'.").format(format=backup_format))  # i18n

    # Попередження та підтвердження
    logger.warning(
        _("УВАГА! Ця операція може перезаписати дані в базі '{db_name}' на хості '{db_host}'.").format(db_name=db_name,
                                                                                                       db_host=db_host))  # i18n
    logger.warning(
        _("Рекомендується створити резервну копію поточної БД перед відновленням, якщо вона містить цінні дані."))  # i18n
    if not args.force:
        if not confirm_action(
                _("Ви впевнені, що хочете продовжити відновлення БД '{db_name}' з '{backup_path}'?").format(
                        db_name=db_name, backup_path=args.backup_file)):  # i18n
            logger.info(_("Відновлення скасовано користувачем."))  # i18n
            sys.exit(0)

    # Пароль
    db_password_to_use = db_password_arg
    if not db_password_to_use:
        try:
            prompt_msg = _(
                "Введіть пароль для користувача '{user}' бази даних '{db}' (або натисніть Enter, якщо пароль не потрібен): ").format(
                user=db_user, db=db_name)  # i18n
            db_password_to_use = getpass(prompt_msg)
        except KeyboardInterrupt:
            logger.warning(_("\nВведення пароля перервано. Відновлення скасовано."))  # i18n
            sys.exit(1)
        except EOFError:
            logger.error(
                _("Не вдалося прочитати пароль (EOF). Якщо пароль не потрібен, спробуйте передати порожній пароль через змінну середовища PGPASSWORD=''."))  # i18n
            sys.exit(1)

    process_env = os.environ.copy()
    if db_password_to_use:  # Навіть якщо порожній рядок, встановимо, pg_restore/psql це оброблять
        process_env["PGPASSWORD"] = db_password_to_use
    elif "PGPASSWORD" in process_env:  # Якщо користувач передав порожній пароль, а PGPASSWORD вже є в env, видаляємо його
        del process_env["PGPASSWORD"]

    restore_command: List[str] = []
    tool_name = ""

    if backup_format == 'p':  # Plain SQL
        tool_name = str(psql_path)
        logger.info(
            _("Відновлення з plain SQL файлу '{path}' за допомогою psql...").format(path=args.backup_file))  # i18n
        restore_command = [
            tool_name, "--host", str(db_host), "--port", str(db_port),
            "--username", str(db_user), "--dbname", str(db_name),
            "--file", args.backup_file, "--single-transaction"
        ]
        if args.clean or args.create_db:
            logger.warning(
                _("Опції --clean та --create-db мають обмежену дію з psql. Очищення/створення БД може потребувати окремих кроків."))  # i18n
    else:  # Custom, Directory, Tar
        tool_name = str(pgrestore_path)
        logger.info(_("Відновлення з формату '{format}' файлу/директорії '{path}' за допомогою pg_restore...").format(
            format=backup_format, path=args.backup_file))  # i18n
        restore_command = [
            tool_name, "--host", str(db_host), "--port", str(db_port),
            "--username", str(db_user), "--dbname", str(db_name)
        ]
        if args.clean: restore_command.append("--clean")
        if args.create_db: restore_command.append("--create")
        if args.jobs is not None: restore_command.extend(["--jobs", str(args.jobs)])
        restore_command.append(args.backup_file)  # шлях до файлу/директорії бекапу

    logger.info(_("Запуск команди відновлення..."))  # i18n
    logger.debug(f"Команда: {' '.join(restore_command)}")

    try:
        result = subprocess.run(restore_command, env=process_env, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            logger.info(_("Відновлення бази даних '{db_name}' успішно завершено.").format(db_name=db_name))  # i18n
            if result.stdout: logger.info(_("Stdout:\n{output}").format(output=result.stdout))  # i18n
            if result.stderr: logger.info(
                _("Stderr (може містити інформацію про прогрес):\n{output}").format(output=result.stderr))  # i18n
        else:
            logger.error(_("Помилка під час виконання команди відновлення (код: {code}).").format(
                code=result.returncode))  # i18n
            if result.stdout: logger.error(_("Stdout:\n{output}").format(output=result.stdout))  # i18n
            if result.stderr: logger.error(_("Stderr:\n{output}").format(output=result.stderr))  # i18n
            sys.exit(result.returncode)

    except FileNotFoundError:
        logger.error(
            _("Помилка: команда '{tool}' не знайдена. Переконайтесь, що PostgreSQL встановлено та утиліта доступна в PATH, або вкажіть шлях через відповідну опцію (--{tool_option}-path).").format(
                tool=tool_name, tool_option=tool_name.replace('_', '-')))  # i18n
        sys.exit(1)
    except Exception as e:
        logger.error(_("Неочікувана помилка під час відновлення бази даних: {error}").format(error=e),
                     exc_info=True)  # i18n
        sys.exit(1)


if __name__ == "__main__":
    # Приклади запуску:
    # python backend/scripts/db_restore.py backups/kudos_dev_db_backup_YYYYMMDD_HHMMSS.dump --db-name kudos_restored_db --format c --create-db --force
    # python backend/scripts/db_restore.py backups/backup.sql --format p
    main()
