# backend/app/src/config/logging.py
# -*- coding: utf-8 -*-
"""
Цей модуль відповідає за налаштування системи логування для додатку.
Використовується бібліотека `loguru` для гнучкого та потужного логування.
Налаштовуються обробники для виводу логів в консоль та, опціонально, у файли,
а також рівні логування та формати повідомлень.
"""

import sys
import logging
from typing import cast
from loguru import logger # type: ignore # Loguru не має офіційних стабів, але працює

# Імпорт налаштувань додатку для визначення рівня логування та інших параметрів
from backend.app.src.config.settings import settings # Головний об'єкт settings
from pathlib import Path # Для роботи зі шляхами

# --- Конфігурація Loguru ---

# Видаляємо стандартний обробник loguru, щоб налаштувати власні.
logger.remove(None) # Видаляє всі попередньо налаштовані обробники, якщо є

# Рівень логування з налаштувань LoggingSettings.
LOG_LEVEL = settings.logging.LOG_LEVEL.upper()

# Формат логів
# Детальний формат, що включає час, рівень, модуль, функцію, рядок та повідомлення.
# Приклад: "2023-10-27 10:00:00.123 | INFO     | my_module:my_function:12 - Log message"
# {time:YYYY-MM-DD HH:mm:ss.SSS} - час
# {level: <8} - рівень логування, вирівняний до 8 символів
# {name} - ім'я логгера (зазвичай __name__ модуля)
# {module} - ім'я модуля
# {function} - ім'я функції
# {line} - номер рядка
# {message} - повідомлення логу
# {exception} - деталі винятку, якщо є
LOG_FORMAT_DETAILED = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
# Простіший формат для production (можна налаштувати)
LOG_FORMAT_SIMPLE = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
    "{level: <8} | "
    "{message}"
)
# Обираємо формат залежно від середовища
CURRENT_LOG_FORMAT = LOG_FORMAT_DETAILED if settings.app.DEBUG else LOG_FORMAT_SIMPLE


# 1. Обробник для виводу в консоль (stdout)
logger.add(
    sys.stdout,
    level=LOG_LEVEL.upper(), # Рівень логування для цього обробника
    format=CURRENT_LOG_FORMAT,
    colorize=True, # Розфарбовування виводу в консолі
    enqueue=True, # Асинхронне логування (рекомендовано для продуктивності)
    backtrace=settings.app.DEBUG, # Виводити повний backtrace при помилках (лише в DEBUG)
    diagnose=settings.app.DEBUG  # Виводити діагностичну інформацію про змінні (лише в DEBUG)
)

# 2. Обробник для запису логів у файл (якщо увімкнено в `settings.logging`)
if settings.logging.LOG_TO_FILE_ENABLE:
    log_file_path_str = settings.logging.LOG_FILE_PATH
    log_file_path = Path(log_file_path_str)

    # Якщо шлях не абсолютний, робимо його відносним до BASE_DIR
    if not log_file_path.is_absolute():
        log_file_path = settings.app.BASE_DIR / log_file_path

    log_dir = log_file_path.parent
    log_file_created_successfully = False
    try:
        if not log_dir.exists():
            logger.info(f"Спроба створити каталог для логів: {log_dir}")
            log_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Каталог для логів створено: {log_dir}")
        log_file_created_successfully = True
    except OSError as e:
        # Використовуємо print, оскільки логгер може ще не писати у файл
        print(f"ПОМИЛКА КОНФІГУРАЦІЇ ЛОГУВАННЯ: Не вдалося створити каталог для лог-файлів '{log_dir}': {e}")
        logger.error(f"Не вдалося створити каталог для лог-файлів '{log_dir}': {e}")


    if log_file_created_successfully:
        logger.add(
            log_file_path, # Тепер це об'єкт Path
            level=settings.logging.LOG_FILE_LEVEL.upper(),
            format=LOG_FORMAT_DETAILED, # Зазвичай у файли пишуть детальні логи
            rotation=settings.logging.LOG_FILE_ROTATION,
            retention=settings.logging.LOG_FILE_RETENTION,
            compression=settings.logging.LOG_FILE_COMPRESSION,
            enqueue=True, # Асинхронне логування
            encoding="utf-8", # Явне кодування для файлу
            backtrace=settings.app.DEBUG, # Також додамо backtrace/diagnose для файлів, якщо DEBUG
            diagnose=settings.app.DEBUG
        )
        logger.info(f"Файловий логгер налаштовано. Шлях: {log_file_path}, Рівень: {settings.logging.LOG_FILE_LEVEL.upper()}")
    else:
        logger.warning(f"Файлове логування увімкнено, але не вдалося підготувати каталог. Логування у файл '{log_file_path}' не буде активовано.")

