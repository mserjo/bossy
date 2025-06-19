# backend/scripts/db_backup.py
# -*- coding: utf-8 -*-
"""
Скрипт для створення резервної копії бази даних PostgreSQL.

Використовує утиліту `pg_dump` для створення бекапу.
Дозволяє налаштовувати параметри підключення до БД, шлях збереження,
ім'я файлу, формат бекапу та рівень стиснення.
Параметри можуть передаватися через аргументи командного рядка,
змінні середовища (стандартні для PostgreSQL), або, якщо доступно,
з конфігураційного файлу додатка.
"""
import subprocess
import os
import sys
import logging  # Стандартний модуль логування
import argparse
from datetime import datetime
from typing import Optional, List, Union, Any

# --- Налаштування шляхів для імпорту модулів додатку ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)  # Директорія 'backend'
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

# --- Імпорт компонентів додатку ---
# Намагаємося імпортувати логер та налаштування додатку.
try:
    from backend.app.src.config.logging import get_logger # Змінено імпорт
    logger = get_logger(__name__) # Отримуємо логер для цього скрипта
    logger.info("Використовується логер додатку для скрипта db_backup.")  # i18n
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.info("Логер додатку не знайдено (ImportError), використовується базовий логер для db_backup.")  # i18n

try:
    from backend.app.src.core.config import \
        settings as app_settings  # Припускаємо, що головний об'єкт налаштувань називається 'settings'

    # Для доступу до DATABASE_URL або окремих параметрів БД.
    # Наприклад: app_settings.DATABASE_URL або app_settings.POSTGRES_USER, ..._PASSWORD, etc.
    logger.debug("Налаштування додатка успішно імпортовано.")  # i18n
except ImportError:
    app_settings = None
    logger.warning("Не вдалося імпортувати налаштування додатка ('settings' з 'backend.app.src.core.config'). "  # i18n
                   "Скрипт буде покладатися на аргументи командного рядка та змінні середовища.")


# Базова функція-заглушка для інтернаціоналізації рядків
def _(text: str) -> str:
    return text


