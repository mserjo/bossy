# /backend/app/src/config/logging.py
"""
Конфігурація системи логування для FastAPI програми Kudos.

Цей модуль налаштовує логування на основі параметрів, визначених у `settings.py`.
Він підтримує:
- Різні рівні логування (DEBUG, INFO, WARNING, ERROR, CRITICAL).
- Форматування повідомлень логів для читабельності.
- Виведення логів у консоль (stdout).
- Опціональне збереження логів у файли (окремі файли для всіх логів програми та для помилок).
- Ротацію файлів логів для запобігання їх надмірному зростанню.
- Налаштування логерів для основних компонентів: Uvicorn, FastAPI, SQLAlchemy та самої програми.
- Можливість використання JSON-форматера для логів (потребує `python-json-logger`).

Основні компоненти:
- `LOGGING_CONFIG`: Словник конфігурації для `logging.config.dictConfig`.
- `setup_logging()`: Функція для застосування конфігурації логування.
- `get_logger()`: Допоміжна функція для отримання екземпляра логера.

Використання:
Функцію `setup_logging()` слід викликати один раз при старті програми (наприклад, у `main.py`).
Функція `get_logger(name)` використовується в інших модулях для отримання логера.
"""
import logging
import logging.config
import sys
from pathlib import Path # Використовується для роботи зі шляхами
from typing import Optional # Для типізації аргументу name в get_logger

from backend.app.src.config.settings import settings

# --- Конфігурація логування ---

# Директорія для логів визначається та створюється в settings.py.
# Тут ми просто використовуємо шлях з settings.LOG_DIR, який вже є об'єктом Path.
LOG_DIR_PATH: Optional[Path] = settings.LOG_DIR if settings.LOG_TO_FILE else None

