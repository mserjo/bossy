# backend/app/src/tasks/system/backup.py
# -*- coding: utf-8 -*-
"""
Фонові завдання для створення резервних копій системи.
"""
from backend.app.src.config.logging import get_logger
# TODO: Імпортувати екземпляр Celery app
# from backend.app.src.workers import celery_app as app # Приклад
# TODO: Імпортувати налаштування (шляхи для бекапів, дані для підключення до БД)
# from backend.app.src.core.config import settings
# import subprocess # Для запуску утиліт типу pg_dump
# import os
# from datetime import datetime

logger = get_logger(__name__)

# @app.task(name="tasks.system.backup.backup_database_task") # Приклад для Celery
def backup_database_task(backup_directory: Optional[str] = None, retention_days: Optional[int] = 7):
    """
    Періодичне завдання для створення резервної копії бази даних.

    Args:
        backup_directory (Optional[str]): Директорія для збереження бекапів.
                                          Якщо None, використовується значення з settings.
        retention_days (Optional[int]): Кількість днів, протягом яких зберігати бекапи.
                                        Старіші бекапи будуть видалені.
                                        Якщо None, використовується значення з settings.
    """
    logger.info("Запуск завдання створення резервної копії бази даних...")

    # backup_dir = backup_directory or settings.DATABASE_BACKUP_DIR
    # effective_retention_days = retention_days if retention_days is not None else settings.DATABASE_BACKUP_RETENTION_DAYS

    # if not os.path.exists(backup_dir):
    #     try:
    #         os.makedirs(backup_dir)
    #         logger.info(f"Створено директорію для бекапів: {backup_dir}")
    #     except OSError as e:
    #         logger.error(f"Не вдалося створити директорію для бекапів {backup_dir}: {e}")
    #         return {"status": "failed", "message": f"Could not create backup directory: {e}"}

    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # backup_filename = f"db_backup_{timestamp}.sql.gz" # Або .dump, .bak залежно від СУБД
    # backup_filepath = os.path.join(backup_dir, backup_filename)

    # # Команда для pg_dump (приклад для PostgreSQL)
    # # Потрібно безпечно отримати дані для підключення з settings
    # db_user = settings.DATABASE_USER
    # db_password = settings.DATABASE_PASSWORD # Увага: безпека пароля!
    # db_host = settings.DATABASE_HOST
    # db_port = settings.DATABASE_PORT
    # db_name = settings.DATABASE_NAME
    #
    # # Встановлення змінної середовища для пароля, щоб не передавати його в командному рядку
    # pg_env = os.environ.copy()
    # pg_env["PGPASSWORD"] = db_password
    #
    # dump_command = [
    #     'pg_dump',
    #     f'--host={db_host}',
    #     f'--port={db_port}',
    #     f'--username={db_user}',
    #     f'--dbname={db_name}',
    #     '--format=c', # Стиснутий формат
    #     '--blobs',
    #     f'--file={backup_filepath}' # pg_dump сам стисне, якщо файл має .gz, або використовуємо gzip окремо
    # ]
    # # Якщо pg_dump не стискає, то:
    # # dump_command = f"pg_dump -U {db_user} -h {db_host} -p {db_port} {db_name} | gzip > {backup_filepath}"

    # try:
    #     # logger.info(f"Створення бекапу: {' '.join(dump_command)}") # Не логувати пароль!
    #     logger.info(f"Створення бекапу бази даних {db_name} у файл {backup_filepath}...")
    #     # process = subprocess.run(dump_command, env=pg_env, check=True, capture_output=True, text=True) # Для команди як списку
    #     # Або для команди як рядка з пайпом:
    #     # process = subprocess.run(dump_command, shell=True, env=pg_env, check=True, capture_output=True, text=True)
    #     # logger.info(f"STDOUT: {process.stdout}")
    #     # logger.info(f"STDERR: {process.stderr}")
    #     logger.info(f"Резервну копію бази даних успішно створено: {backup_filepath} (ЗАГЛУШКА).")
    #
    #     # TODO: Реалізувати очищення старих бекапів згідно retention_days
    #     # cleanup_old_backups(backup_dir, effective_retention_days)
    #
    # except subprocess.CalledProcessError as e:
    #     # logger.error(f"Помилка створення резервної копії: {e}")
    #     # logger.error(f"STDOUT: {e.stdout}")
    #     # logger.error(f"STDERR: {e.stderr}")
    #     # return {"status": "failed", "message": f"Database backup failed: {e.stderr}"}
    #     pass # Заглушка
    # except Exception as e:
    #     # logger.error(f"Неочікувана помилка при створенні резервної копії: {e}", exc_info=True)
    #     # return {"status": "failed", "message": f"Unexpected error during backup: {e}"}
    #     pass # Заглушка

    logger.info("Завдання створення резервної копії бази даних завершено (ЗАГЛУШКА).")
    return {"status": "completed", "message": "Database backup task finished (stub)."}


# def cleanup_old_backups(backup_dir: str, retention_days: int):
#     """Видаляє старі файли бекапів."""
#     # logger.info(f"Очищення старих бекапів у {backup_dir}, зберігаємо за останні {retention_days} днів.")
#     # now = time.time()
#     # for filename in os.listdir(backup_dir):
#     #     file_path = os.path.join(backup_dir, filename)
#     #     if os.path.isfile(file_path) and filename.startswith("db_backup_") and (filename.endswith(".gz") or filename.endswith(".sql")):
#     #         try:
#     #             file_age_days = (now - os.path.getmtime(file_path)) / (24 * 3600)
#     #             if file_age_days > retention_days:
#     #                 os.remove(file_path)
#     #                 logger.info(f"Видалено старий бекап: {file_path}")
#     #         except OSError as e:
#     #             logger.error(f"Помилка видалення старого бекапу {file_path}: {e}")
#     pass

# TODO: Додати завдання для резервного копіювання завантажених файлів (якщо вони не в S3 тощо).
