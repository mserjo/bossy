# backend/scripts/db_restore.py
import subprocess
import os
import sys
import logging
import argparse
from getpass import getpass # Для запиту пароля, якщо потрібно

# Налаштування базового логування для скрипта
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Додавання шляху до батьківської директорії (backend) для імпорту модулів додатку,
# зокрема, для доступу до конфігурації бази даних (якщо потрібно).
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) # 'backend/'
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
    logger.info(f"Додано {PROJECT_ROOT} до sys.path")

# Спроба імпортувати налаштування БД (як у db_backup.py)
try:
    from app.src.config.settings import settings_app
except ImportError:
    logger.warning("Не вдалося імпортувати 'settings_app'. Покладатимемося на змінні оточення/аргументи.")
    settings_app = None

def get_db_env_var(var_name, default=None, is_int=False):
    value = os.getenv(var_name)
    # (Логіка отримання з settings_app може бути додана тут, аналогічно db_backup.py)
    if value is None:
        value = default
    if is_int:
        try:
            return int(value) if value is not None else default
        except ValueError:
            logger.error(f"Не вдалося перетворити '{value}' ({var_name}) на ціле число. Використовується: {default}.")
            return default
    return value

def confirm_action(prompt: str) -> bool:
    """Запитує підтвердження від користувача."""
    while True:
        response = input(f"{prompt} [так/ні]: ").strip().lower()
        if response == "так":
            return True
        elif response == "ні":
            return False
        else:
            logger.info("Будь ласка, введіть 'так' або 'ні'.")