# Словник конфігурації логування для logging.config.dictConfig
LOGGING_CONFIG: dict = {
    "version": 1, # Версія схеми конфігурації
    "disable_existing_loggers": False, # Не вимикати існуючі логери (наприклад, логери бібліотек)
    "formatters": { # Визначення форматерів для повідомлень логів
        "default": { # Стандартний детальний форматер
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(process)d - %(threadName)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S", # Формат дати та часу
        },
        "simple": { # Спрощений форматер для менш детального виводу (наприклад, для продакшен консолі)
            "format": "%(asctime)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": { # JSON форматер для структурованого логування.
                  # ПОТРЕБУЄ ВСТАНОВЛЕНОЇ БІБЛІОТЕКИ: python-json-logger
                  # Якщо бібліотека не встановлена, цей форматер не буде працювати
                  # і може викликати помилку при спробі його використання.
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(process)d %(threadName)s %(module)s %(funcName)s %(lineno)d %(message)s"
            # Додаткові поля можна додати через клас LogstashFormatter, якщо потрібно.
        }
    },
    "handlers": { # Обробники логів (куди направляти повідомлення)
        "console": { # Обробник для виводу в консоль (stdout)
            "class": "logging.StreamHandler",
            # Використовувати детальний форматер, якщо DEBUG=True, інакше спрощений
            "formatter": "default" if settings.DEBUG else "simple",
            "level": settings.LOGGING_LEVEL.upper(), # Рівень логування з налаштувань
            "stream": sys.stdout, # Явно вказати потік виводу
        },
    },
    "loggers": { # Конфігурація для конкретних логерів
        "uvicorn.error": { # Логер помилок Uvicorn
            "handlers": ["console"], # Направляти в консоль
            "level": "INFO", # Рівень для логера Uvicorn
            "propagate": False, # Не передавати повідомлення батьківському логеру
        },
        "uvicorn.access": { # Логер доступів Uvicorn (запитів)
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "fastapi": { # Логер FastAPI
            "handlers": ["console"],
            "level": settings.LOGGING_LEVEL.upper(),
            "propagate": False,
        },
        "sqlalchemy.engine": { # Логер SQLAlchemy (корисний для перегляду SQL-запитів)
            "handlers": ["console"],
            # В режимі DEBUG логувати SQL-запити (INFO), інакше тільки WARNING та вище
            "level": "INFO" if settings.DEBUG else "WARNING",
            "propagate": False,
        },
        # Логер для поточної програми, назва береться з налаштувань
        settings.PROJECT_NAME.lower(): {
            "handlers": ["console"],
            "level": settings.LOGGING_LEVEL.upper(),
            "propagate": False, # Якщо тут є обробники, не передавати батьківському
        },
    },
    "root": { # Конфігурація кореневого логера (ловить всі інші повідомлення)
        "handlers": ["console"], # За замовчуванням направляти в консоль
        "level": settings.LOGGING_LEVEL.upper(), # Рівень з налаштувань
    },
}

# Динамічне додавання файлових обробників, якщо увімкнено логування у файл
if settings.LOG_TO_FILE and LOG_DIR_PATH:
    # Файловий обробник для всіх логів програми
    LOGGING_CONFIG["handlers"]["app_file"] = {
        "class": "logging.handlers.RotatingFileHandler", # Ротація файлів
        "formatter": "default", # Використовувати детальний форматер
        "level": settings.LOGGING_LEVEL.upper(),
        "filename": LOG_DIR_PATH / settings.LOG_APP_FILE, # Повний шлях до файлу
        "maxBytes": settings.LOG_MAX_BYTES, # Максимальний розмір файлу перед ротацією
        "backupCount": settings.LOG_BACKUP_COUNT, # Кількість резервних копій
        "encoding": "utf-8", # Кодування файлу
    }
    # Файловий обробник спеціально для логів помилок (рівень ERROR та вище)
    LOGGING_CONFIG["handlers"]["error_file"] = {
        "class": "logging.handlers.RotatingFileHandler",
        "formatter": "default",
        "level": "ERROR", # Логувати тільки ERROR та CRITICAL
        "filename": LOG_DIR_PATH / settings.LOG_ERROR_FILE,
        "maxBytes": settings.LOG_MAX_BYTES,
        "backupCount": settings.LOG_BACKUP_COUNT,
        "encoding": "utf-8",
    }
    # Додавання файлових обробників до логера програми та кореневого логера
    LOGGING_CONFIG["loggers"][settings.PROJECT_NAME.lower()]["handlers"].extend(["app_file", "error_file"])
    LOGGING_CONFIG["root"]["handlers"].extend(["app_file", "error_file"])

    # Приклад: якщо потрібно, щоб FastAPI також логував у файли:
    # if "fastapi" in LOGGING_CONFIG["loggers"]:
    #     LOGGING_CONFIG["loggers"]["fastapi"]["handlers"].extend(["app_file", "error_file"])


def setup_logging():
    """
    Застосовує конфігурацію логування, визначену в `LOGGING_CONFIG`.

    Цю функцію слід викликати один раз під час запуску програми (наприклад, у `main.py`
    або в обробнику події `startup` FastAPI), щоб налаштувати систему логування.
    """
    try:
        logging.config.dictConfig(LOGGING_CONFIG)
        # Отримуємо логер програми для першого повідомлення про успішне налаштування
        logger = logging.getLogger(settings.PROJECT_NAME.lower())
        logger.info(
            f"Систему логування налаштовано. Рівень: {settings.LOGGING_LEVEL.upper()}, "
            f"Логування у файл: {settings.LOG_TO_FILE}"
        )
        if settings.LOG_TO_FILE and LOG_DIR_PATH:
            logger.info(f"Логи програми зберігатимуться у: {LOG_DIR_PATH / settings.LOG_APP_FILE}")
            logger.info(f"Логи помилок програми зберігатимуться у: {LOG_DIR_PATH / settings.LOG_ERROR_FILE}")
    except ImportError as e:
        # Якщо виникає помилка імпорту (наприклад, python-json-logger не встановлено)
        logging.basicConfig(level=settings.LOGGING_LEVEL.upper(), format="%(asctime)s - %(levelname)s - %(message)s")
        logging.error(f"Помилка імпорту при налаштуванні логування: {e}. Можливо, відсутня бібліотека 'python-json-logger'. Перехід до базової конфігурації.")
    except Exception as e:
        # Резервне базове логування, якщо будь-яка інша помилка конфігурації
        logging.basicConfig(level=settings.LOGGING_LEVEL.upper(), format="%(asctime)s - %(levelname)s - %(message)s")
        logging.error(f"Не вдалося налаштувати конфігурацію логування: {e}. Перехід до базової конфігурації (basicConfig).")

# --- Допоміжна функція для отримання екземпляра логера ---
def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Отримує екземпляр логера.

    Якщо `name` не вказано, повертає основний логер програми,
    визначений як `settings.PROJECT_NAME`.

    Args:
        name (Optional[str]): Назва логера. Якщо `None`, використовується
                              назва проекту з `settings.PROJECT_NAME`.

    Returns:
        logging.Logger: Екземпляр логера `logging.Logger`.
    """
    if name is None:
        # Використовувати назву проекту з налаштувань, переведену в нижній регістр
        name = settings.PROJECT_NAME.lower()
    return logging.getLogger(name)

# Приклад використання та тестування налаштувань логування
if __name__ == "__main__":
    # Для тестування, спочатку застосовуємо конфігурацію
    setup_logging()

    # Отримання різних логерів
    root_logger = get_logger("root") # Кореневий логер
    app_logger = get_logger() # Логер програми (використовує settings.PROJECT_NAME)
    fastapi_logger = get_logger("fastapi") # Логер FastAPI
    sqlalchemy_logger = get_logger("sqlalchemy.engine") # Логер SQLAlchemy

    # Демонстрація логування повідомлень різного рівня
    root_logger.debug("Це DEBUG повідомлення від кореневого логера.")
    root_logger.info("Це INFO повідомлення від кореневого логера.")
    root_logger.warning("Це WARNING повідомлення від кореневого логера.")
    root_logger.error("Це ERROR повідомлення від кореневого логера.")
    root_logger.critical("Це CRITICAL повідомлення від кореневого логера.")

    app_logger.info(f"Це INFO повідомлення від логера програми '{settings.PROJECT_NAME.lower()}'.")
    app_logger.error(
        "Це ERROR повідомлення від логера програми. "
        "Воно повинно потрапити до error.log, якщо логування у файл увімкнено."
    )

    fastapi_logger.info("Це INFO повідомлення від логера FastAPI.")

    # Логування SQLAlchemy залежить від DEBUG режиму
    if settings.DEBUG:
        sqlalchemy_logger.info("Це INFO повідомлення від SQLAlchemy (імітація SQL-запиту в DEBUG режимі).")
    else:
        sqlalchemy_logger.warning("Це WARNING від SQLAlchemy (наприклад, повільний запит, НЕ SQL-запит).")

    # Демонстрація логування винятків
    try:
        x = 1 / 0
    except ZeroDivisionError:
        # app_logger.error("Виникла помилка ділення на нуль!", exc_info=True) # Альтернативний спосіб логування трасування
        app_logger.exception("Виник виняток ZeroDivisionError! Трасування стеку буде автоматично додано.")

    print(f"\nНалаштування логування успішно застосовано. Перевірте вивід консолі.")
    if settings.LOG_TO_FILE and LOG_DIR_PATH:
        print(f"Якщо логування у файл увімкнено, перевірте файли у директорії: {LOG_DIR_PATH.resolve()}")
        print(f"  Лог програми: {LOG_DIR_PATH / settings.LOG_APP_FILE}")
        print(f"  Лог помилок: {LOG_DIR_PATH / settings.LOG_ERROR_FILE}")
