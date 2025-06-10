# backend/app/src/tasks/system/backup.py
# -*- coding: utf-8 -*-
"""
Модуль для завдання створення резервних копій бази даних.

Визначає `DatabaseBackupTask`, відповідальний за періодичне
створення резервних копій бази даних PostgreSQL.
"""

import asyncio
import logging
import os
import subprocess # Хоча ми використовуємо asyncio.create_subprocess_exec, імпорт може бути корисним для розуміння
from datetime import datetime
from typing import Any, Dict # Додано для типізації run

from app.src.tasks.base import BaseTask
# from app.src.config.settings import settings # Для доступу до налаштувань БД та шляхів

# Налаштування логера для цього модуля
logger = logging.getLogger(__name__)

# Приклад конфігурації (має бути винесено в settings)
DB_NAME = os.getenv("DB_NAME", "kudos_db")
DB_USER = os.getenv("DB_USER", "kudos_user")
DB_HOST = os.getenv("DB_HOST", "localhost") # Або IP/hostname сервера БД
DB_PORT = os.getenv("DB_PORT", "5432")
BACKUP_DIR = os.getenv("BACKUP_DIR", "/var/backups/kudos_db")
# Пароль до БД (DB_PASSWORD) має передаватися через змінну середовища PGPASSWORD.
# Наприклад, DB_PASSWORD = os.getenv("DB_PASSWORD")
# І потім в env["PGPASSWORD"] = self.db_password, якщо він є.