def main():
    parser = argparse.ArgumentParser(description="Скрипт для відновлення бази даних PostgreSQL з резервної копії.")

    parser.add_argument(
        "backup_file",
        help="Шлях до файлу резервної копії (наприклад, my_backup.dump, my_backup.sql, my_backup.tar) або директорії (для формату 'directory')."
    )

    # Параметри підключення до БД
    db_user = get_db_env_var("DB_USER", "postgres")
    db_password = get_db_env_var("DB_PASSWORD") # Пароль краще не мати за замовчуванням
    db_host = get_db_env_var("DB_HOST", "localhost")
    db_port = get_db_env_var("DB_PORT", 5432, is_int=True)
    db_name = get_db_env_var("DB_NAME", "kudos_dev_db")

    parser.add_argument(
        "--db-user", default=db_user, help=f"Ім'я користувача бази даних (за замовчуванням: {db_user} або DB_USER)"
    )
    parser.add_argument(
        "--db-password", default=db_password, help="Пароль користувача бази даних (рекомендується встановлювати через DB_PASSWORD або буде запитано)"
    )
    parser.add_argument(
        "--db-host", default=db_host, help=f"Хост бази даних (за замовчуванням: {db_host} або DB_HOST)"
    )
    parser.add_argument(
        "--db-port", type=int, default=db_port, help=f"Порт бази даних (за замовчуванням: {db_port} або DB_PORT)"
    )
    parser.add_argument(
        "--db-name", default=db_name, help=f"Назва бази даних, в яку буде відновлено дані (за замовчуванням: {db_name} або DB_NAME)"
    )
    parser.add_argument(
        "--pgrestore-path", default=get_db_env_var("PGRESTORE_PATH", "pg_restore"), help="Шлях до утиліти pg_restore."
    )
    parser.add_argument(
        "--psql-path", default=get_db_env_var("PSQL_PATH", "psql"), help="Шлях до утиліти psql."
    )
    parser.add_argument(
        "--format",
        choices=['c', 'd', 't', 'p', 'auto'],
        default='auto',
        help="Формат файлу резервної копії: c (custom), d (directory), t (tar), p (plain SQL), auto (спробувати визначити). За замовчуванням: 'auto'."
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Додати опцію --clean до pg_restore (видалити об'єкти БД перед відновленням)."
    )
    parser.add_argument(
        "--create-db",
        action="store_true",
        help="Додати опцію --create до pg_restore (створити БД перед відновленням). БД {db_name} не повинна існувати."
    )
    parser.add_argument(
        "-j", "--jobs",
        type=int,
        default=None, # За замовчуванням pg_restore використовує 1
        help="Кількість паралельних завдань для pg_restore (опціонально)."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Пропустити запит на підтвердження (НЕ РЕКОМЕНДУЄТЬСЯ для продуктивних середовищ)."
    )


    args = parser.parse_args()

    if not os.path.exists(args.backup_file):
        logger.error(f"Файл резервної копії '{args.backup_file}' не знайдено.")
        sys.exit(1)

    # Визначення формату, якщо 'auto'
    backup_format = args.format
    if backup_format == 'auto':
        # Проста евристика на основі розширення або типу файлу/директорії
        if os.path.isdir(args.backup_file):
            backup_format = 'd'
            logger.info("Автоматично визначено формат резервної копії: 'directory'.")
        elif args.backup_file.endswith(".sql"):
            backup_format = 'p'
            logger.info("Автоматично визначено формат резервної копії: 'plain SQL'.")
        elif args.backup_file.endswith(".tar"):
            backup_format = 't'
            logger.info("Автоматично визначено формат резервної копії: 'tar'.")
        elif args.backup_file.endswith(".dump") or args.backup_file.endswith(".backup"): # Популярні для custom
            backup_format = 'c'
            logger.info("Автоматично визначено формат резервної копії: 'custom'.")
        else:
            logger.error("Не вдалося автоматично визначити формат резервної копії за назвою файлу.")
            logger.info("Будь ласка, вкажіть формат явно за допомогою опції --format [c|d|t|p].")
            sys.exit(1)

    # Попередження та запит на підтвердження
    logger.warning(f"УВАГА! Ця операція перезапише ВСІ дані в базі даних '{args.db_name}' на хості '{args.db_host}'.")
    logger.warning("Рекомендується створювати резервну копію поточної БД перед відновленням, якщо вона містить цінні дані.")
    if not args.force:
        if not confirm_action(f"Ви впевнені, що хочете продовжити відновлення БД '{args.db_name}' з файлу '{args.backup_file}'?"):
            logger.info("Відновлення скасовано користувачем.")
            sys.exit(0)

    # Запит пароля, якщо не надано
    db_password_to_use = args.db_password
    if not db_password_to_use:
        logger.info("Пароль бази даних не надано через аргумент або змінну оточення.")
        db_password_to_use = getpass(f"Введіть пароль для користувача '{args.db_user}' бази даних '{args.db_name}': ")

    env = os.environ.copy()
    if db_password_to_use:
        env["PGPASSWORD"] = db_password_to_use

    restore_command = []

    if backup_format == 'p': # Plain SQL
        logger.info(f"Відновлення з plain SQL файлу '{args.backup_file}' за допомогою psql...")
        restore_command = [
            args.psql_path,
            "--host", args.db_host,
            "--port", str(args.db_port),
            "--username", args.db_user,
            "--dbname", args.db_name, # psql підключається до вказаної БД
            "--file", args.backup_file,
            "--single-transaction" # Рекомендується для атомарності
        ]
        # Для psql, якщо БД потрібно створити, це має бути зроблено окремою командою `createdb`
        # Опції --clean та --create-db не застосовуються до psql таким же чином, як до pg_restore
        if args.clean or args.create_db:
            logger.warning("Опції --clean та --create-db не повністю сумісні з відновленням з plain SQL через psql. "
                           "Очищення та створення БД може потребувати окремих кроків.")

    else: # Custom, Directory, Tar - використовуються pg_restore
        logger.info(f"Відновлення з формату '{backup_format}' файлу/директорії '{args.backup_file}' за допомогою pg_restore...")
        restore_command = [
            args.pgrestore_path,
            "--host", args.db_host,
            "--port", str(args.db_port),
            "--username", args.db_user,
            "--dbname", args.db_name # pg_restore може створити БД, якщо вказано --create
        ]
        if args.clean:
            restore_command.append("--clean")
        if args.create_db:
            restore_command.append("--create")
        if args.jobs is not None:
            restore_command.extend(["--jobs", str(args.jobs)])

        if backup_format == 'd': # Для directory format, backup_file це шлях до директорії
            restore_command.append(args.backup_file)
        else: # Для custom та tar, це шлях до файлу
            restore_command.append(args.backup_file)


    logger.info(f"Запуск команди відновлення...")
    # logger.debug(f"Команда: {' '.join(restore_command)}") # Може містити пароль, якщо не через PGPASSWORD

    try:
        result = subprocess.run(restore_command, env=env, capture_output=True, text=True, check=True)
        logger.info(f"Відновлення бази даних '{args.db_name}' успішно завершено.")
        if result.stdout: # psql може виводити інформацію в stdout
            logger.info(f"Стандартний потік виводу:\n{result.stdout}")
        if result.stderr: # pg_restore часто виводить прогрес та підсумки в stderr
            logger.info(f"Стандартний потік помилок (може містити інформацію про прогрес):\n{result.stderr}")

    except subprocess.CalledProcessError as e:
        logger.error(f"Помилка під час виконання команди відновлення (код повернення: {e.returncode}):")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        tool_path = args.psql_path if backup_format == 'p' else args.pgrestore_path
        logger.error(f"Помилка: команда '{tool_path}' не знайдена. Переконайтеся, що PostgreSQL встановлено та утиліта доступна в PATH, або вкажіть шлях через відповідну опцію.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Неочікувана помилка під час відновлення бази даних: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    # Приклади запуску:
    # python backend/scripts/db_restore.py backups/my_db_backup_20230101_120000.dump --db-name my_restored_db --format c --create-db
    # python backend/scripts/db_restore.py backups/my_db_backup.sql --format p
    # Не забувайте про підтвердження, якщо не використовуєте --force.
    main()
