# backend/scripts/db_backup.py
import subprocess
import os
import sys
import logging
import argparse
from datetime import datetime

# Налаштування базового логування для скрипта
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Додавання шляху до батьківської директорії (backend) для імпорту модулів додатку,
# зокрема, для доступу до конфігурації бази даних.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) # 'backend/'
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
    logger.info(f"Додано {PROJECT_ROOT} до sys.path")

# Спроба імпортувати налаштування БД. Може бути адаптовано під конкретну структуру конфігурації.
try:
    from app.src.config.settings import settings_app
    # Припускаємо, що settings_app має атрибути для підключення до БД, наприклад:
    # DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
    # Або ці змінні встановлені в оточенні.
except ImportError:
    logger.warning("Не вдалося імпортувати 'settings_app' з 'app.src.config.settings'. "
                   "Скрипт буде покладатися виключно на змінні оточення для параметрів БД.")
    settings_app = None

def get_db_env_var(var_name, default=None, is_int=False):
    """
    Отримує змінну оточення. Якщо settings_app існує і має відповідний атрибут,
    використовує його як значення за замовчуванням перед глобальним default.
    """
    # Назви атрибутів в settings_app можуть відрізнятися, наприклад, POSTGRES_USER замість DB_USER
    # Потрібно адаптувати відповідно до реальної структури settings_app
    # Для прикладу, припускаємо, що settings_app має атрибути DB_USER, DB_PASSWORD і т.д.
    # Або, якщо settings_app.DATABASE_URL є, можна спробувати розпарсити його.
    # Тут для простоти будемо використовувати змінні оточення напряму,
    # але з можливістю розширення для settings_app.

    value = os.getenv(var_name)
    if value is None and settings_app:
        # Приклад: намагаємося отримати DB_USER з settings_app, якщо змінна оточення DB_USER не встановлена.
        # Це потребує узгодження імен змінних. Наприклад, settings_app.DB_USER.
        # Для цього прикладу, припустимо, що ми використовуємо getenv безпосередньо.
        pass # Залишаємо value як None, щоб спрацював default, якщо є

    if value is None:
        value = default
        if value is None and not is_int: # Не встановлюємо default=None для int, щоб уникнути помилки int(None)
             logger.warning(f"Змінна оточення {var_name} не встановлена, і значення за замовчуванням не надано.")
             return None # Явно повертаємо None, якщо немає значення

    if is_int:
        try:
            return int(value) if value is not None else default
        except ValueError:
            logger.error(f"Не вдалося перетворити значення '{value}' змінної {var_name} на ціле число. Використовується значення за замовчуванням: {default}.")
            return default
    return value