class DatabaseBackupTask(BaseTask):
    """
    Завдання для створення резервних копій бази даних PostgreSQL.

    Використовує утиліту `pg_dump` для створення резервної копії.
    Резервні копії зберігаються у вказаній директорії з іменем,
    що містить дату та час створення. Використовується стиснений custom format.
    """

    def __init__(self, name: str = "DatabaseBackupTask"):
        """
        Ініціалізація завдання резервного копіювання.
        """
        super().__init__(name)
        self.db_name = DB_NAME
        self.db_user = DB_USER
        self.db_host = DB_HOST
        self.db_port = DB_PORT
        self.backup_dir = BACKUP_DIR
        # self.db_password = os.getenv("DB_PASSWORD") # Рекомендовано використовувати PGPASSWORD напряму

        self.initialization_failed = False
        try:
            os.makedirs(self.backup_dir, exist_ok=True)
            self.logger.info(f"Директорія для резервних копій: {self.backup_dir}. Перевірте права на запис.")
        except OSError as e:
            self.logger.error(f"Не вдалося створити/перевірити директорію для резервних копій {self.backup_dir}: {e}", exc_info=True)
            self.initialization_failed = True # Позначаємо, що ініціалізація не вдалася


    async def _perform_backup(self) -> str:
        """
        Виконує фактичне створення резервної копії за допомогою pg_dump.
        """
        if self.initialization_failed:
            raise RuntimeError(f"Ініціалізація завдання не вдалася, неможливо створити бекап в {self.backup_dir}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Використовуємо .dump, оскільки pg_dump з --format=c створює архів у власному форматі,
        # який вже є стисненим і не потребує .gz розширення.
        backup_filename = f"{self.db_name}_backup_{timestamp}.dump"
        backup_filepath = os.path.join(self.backup_dir, backup_filename)

        self.logger.info(f"Початок створення резервної копії БД '{self.db_name}' у файл: {backup_filepath}")

        command = [
            "pg_dump",
            "-h", self.db_host,
            "-p", self.db_port,
            "-U", self.db_user,
            "-d", self.db_name,
            "--format=c", # Custom format, стиснений і підходить для pg_restore
            "--blobs",    # Включити large objects
            f"--file={backup_filepath}" # pg_dump запише напряму у файл
        ]

        # Безпека пароля: PGPASSWORD має бути встановлено в середовищі виконання процесу,
        # а не передаватися як аргумент командного рядка.
        # FastAPI/Uvicorn може запускатися з системного сервісу, де можна встановити змінні середовища.
        # Docker-контейнери також дозволяють безпечно передавати змінні середовища.
        env = os.environ.copy()
        # if self.db_password: # Якщо ви вирішили отримувати пароль з settings/env
        #     env["PGPASSWORD"] = self.db_password
        # self.logger.info(f"Використовується PGPASSWORD: {'Так' if 'PGPASSWORD' in env else 'Ні (очікується .pgpass або довірча автентифікація)'}")

        process = None # Ініціалізуємо змінну process
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                # stdout=asyncio.subprocess.PIPE, # Не потрібно, якщо pg_dump пише у файл
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            stderr_output = await process.communicate() # stdout буде None, stderr - байти помилок

            if process.returncode == 0:
                self.logger.info(f"Резервну копію успішно створено: {backup_filepath}")
                if stderr_output[1]: # stderr_output це кортеж (stdout_bytes, stderr_bytes)
                    self.logger.warning(f"Попередження від pg_dump під час створення '{backup_filepath}': {stderr_output[1].decode().strip()}")
                return backup_filepath
            else:
                error_message = stderr_output[1].decode().strip() if stderr_output[1] else f"Невідома помилка pg_dump (код: {process.returncode})."
                self.logger.error(f"Помилка під час виконання pg_dump: {error_message}")
                if os.path.exists(backup_filepath): # Видалити частковий файл, якщо він був створений
                    try:
                        os.remove(backup_filepath)
                        self.logger.info(f"Частковий файл резервної копії {backup_filepath} видалено.")
                    except OSError as e_rem:
                        self.logger.error(f"Не вдалося видалити частковий файл {backup_filepath}: {e_rem}")
                raise RuntimeError(f"pg_dump failed: {error_message}")

        except FileNotFoundError:
            self.logger.error("Команду 'pg_dump' не знайдено. Переконайтеся, що PostgreSQL client tools встановлено та доступні в PATH.")
            raise # Прокидаємо далі, щоб завдання позначилося як невдале
        except Exception as e:
            self.logger.error(f"Непередбачена помилка під час створення резервної копії: {e}", exc_info=True)
            # Додатково перевіряємо, чи файл існує і чи був процес запущений перед видаленням
            if process and process.returncode != 0 and os.path.exists(backup_filepath):
                 try:
                    os.remove(backup_filepath)
                    self.logger.info(f"Частковий/невдалий файл резервної копії {backup_filepath} видалено (через виняток).")
                 except OSError as remove_err:
                    self.logger.error(f"Не вдалося видалити частковий/невдалий файл резервної копії {backup_filepath}: {remove_err}")
            raise


    async def _cleanup_old_backups(self, keep_last_n: int = 7) -> int:
        """
        Видаляє старі резервні копії, залишаючи вказану кількість останніх.
        """
        if self.initialization_failed:
            self.logger.warning(f"Очищення старих бекапів пропущено, оскільки ініціалізація завдання не вдалася (директорія {self.backup_dir}).")
            return 0

        self.logger.info(f"Початок очищення старих резервних копій у {self.backup_dir}. Залишити {keep_last_n} останніх.")
        count_deleted = 0
        try:
            backup_files = sorted(
                [f for f in os.listdir(self.backup_dir) if f.startswith(f"{self.db_name}_backup_") and f.endswith(".dump")],
                key=lambda f: os.path.getmtime(os.path.join(self.backup_dir, f))
            )

            if len(backup_files) > keep_last_n:
                files_to_delete = backup_files[:-keep_last_n]
                for filename in files_to_delete:
                    file_path = os.path.join(self.backup_dir, filename)
                    try:
                        os.remove(file_path)
                        self.logger.info(f"Видалено стару резервну копію: {file_path}")
                        count_deleted += 1
                    except Exception as e:
                        self.logger.error(f"Помилка видалення старої резервної копії {file_path}: {e}", exc_info=True)
            else:
                self.logger.info("Немає достатньо старих резервних копій для видалення.")

        except FileNotFoundError:
            self.logger.warning(f"Директорія для резервних копій не знайдена під час очищення: {self.backup_dir}")
        except Exception as e:
            self.logger.error(f"Помилка під час очищення старих резервних копій: {e}", exc_info=True)

        self.logger.info(f"Очищення старих резервних копій завершено. Видалено: {count_deleted} файлів.")
        return count_deleted

    async def run(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Виконує створення резервної копії та очищення старих копій.
        """
        self.logger.info(f"Запуск завдання '{self.name}'...")
        results: Dict[str, Any] = {}
        start_time = asyncio.get_event_loop().time()

        try:
            if self.initialization_failed:
                 raise RuntimeError(f"Ініціалізація завдання '{self.name}' не вдалася, директорію {self.backup_dir} не вдалося підготувати.")

            backup_file_path = await self._perform_backup()
            results["backup_created"] = True
            results["backup_filepath"] = backup_file_path

            keep_backups = kwargs.get("keep_last_n_backups", 7)
            results["old_backups_deleted_count"] = await self._cleanup_old_backups(keep_last_n=keep_backups)

        except Exception as e: # Цей Exception має ловити помилки з _perform_backup та _cleanup_old_backups
            self.logger.error(f"Критична помилка під час виконання завдання '{self.name}': {e}", exc_info=False) # exc_info=False, бо вже залоговано вище
            results["backup_created"] = results.get("backup_created", False) # Зберігаємо попереднє значення, якщо є
            results["error"] = str(e)
            # Відповідно до BaseTask, ми не прокидаємо виняток тут,
            # а дозволяємо on_failure обробити його, якщо він перевизначений.
            # Якщо on_failure не обробляє його специфічно, то помилка буде залогована там.
            # Для того, щоб BaseTask.execute() викликав on_failure, виняток має бути прокинутий з run().
            raise
        finally:
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            self.logger.info(
                f"Завдання '{self.name}' завершено за {duration:.4f} секунд. "
                f"Результати: {results}"
            )
        return results # Повертаємо результати в будь-якому випадку (успіх або частковий успіх перед винятком)

# Приклад використання (можна видалити або закоментувати):
# async def main():
#     logging.basicConfig(
#         level=logging.INFO,
#         format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
#     )
#     # Переконайтесь, що змінні середовища (DB_*, BACKUP_DIR, PGPASSWORD) встановлені,
#     # або змініть константи в коді.
#     # Потрібен працюючий сервер PostgreSQL та встановлені утиліти pg_dump.
#
#     # Створення тестової директорії, якщо її немає
#     if not os.path.exists(BACKUP_DIR):
#         try:
#             os.makedirs(BACKUP_DIR)
#             logger.info(f"Створено тестову директорію для бекапів: {BACKUP_DIR}")
#         except OSError as e:
#             logger.error(f"Не вдалося створити тестову директорію {BACKUP_DIR}: {e}")
#             return # Вихід, якщо директорію не створити
#
#     try:
#         backup_task = DatabaseBackupTask()
#         # Перевірка, чи ініціалізація пройшла успішно
#         if backup_task.initialization_failed:
#             logger.error("Ініціалізація завдання резервного копіювання не вдалася. Завдання не буде виконано.")
#             return
#
#         await backup_task.execute(keep_last_n_backups=3)
#     except RuntimeError as e:
#         logger.error(f"Не вдалося виконати завдання резервного копіювання: {e}")
#     except FileNotFoundError:
#         logger.error("'pg_dump' не знайдено. Завдання не може бути виконано. Перевірте PATH та встановлення PostgreSQL client tools.")
#     except Exception as e:
#         logger.error(f"Загальна помилка під час виконання main прикладу: {e}", exc_info=True)

# if __name__ == "__main__":
#     # Приклад запуску:
#     # PGPASSWORD="your_db_password" python backend/app/src/tasks/system/backup.py
#     # Або експортуйте PGPASSWORD перед запуском.
#     # Для Windows може знадобитися: asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
#     asyncio.run(main())
