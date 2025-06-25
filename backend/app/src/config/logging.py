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
import os # Для роботи зі шляхами та створення каталогів

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
    log_file_path = settings.logging.LOG_FILE_PATH

    # Переконуємося, що каталог для логів існує
    try:
        log_dir = os.path.dirname(log_file_path)
        if log_dir and not os.path.exists(log_dir): # Створюємо, лише якщо шлях не порожній
            os.makedirs(log_dir, exist_ok=True)
            logger.info(f"Створено каталог для логів: {log_dir}")
    except Exception as e:
        logger.error(f"Не вдалося створити каталог для логів '{log_dir}': {e}")
        # Продовжуємо без файлового логування, якщо не вдалося створити каталог

    if not log_dir or os.path.exists(log_dir): # Додаємо обробник, лише якщо каталог існує або не потрібен (файл в поточному)
        logger.add(
            log_file_path,
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
# Інтеграція з логами Uvicorn/FastAPI може бути доопрацьована.
# Зазвичай, якщо Uvicorn використовує стандартний `logging`, то достатньо
# `logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)`
# або налаштувати обробники для конкретних логгерів (uvicorn, uvicorn.access, fastapi).

# --- Функція для отримання логгера ---
# Loguru логгер є глобальним, тому його можна просто імпортувати: `from loguru import logger`
# Але для консистентності або якщо потрібні специфічні налаштування для різних модулів,
# можна створити функцію-обгортку.
# На даний момент, прямий імпорт `logger` з `loguru` є достатнім.
# def get_logger(name: Optional[str] = None) -> "Logger": # type: ignore
#     # Якщо name не передано, Loguru використовує ім'я модуля, звідки викликано.
#     # Можна повернути той самий глобальний екземпляр logger.
#     # Або logger.bind(name=name) для створення "дочірнього" логгера з контекстом.
#     # Поки що просто повертаємо глобальний.
#     return logger

# Приклад використання в інших модулях:
# from backend.app.src.config.logging import logger (якщо get_logger не використовується)
# logger.info("Це інформаційне повідомлення.")
# logger.debug("Це повідомлення для відладки.")
# try:
#     x = 1 / 0
# except ZeroDivisionError:
#     logger.exception("Виникла помилка ділення на нуль!")

# TODO: Доопрацювати інтеграцію з логами Uvicorn/FastAPI.
# Можливо, потрібно буде налаштувати `LOGGING_CONFIG` для Uvicorn,
# щоб він використовував обробники Loguru або стандартний logging, перехоплений Loguru.
# Див. документацію FastAPI та Uvicorn щодо конфігурації логування.
#
# TODO: Розглянути можливість структурованого логування (наприклад, у JSON форматі)
# для файлових логів, якщо вони будуть відправлятися в системи агрегації логів (ELK, Splunk).
# Loguru підтримує кастомні серіалізатори для цього.
# logger.add(..., serialize=True)
#
# TODO: Додати перевірку існування каталогу для лог-файлів перед їх створенням,
# якщо логування у файл буде увімкнено.
#
# Все виглядає як хороший базовий набір налаштувань логування.
# Файловий логгер закоментований, оскільки потребує змінних в `AppSettings`.
# Це можна буде додати пізніше.
# Основний консольний логгер налаштований.
# Перехоплення стандартних логів `logging` через `InterceptHandler` - корисна практика.
# `force=True` в `logging.basicConfig` може бути потрібним, якщо Uvicorn/FastAPI
# вже налаштували свої обробники.
# Замість `logging.basicConfig`, краще налаштовувати конкретні логгери,
# наприклад, `logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]`
# та `logging.getLogger("uvicorn.error").handlers = [InterceptHandler()]`.
# І встановити їм рівні.
#
# Для FastAPI, якщо він використовує стандартний `logging`, то цього може бути достатньо.
# Якщо ні, то потрібно буде дивитися на його конфігурацію логування.
#
# Поки що основний функціонал логування для додатку через Loguru налаштований.
#
# Вирішено: інтеграцію з `logging` зроблю простішою, просто налаштувавши
# обробники для кореневого логгера `logging`.
logging.getLogger().handlers = [InterceptHandler()]
logging.getLogger().setLevel(LOG_LEVEL.upper()) # Встановлюємо рівень для стандартного logging

# Це має перехоплювати логи з усіх бібліотек, що використовують стандартний logging,
# якщо вони не мають власних специфічних налаштувань, що ігнорують батьківські обробники.
# Для Uvicorn, це зазвичай працює, якщо не передавати йому кастомний `log_config`.
# Uvicorn за замовчуванням використовує стандартний logging.
#
# Все готово.