def get_db_param(
        arg_value: Optional[str],
        env_var_name: str,
        app_setting_attr: Optional[str] = None,
        default_value: Optional[Union[str, int]] = None,
        is_int: bool = False
) -> Optional[Union[str, int]]:
    """
    Визначає параметр БД, надаючи пріоритет:
    1. Аргументу командного рядка (arg_value).
    2. Змінній середовища (env_var_name).
    3. Налаштуванню з об'єкта `app_settings` (app_setting_attr), якщо доступно.
    4. Значенню за замовчуванням (default_value).

    Args:
        arg_value: Значення з аргументу командного рядка.
        env_var_name: Назва змінної середовища.
        app_setting_attr: Назва атрибута в об'єкті `app_settings`.
        default_value: Значення за замовчуванням.
        is_int: Чи потрібно перетворити значення на ціле число.

    Returns:
        Визначене значення параметра або None.
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
        logger.warning(
            _("Параметр '{param_name}' не визначено (аргумент, змінна середовища, налаштування додатка чи значення за замовчуванням).").format(
                param_name=env_var_name))  # i18n
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


def main():
    # i18n: Argparse description for the script
    parser = argparse.ArgumentParser(
        description=_("Скрипт для створення резервної копії бази даних PostgreSQL за допомогою pg_dump."))

    # Аргументи командного рядка
    parser.add_argument("--db-user", type=str, default=None, help=_(
        "Ім'я користувача бази даних. Пріоритет: аргумент > PGUSER > налаштування > 'postgres'."))  # i18n
    parser.add_argument("--db-password", type=str, default=None, help=_(
        "Пароль користувача БД. Пріоритет: аргумент > PGPASSWORD. (не рекомендовано передавати як аргумент)"))  # i18n
    parser.add_argument("--db-host", type=str, default=None,
                        help=_("Хост бази даних. Пріоритет: аргумент > PGHOST > налаштування > 'localhost'."))  # i18n
    parser.add_argument("--db-port", type=int, default=None,
                        help=_("Порт бази даних. Пріоритет: аргумент > PGPORT > налаштування > 5432."))  # i18n
    parser.add_argument("--db-name", type=str, default=None, help=_(
        "Назва бази даних. Пріоритет: аргумент > PGDATABASE > налаштування > 'kudos_dev_db'."))  # i18n

    default_backup_dir = os.path.join(BACKEND_DIR, "backups")
    parser.add_argument("--backup-dir", type=str, default=None, help=_(
        "Директорія для збереження резервних копій. За замовчуванням: '{default_dir}' або DB_BACKUP_DIR.").format(
        default_dir=default_backup_dir))  # i18n
    parser.add_argument("--filename", type=str, default=None, help=_(
        "Ім'я файлу для резервної копії (без розширення). Якщо не вказано, генерується автоматично."))  # i18n
    parser.add_argument("--pgdump-path", type=str, default=None, help=_(
        "Шлях до утиліти pg_dump. За замовчуванням: 'pg_dump' (з PATH) або PGDUMP_PATH."))  # i18n
    parser.add_argument("--format", default="c", choices=['p', 'c', 'd', 't'], help=_(
        "Формат pg_dump: p (plain SQL), c (custom archive), d (directory), t (tar archive). За замовчуванням: 'c'."))  # i18n
    parser.add_argument("--compress", type=int, default=None, choices=range(10), help=_(
        "Рівень стиснення для формату 'c' або 'd' (0-9). 0 - без стиснення. За замовчуванням: не встановлено (pg_dump default)."))  # i18n

    args = parser.parse_args()

    # Визначення параметрів підключення до БД
    # Пріоритет: аргумент командного рядка > стандартна змінна середовища PostgreSQL > налаштування додатка > значення за замовчуванням
    db_user = get_db_param(args.db_user, "PGUSER", "POSTGRES_USER", "postgres")
    db_password = get_db_param(args.db_password, "PGPASSWORD", "POSTGRES_PASSWORD",
                               None)  # Пароль не має значення за замовчуванням
    db_host = get_db_param(args.db_host, "PGHOST", "POSTGRES_HOST", "localhost")
    db_port = get_db_param(args.db_port, "PGPORT", "POSTGRES_PORT", 5432, is_int=True)
    db_name = get_db_param(args.db_name, "PGDATABASE", "POSTGRES_DB", "kudos_dev_db")

    pgdump_path = get_db_param(args.pgdump_path, "PGDUMP_PATH", None, "pg_dump")
    backup_dir = get_db_param(args.backup_dir, "DB_BACKUP_DIR", None, default_backup_dir)

    if not all([db_user, db_host, db_port is not None, db_name, pgdump_path, backup_dir]):
        logger.error(
            _("Один або декілька критичних параметрів не визначено (користувач БД, хост, порт, назва БД, шлях до pg_dump, директорія для бекапів). Перевірте налаштування."))  # i18n
        sys.exit(1)

    # Створення директорії для бекапів, якщо вона не існує
    try:
        os.makedirs(backup_dir, exist_ok=True)
        logger.info(_("Директорія для резервних копій: {backup_dir}").format(backup_dir=backup_dir))  # i18n
    except OSError as e:
        logger.error(_("Не вдалося створити директорію для резервних копій '{backup_dir}': {error}").format(
            backup_dir=backup_dir, error=e))  # i18n
        sys.exit(1)

    # Формування імені файлу або шляху для директорії
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename_base = args.filename if args.filename else f"{db_name}_backup_{timestamp}"

    output_path: str  # Шлях для опції --file у pg_dump

    if args.format == 'd':  # Directory format
        output_path = os.path.join(backup_dir, backup_filename_base)  # Це буде назва директорії для бекапу
        try:
            if os.path.exists(output_path) and os.listdir(output_path):  # Перевірка, чи існує і не порожня
                logger.error(
                    _("Директорія для резервної копії формату 'directory' ('{path}') вже існує та не порожня. Будь ласка, видаліть її або оберіть інше ім'я/шлях.").format(
                        path=output_path))  # i18n
                sys.exit(1)
            os.makedirs(output_path, exist_ok=True)  # Створюємо, якщо не існує; якщо існує і порожня - все гаразд
            logger.info(
                _("Резервна копія у форматі 'directory' буде збережена в: {path}").format(path=output_path))  # i18n
        except OSError as e:
            logger.error(_("Не вдалося створити/перевірити директорію для резервної копії '{path}': {error}").format(
                path=output_path, error=e))  # i18n
            sys.exit(1)
    else:  # File formats (p, c, t)
        file_extensions = {'p': ".sql", 'c': ".dump", 't': ".tar"}
        file_extension = file_extensions[args.format]
        output_path = os.path.join(backup_dir, f"{backup_filename_base}{file_extension}")
        logger.info(_("Файл резервної копії буде збережено як: {path}").format(path=output_path))  # i18n

    # Формування команди pg_dump
    pg_dump_command: List[str] = [
        str(pgdump_path),  # Переконуємося, що шлях є рядком
        "--host", str(db_host),
        "--port", str(db_port),
        "--username", str(db_user),
        "--dbname", str(db_name),
        f"--format={args.format}",
        "--file", output_path  # Для всіх форматів pg_dump приймає --file
    ]

    if args.compress is not None and args.format in ['c', 'd', 't']:  # Стиснення для custom, directory, tar
        pg_dump_command.append(f"--compress={args.compress}")

    # Додаткові корисні опції для pg_dump:
    # pg_dump_command.append("--verbose") # Для детального виводу від pg_dump
    # pg_dump_command.append("--clean")   # Додати команди DROP перед CREATE (для plain text)
    # pg_dump_command.append("--if-exists") # Використовувати DROP ... IF EXISTS (для plain text)

    # Встановлення змінної оточення PGPASSWORD
    process_env = os.environ.copy()
    if db_password:
        process_env["PGPASSWORD"] = db_password
    else:
        # i18n: Log message - PGPASSWORD not set
        logger.info(_("Пароль для pg_dump не надано (PGPASSWORD не встановлено). "
                      "pg_dump спробує використати інші методи автентифікації (наприклад, .pgpass або довіру)."))

    # i18n: Log message - Starting pg_dump
    logger.info(_("Запуск pg_dump для бази даних '{db_name}'...").format(db_name=db_name))
    logger.debug(f"Команда pg_dump: {' '.join(pg_dump_command)}")  # Увага: може містити шлях до файлу, але не пароль

    try:
        # Виконання команди pg_dump
        result = subprocess.run(pg_dump_command, env=process_env, capture_output=True, text=True,
                                check=False)  # check=False для ручної обробки помилок

        if result.returncode == 0:
            logger.info(_("Резервне копіювання успішно завершено."))  # i18n
            if result.stderr:  # pg_dump може виводити інформаційні повідомлення в stderr
                logger.info(
                    _("Стандартний потік помилок (stderr) від pg_dump:\n{stderr}").format(stderr=result.stderr))  # i18n
        else:
            # i18n: Error message - pg_dump failed
            logger.error(_("Помилка під час виконання pg_dump (код повернення: {return_code}):").format(
                return_code=result.returncode))
            if result.stdout:
                logger.error(_("Stdout від pg_dump:\n{stdout}").format(stdout=result.stdout))  # i18n
            if result.stderr:
                logger.error(_("Stderr від pg_dump:\n{stderr}").format(stderr=result.stderr))  # i18n
            sys.exit(result.returncode)

    except FileNotFoundError:
        # i18n: Error message - pg_dump command not found
        logger.error(
            _("Помилка: команда '{pgdump_path}' не знайдена. Переконайтеся, що PostgreSQL клієнт встановлено та pg_dump доступний в системному PATH, або вкажіть шлях через --pgdump-path.").format(
                pgdump_path=pgdump_path))
        sys.exit(1)
    except Exception as e:
        # i18n: Error message - Unexpected error during backup
        logger.error(_("Неочікувана помилка під час створення резервної копії: {error}").format(error=e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Приклади запуску:
    # python backend/scripts/db_backup.py
    # python backend/scripts/db_backup.py --db-name my_other_db --backup-dir /mnt/backups
    # python backend/scripts/db_backup.py --filename custom_backup_name --format p
    #
    # Рекомендації:
    # - Встановлюйте змінні середовища PGUSER, PGPASSWORD, PGHOST, PGDATABASE, PGPORT для автоматичної конфігурації.
    # - Або передавайте параметри через аргументи командного рядка.
    # - Для безпеки, уникайте передачі пароля як аргументу командного рядка у продакшн середовищах.
    main()