# --- Інтеграція з стандартним модулем logging (для бібліотек, що його використовують) ---
# Loguru може перехоплювати логи, згенеровані стандартним `logging`.
class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Отримуємо відповідний рівень loguru
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        # Знаходимо кадр стека, звідки був зроблений виклик логування
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__: # type: ignore
            frame = cast(Any, frame).f_back # type: ignore
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

# Налаштовуємо стандартний logging на використання InterceptHandler
# Це дозволить логам з бібліотек (наприклад, SQLAlchemy, Uvicorn, FastAPI)
# потрапляти в обробники Loguru.
# logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True) # force=True для перезапису існуючих
# Або більш гранульовано:
# logging.getLogger().handlers = [InterceptHandler()]
# logging.getLogger().setLevel(LOG_LEVEL.upper())
#
# Для Uvicorn та FastAPI, вони мають власні налаштування логування,
# які можна конфігурувати при запуску сервера.
# Можна налаштувати їх так, щоб вони використовували стандартний logging,
# який потім перехоплюється Loguru.
# Або ж Loguru може бути основним логгером, і тоді Uvicorn/FastAPI
# налаштовуються на використання кастомного класу логгера.
#
# Поки що, для простоти, основний акцент на налаштуванні Loguru для коду додатку.

# Налаштування стандартного logging для перехоплення логів з бібліотек
# (наприклад, Uvicorn, SQLAlchemy).
# Встановлюємо InterceptHandler для кореневого логера.
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

# Додатково можна налаштувати рівні для конкретних бібліотечних логерів,
# щоб зменшити кількість "шуму", якщо потрібно.
# Наприклад:
# logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO if settings.app.DEBUG else logging.WARNING)
# logging.getLogger("uvicorn.access").setLevel(logging.INFO) # Логи доступу Uvicorn
# logging.getLogger("uvicorn.error").setLevel(logging.ERROR) # Помилки Uvicorn

# Для більш тонкого налаштування логів Uvicorn, особливо форматів,
# краще використовувати кастомний `log_config` при запуску Uvicorn.
# Однак, `InterceptHandler` має перехопити їх, якщо вони використовують стандартний `logging`.

logger.info("Loguru налаштовано. Стандартні логи Python будуть перехоплюватися.")

# Приклад використання в інших модулях:
# from backend.app.src.config.logging import logger
# logger.info("Це інформаційне повідомлення.")
# logger.debug("Це повідомлення для відладки.")
# try:
#     x = 1 / 0
# except ZeroDivisionError:
#     logger.exception("Виникла помилка ділення на нуль!")

# TODO: Розглянути можливість структурованого логування (наприклад, у JSON форматі)
# для файлових логів, якщо вони будуть відправлятися в системи агрегації логів (ELK, Splunk).
# Loguru підтримує це через `serialize=True` в `logger.add()`.
# Можна додати відповідний параметр в `LoggingSettings`, наприклад, `LOG_FILE_SERIALIZE: bool = False`.
# І потім використовувати `serialize=settings.logging.LOG_FILE_SERIALIZE` для файлового обробника.

# Все готово для цього файлу.

def get_logger(name: str | None = None) -> "logger": # type: ignore
    """
    Повертає налаштований екземпляр логера Loguru.

    Args:
        name (str, optional): Ім'я логера. Якщо передано, може бути використано
                              для біндінгу до логера, хоча в поточній конфігурації
                              Loguru глобально налаштований.
                              За замовчуванням None.

    Returns:
        logger: Екземпляр логера Loguru.
    """
    if name:
        return logger.bind(name=name)
    return logger