def main():
    parser = argparse.ArgumentParser(description="Скрипт для створення резервної копії бази даних PostgreSQL за допомогою pg_dump.")

    # Параметри підключення до БД
    db_user = get_db_env_var("DB_USER", "postgres") # Або інше ім'я користувача за замовчуванням
    db_password = get_db_env_var("DB_PASSWORD") # Пароль краще не мати за замовчуванням
    db_host = get_db_env_var("DB_HOST", "localhost")
    db_port = get_db_env_var("DB_PORT", 5432, is_int=True)
    db_name = get_db_env_var("DB_NAME", "kudos_dev_db") # Або інша назва БД за замовчуванням

    # Шлях для збереження резервної копії
    default_backup_dir = os.path.join(PROJECT_ROOT, "backups")
    backup_dir_env = get_db_env_var("DB_BACKUP_DIR", default_backup_dir)

    parser.add_argument(
        "--db-user", default=db_user, help=f"Ім'я користувача бази даних (за замовчуванням: {db_user} або DB_USER)"
    )
    parser.add_argument(
        "--db-password", default=db_password, help="Пароль користувача бази даних (рекомендується встановлювати через DB_PASSWORD)"
    )
    parser.add_argument(
        "--db-host", default=db_host, help=f"Хост бази даних (за замовчуванням: {db_host} або DB_HOST)"
    )
    parser.add_argument(
        "--db-port", type=int, default=db_port, help=f"Порт бази даних (за замовчуванням: {db_port} або DB_PORT)"
    )
    parser.add_argument(
        "--db-name", default=db_name, help=f"Назва бази даних (за замовчуванням: {db_name} або DB_NAME)"
    )
    parser.add_argument(
        "--backup-dir", default=backup_dir_env, help=f"Директорія для збереження резервних копій (за замовчуванням: {backup_dir_env} або DB_BACKUP_DIR)"
    )
    parser.add_argument(
        "--filename", help="Ім'я файлу для резервної копії (без розширення). Якщо не вказано, генерується автоматично з часовою міткою."
    )
    parser.add_argument(
        "--pgdump-path", default=get_db_env_var("PGDUMP_PATH", "pg_dump"), help="Шлях до утиліти pg_dump (якщо вона не в PATH)."
    )
    parser.add_argument(
        "--format", default="c", choices=['p', 'c', 'd', 't'], help="Формат pg_dump: p (plain text), c (custom), d (directory), t (tar). За замовчуванням: 'c'."
    )
    parser.add_argument(
        "--compress", type=int, default=None, choices=range(10), help="Рівень стиснення для формату 'custom' або 'directory' (0-9). 0 - без стиснення."
    )


    args = parser.parse_args()

    if not args.db_password:
        logger.warning("Пароль бази даних не встановлено через аргумент --db-password або змінну оточення DB_PASSWORD.")
        # Можна додати запит пароля тут, якщо це безпечно для середовища виконання
        # password_input = getpass("Введіть пароль для бази даних: ")
        # args.db_password = password_input
        # Або просто продовжити, покладаючись на інші методи автентифікації pg_dump (напр., .pgpass)

    # Створення директорії для бекапів, якщо вона не існує
    try:
        os.makedirs(args.backup_dir, exist_ok=True)
        logger.info(f"Директорія для резервних копій: {args.backup_dir}")
    except OSError as e:
        logger.error(f"Не вдалося створити директорію для резервних копій '{args.backup_dir}': {e}")
        sys.exit(1)

    # Формування імені файлу
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename_base = args.filename if args.filename else f"{args.db_name}_backup_{timestamp}"

    # Розширення файлу залежно від формату
    file_extension = ".sql" # для plain
    if args.format == 'c':
        file_extension = ".dump" # custom format (часто використовують .dump або .backup)
    elif args.format == 't':
        file_extension = ".tar"
    elif args.format == 'd': # directory format, розширення не потрібне для імені директорії
        file_extension = ""
        # У цьому випадку backup_file_path буде шляхом до директорії

    backup_file_path = os.path.join(args.backup_dir, f"{backup_filename_base}{file_extension}")

    # Формування команди pg_dump
    pg_dump_command = [
        args.pgdump_path,
        "--host", args.db_host,
        "--port", str(args.db_port),
        "--username", args.db_user,
        "--dbname", args.db_name,
        f"--format={args.format}"
    ]
    if args.format != 'd': # Для формату 'directory' файл не вказується, а шлях
        pg_dump_command.extend(["--file", backup_file_path])
    else: # Для формату 'directory', backup_file_path це шлях до директорії
        pg_dump_command.extend(["--file", args.backup_dir]) # pg_dump створить піддиректорію там
        logger.warning(f"Для формату 'directory' pg_dump створить піддиректорію в '{args.backup_dir}'. "
                       f"Ім'я файлу '{backup_filename_base}' буде проігноровано для шляху виводу, але може бути використано для назви директорії, якщо pg_dump це підтримує (зазвичай ні).")
        # Насправді, для directory format, pg_dump очікує, що --file вказує на директорію, куди буде збережено дамп.
        # pg_dump сам не створює піддиректорію з іменем файлу. Він створює файли всередині вказаної --file директорії.
        # Тому, якщо format='d', то backup_file_path має бути директорією.
        # Ми вже створили args.backup_dir. Якщо користувач хоче специфічну піддиректорію, він має вказати її в --backup-dir.
        # Для формату 'd', pg_dump вимагає, щоб цільова директорія не існувала або була порожньою.
        # Наш скрипт створює args.backup_dir. Якщо ця директорія не порожня, pg_dump може видати помилку.
        # Це потребує більш складної логіки, якщо ми хочемо автоматично створювати унікальні піддиректорії для кожного 'd' бекапу.
        # Поки що, для 'd', ми будемо використовувати args.backup_dir як цільову, і користувач має це враховувати.
        # Або ж, для 'd' формату, ми можемо створити унікальну піддиректорію.
        if args.format == 'd':
            backup_output_path = os.path.join(args.backup_dir, backup_filename_base) # Створюємо унікальну піддиректорію
            try:
                os.makedirs(backup_output_path, exist_ok=False) # exist_ok=False, щоб переконатися, що вона нова
                logger.info(f"Створено директорію для формату 'directory': {backup_output_path}")
                pg_dump_command = [cmd if cmd != backup_file_path else backup_output_path for cmd in pg_dump_command] # Замінюємо шлях
            except FileExistsError:
                logger.error(f"Директорія для 'directory' формату '{backup_output_path}' вже існує. Видаліть її або оберіть інше ім'я/шлях.")
                sys.exit(1)
            except OSError as e:
                logger.error(f"Не вдалося створити директорію для 'directory' формату '{backup_output_path}': {e}")
                sys.exit(1)


    if args.compress is not None and args.format in ['c', 'd']: # Стиснення доступне для custom та directory
        pg_dump_command.extend([f"--compress={args.compress}"])

    # Встановлення змінної оточення PGPASSWORD для pg_dump
    env = os.environ.copy()
    if args.db_password:
        env["PGPASSWORD"] = args.db_password
    else:
        logger.info("Пароль для pg_dump не надано, покладаємося на інші методи автентифікації (наприклад, .pgpass).")

    logger.info(f"Запуск pg_dump для бази даних '{args.db_name}'...")
    # logger.debug(f"Команда: {' '.join(pg_dump_command)}") # Може містити пароль, якщо не через PGPASSWORD

    try:
        result = subprocess.run(pg_dump_command, env=env, capture_output=True, text=True, check=True)
        logger.info(f"Резервне копіювання успішно завершено.")
        if args.format != 'd':
            logger.info(f"Файл резервної копії збережено: {backup_file_path}")
        else:
             logger.info(f"Резервну копію у форматі директорії збережено в: {backup_output_path if 'backup_output_path' in locals() else pg_dump_command[-1]}") # Покращити це
        if result.stderr:
            logger.info(f"Стандартний потік помилок pg_dump:\n{result.stderr}")

    except subprocess.CalledProcessError as e:
        logger.error(f"Помилка під час виконання pg_dump (код повернення: {e.returncode}):")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        logger.error(f"Помилка: команда '{args.pgdump_path}' не знайдена. Переконайтеся, що PostgreSQL встановлено та pg_dump доступний в PATH, або вкажіть шлях через --pgdump-path.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Неочікувана помилка під час створення резервної копії: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    # Приклади запуску:
    # python backend/scripts/db_backup.py
    # python backend/scripts/db_backup.py --db-name my_other_db --backup-dir /mnt/backups
    # python backend/scripts/db_backup.py --filename custom_backup_name --format p
    # Не забувайте встановлювати змінні оточення для DB_USER, DB_PASSWORD тощо, або передавати їх як аргументи.
    main()
```
