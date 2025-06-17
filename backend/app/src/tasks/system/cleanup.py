# backend/app/src/tasks/system/cleanup.py
# -*- coding: utf-8 -*-
"""
Модуль для завдання очищення системи.

Визначає `CleanupTask`, відповідальний за періодичне видалення
застарілих даних, тимчасових файлів, старих логів, неактивних сесій
та інших об'єктів, що потребують очищення для підтримки
продуктивності та вільного місця в системі.
"""

import asyncio
import os
import shutil
import time
from datetime import datetime, timedelta
from typing import Any, Dict

from app.src.tasks.base import BaseTask
# from app.src.config.settings import settings # Для доступу до шляхів, налаштувань зберігання
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Приклад конфігурації шляхів (має бути винесено в settings)
TEMP_FILES_DIR = "/tmp/kudos_temp_files"
OLD_LOGS_DIR = "/var/log/kudos_app_logs"
MAX_LOG_AGE_DAYS = 30
MAX_TEMP_FILE_AGE_SECONDS = 24 * 60 * 60 # 1 день

class CleanupTask(BaseTask):
    """
    Завдання для періодичного очищення системи.

    Виконує такі операції:
    - Видалення застарілих тимчасових файлів.
    - Видалення старих файлів логів.
    - (Потенційно) Очищення старих сесій з бази даних або кешу.
    - (Потенційно) Видалення "м'яко видалених" записів з БД, що перевищили термін зберігання.
    """

    def __init__(self, name: str = "SystemCleanupTask"):
        """
        Ініціалізація завдання очищення.
        """
        super().__init__(name)
        # Ініціалізація шляхів та параметрів може відбуватися тут,
        # бажано отримуючи їх з конфігурації (settings)
        self.temp_dir = TEMP_FILES_DIR # settings.TEMP_DIR
        self.logs_dir = OLD_LOGS_DIR # settings.LOGS_DIR
        self.max_log_age = timedelta(days=MAX_LOG_AGE_DAYS) # settings.MAX_LOG_AGE_DAYS
        self.max_temp_file_age = timedelta(seconds=MAX_TEMP_FILE_AGE_SECONDS) # settings.MAX_TEMP_FILE_AGE_SECONDS

        # Створення директорій, якщо вони не існують (для демонстрації)
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        # Створення кількох тестових файлів (для демонстрації)
        # У реальному сценарії ці файли будуть створюватися додатком
        try:
            # Створення старого тимчасового файлу
            old_temp_file_path = os.path.join(self.temp_dir, "old_temp_file.tmp")
            with open(old_temp_file_path, "w") as f:
                f.write("some old temp data")
            old_time = time.time() - self.max_temp_file_age.total_seconds() * 2
            os.utime(old_temp_file_path, (old_time, old_time))

            # Створення актуального тимчасового файлу
            current_temp_file_path = os.path.join(self.temp_dir, "current_temp_file.tmp")
            with open(current_temp_file_path, "w") as f:
                f.write("some current temp data")

            # Створення старого лог-файлу
            old_log_file_path = os.path.join(self.logs_dir, "app-2023-01-01.log")
            with open(old_log_file_path, "w") as f:
                f.write("old log content")
            log_old_time = (datetime.now() - timedelta(days=self.max_log_age.days * 2)).timestamp()
            os.utime(old_log_file_path, (log_old_time, log_old_time))

            # Створення актуального лог-файлу
            current_log_file_path = os.path.join(self.logs_dir, f"app-{datetime.now().strftime('%Y-%m-%d')}.log")
            with open(current_log_file_path, "w") as f:
                f.write("current log content")
        except OSError as e:
            self.logger.warning(f"Не вдалося створити тестові файли/директорії для демонстрації: {e}")


    async def _cleanup_temp_files(self) -> int:
        """
        Видаляє застарілі тимчасові файли.
        """
        count_deleted = 0
        self.logger.info(f"Початок очищення тимчасових файлів у директорії: {self.temp_dir}")
        now = time.time()
        try:
            for filename in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        file_mod_time = os.path.getmtime(file_path)
                        if (now - file_mod_time) > self.max_temp_file_age.total_seconds():
                            os.remove(file_path)
                            self.logger.info(f"Видалено застарілий тимчасовий файл: {file_path}")
                            count_deleted += 1
                    elif os.path.isdir(file_path):
                        # Можна додати логіку для рекурсивного очищення піддиректорій
                        # або видалення порожніх піддиректорій
                        pass
                except Exception as e:
                    self.logger.error(f"Помилка видалення тимчасового файлу {file_path}: {e}", exc_info=True)
        except FileNotFoundError:
            self.logger.warning(f"Директорія для тимчасових файлів не знайдена: {self.temp_dir}")
        except Exception as e:
            self.logger.error(f"Помилка доступу до директорії тимчасових файлів {self.temp_dir}: {e}", exc_info=True)

        self.logger.info(f"Очищення тимчасових файлів завершено. Видалено: {count_deleted} файлів.")
        return count_deleted

    async def _cleanup_old_logs(self) -> int:
        """
        Видаляє старі файли логів.
        """
        count_deleted = 0
        self.logger.info(f"Початок очищення старих логів у директорії: {self.logs_dir}")
        cutoff_date = datetime.now() - self.max_log_age
        try:
            for filename in os.listdir(self.logs_dir):
                file_path = os.path.join(self.logs_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if file_mod_time < cutoff_date:
                            os.remove(file_path)
                            self.logger.info(f"Видалено старий файл логу: {file_path} (дата модифікації: {file_mod_time})")
                            count_deleted += 1
                except Exception as e:
                    self.logger.error(f"Помилка видалення файлу логу {file_path}: {e}", exc_info=True)
        except FileNotFoundError:
            self.logger.warning(f"Директорія для файлів логів не знайдена: {self.logs_dir}")
        except Exception as e:
            self.logger.error(f"Помилка доступу до директорії логів {self.logs_dir}: {e}", exc_info=True)

        self.logger.info(f"Очищення старих логів завершено. Видалено: {count_deleted} файлів.")
        return count_deleted

    async def _cleanup_stale_sessions(self) -> int:
        """
        Заглушка для очищення старих сесій (наприклад, з Redis або БД).
        Потребує конкретної реалізації залежно від способу зберігання сесій.
        """
        self.logger.info("Перевірка застарілих сесій (заглушка)...")
        # Приклад:
        # count_deleted = await session_service.delete_expired_sessions()
        # self.logger.info(f"Видалено {count_deleted} застарілих сесій.")
        await asyncio.sleep(0.1) # Імітація роботи
        return 0

    async def _cleanup_soft_deleted_records(self) -> int:
        """
        Заглушка для остаточного видалення "м'яко видалених" записів з БД.
        Потребує реалізації з використанням репозиторіїв.
        """
        self.logger.info("Перевірка 'м'яко видалених' записів для остаточного видалення (заглушка)...")
        # Приклад:
        # count_deleted = 0
        # for repository in [user_repo, group_repo, task_repo]:
        #     count_deleted += await repository.permanently_delete_old_soft_deleted(older_than_days=90)
        # self.logger.info(f"Остаточно видалено {count_deleted} 'м'яко видалених' записів.")
        await asyncio.sleep(0.1) # Імітація роботи
        return 0

    async def run(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Виконує всі операції очищення.
        """
        self.logger.info(f"Запуск завдання '{self.name}'...")
        results: Dict[str, Any] = {} # Явна анотація типу
        start_time = time.perf_counter()

        try:
            results["temp_files_deleted"] = await self._cleanup_temp_files()
            results["old_logs_deleted"] = await self._cleanup_old_logs()
            results["stale_sessions_deleted"] = await self._cleanup_stale_sessions() # Заглушка
            results["soft_deleted_records_purged"] = await self._cleanup_soft_deleted_records() # Заглушка

            # Можна додати інші кроки очищення тут
            # Наприклад, очищення кешу, якщо він не має власного механізму TTL

        except Exception as e:
            self.logger.error(f"Критична помилка під час виконання завдання '{self.name}': {e}", exc_info=True)
            # Повертаємо часткові результати, якщо вони є, та інформацію про помилку
            results["error"] = str(e)
            # Не перериваємо finally, тому повертаємо тут або дозволяємо finally завершитися
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time
            self.logger.info(
                f"Завдання '{self.name}' завершено за {duration:.4f} секунд. "
                f"Результати: {results}"
            )

        return results

# # Приклад використання (можна видалити або закоментувати):
# # async def main():
# #     logging.basicConfig(
# #         level=logging.INFO,
# #         format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# #     )
# #     # Перед запуском завдання, переконайтеся, що директорії існують
# #     # os.makedirs(TEMP_FILES_DIR, exist_ok=True)
# #     # os.makedirs(OLD_LOGS_DIR, exist_ok=True)
# #     cleanup_task = CleanupTask()
# #     await cleanup_task.execute()
# #
# # if __name__ == "__main__":
# #     # Потрібно налаштувати event loop для Windows, якщо запускається напряму
# #     # if os.name == 'nt':
# #     # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# #     asyncio.run(main())
