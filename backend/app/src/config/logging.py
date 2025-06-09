import logging
import logging.config
import os
import sys
from pathlib import Path

from backend.app.src.config.settings import settings

# --- Конфігурація логування ---

# Визначити базову директорію для логів, якщо логування у файл увімкнено
LOG_DIR = Path(settings.LOG_DIR) if settings.LOG_TO_FILE else None
if LOG_DIR:
    LOG_DIR.mkdir(parents=True, exist_ok=True) # Переконатися, що директорія логів існує

# Визначити словник конфігурації логування
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False, # Залишити існуючі логери (наприклад, з бібліотек)
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "%(asctime)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": { # Приклад JSON форматера (потребує python-json-logger, якщо не налаштовувати вручну)
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(module)s %(funcName)s %(lineno)d %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default" if settings.DEBUG else "simple",
            "level": settings.LOGGING_LEVEL.upper(),
            "stream": sys.stdout, # Використовувати sys.stdout для виводу в консоль
        },
    },
    "loggers": {
        "uvicorn.error": { # Власний логер помилок Uvicorn
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.access": { # Логер доступів Uvicorn
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "fastapi": { # Логер FastAPI
            "handlers": ["console"],
            "level": settings.LOGGING_LEVEL.upper(),
            "propagate": False,
        },
        "sqlalchemy.engine": { # Логер SQLAlchemy engine (може бути детальним)
            "handlers": ["console"],
            "level": "WARNING" if not settings.DEBUG else "INFO", # INFO в режимі DEBUG для перегляду SQL-запитів
            "propagate": False,
        },
        settings.PROJECT_NAME.lower(): { # Логер для конкретної програми
            "handlers": ["console"],
            "level": settings.LOGGING_LEVEL.upper(),
            "propagate": False, # Не поширювати на кореневий логер, якщо тут визначені обробники
        },
    },
    "root": { # Конфігурація кореневого логера
        "handlers": ["console"],
        "level": settings.LOGGING_LEVEL.upper(),
    },
}

# Додати файлові обробники, якщо LOG_TO_FILE увімкнено в налаштуваннях
if settings.LOG_TO_FILE and LOG_DIR:
    LOGGING_CONFIG["handlers"]["app_file"] = {
        "class": "logging.handlers.RotatingFileHandler",
        "formatter": "default",
        "level": settings.LOGGING_LEVEL.upper(),
        "filename": LOG_DIR / settings.LOG_APP_FILE,
        "maxBytes": settings.LOG_MAX_BYTES,
        "backupCount": settings.LOG_BACKUP_COUNT,
        "encoding": "utf-8",
    }
    LOGGING_CONFIG["handlers"]["error_file"] = {
        "class": "logging.handlers.RotatingFileHandler",
        "formatter": "default",
        "level": "ERROR", # Логувати лише рівень ERROR та вище у цей файл
        "filename": LOG_DIR / settings.LOG_ERROR_FILE,
        "maxBytes": settings.LOG_MAX_BYTES,
        "backupCount": settings.LOG_BACKUP_COUNT,
        "encoding": "utf-8",
    }
    # Додати файлові обробники до відповідних логерів
    LOGGING_CONFIG["loggers"][settings.PROJECT_NAME.lower()]["handlers"].extend(["app_file", "error_file"])
    LOGGING_CONFIG["root"]["handlers"].extend(["app_file", "error_file"])
    # Якщо ви хочете, щоб конкретні логери (наприклад, FastAPI) також логували у файли, додайте обробники і сюди
    # LOGGING_CONFIG["loggers"]["fastapi"]["handlers"].extend(["app_file", "error_file"])


def setup_logging():
    """
    Застосовує конфігурацію логування, визначену в LOGGING_CONFIG.
    Цю функцію слід викликати один раз під час запуску програми.
    """
    try:
        logging.config.dictConfig(LOGGING_CONFIG)
        logger = logging.getLogger(settings.PROJECT_NAME.lower())
        logger.info(f"Логування налаштовано. Рівень: {settings.LOGGING_LEVEL.upper()}, Логування у файл: {settings.LOG_TO_FILE}")
        if settings.LOG_TO_FILE and LOG_DIR:
            logger.info(f"Логи програми будуть зберігатися у: {LOG_DIR / settings.LOG_APP_FILE}")
            logger.info(f"Логи помилок будуть зберігатися у: {LOG_DIR / settings.LOG_ERROR_FILE}")
    except Exception as e:
        # Резервне базове логування, якщо конфігурація не вдалася
        logging.basicConfig(level=logging.INFO)
        logging.error(f"Помилка налаштування конфігурації логування: {e}. Перехід до basicConfig.")

# --- Допоміжна функція для отримання екземпляра логера ---
def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Отримує екземпляр логера, за замовчуванням основного логера проекту.

    Args:
        name (Optional[str]): Назва логера. Якщо None, використовується
                              PROJECT_NAME з налаштувань.

    Returns:
        logging.Logger: Екземпляр логера.
    """
    if name is None:
        name = settings.PROJECT_NAME.lower()
    return logging.getLogger(name)

if __name__ == "__main__":
    # Приклад використання налаштування логування
    setup_logging() # Застосувати конфігурацію

    # Отримати логери
    root_logger = get_logger("root")
    app_logger = get_logger() # Отримує логер, специфічний для проекту
    fastapi_logger = get_logger("fastapi")
    sqlalchemy_logger = get_logger("sqlalchemy.engine")

    # Залогувати кілька повідомлень
    root_logger.debug("Це налагоджувальне повідомлення від кореневого логера.")
    root_logger.info("Це інформаційне повідомлення від кореневого логера.")
    root_logger.warning("Це попереджувальне повідомлення від кореневого логера.")
    root_logger.error("Це повідомлення про помилку від кореневого логера.")
    root_logger.critical("Це критичне повідомлення від кореневого логера.")

    app_logger.info("Це інформаційне повідомлення від логера програми.")
    app_logger.error("Це помилка з програми, вона повинна потрапити до error.log, якщо увімкнено логування у файл.")

    fastapi_logger.info("Це інформаційне повідомлення від логера FastAPI.")
    if settings.DEBUG:
        sqlalchemy_logger.info("Це інформаційне повідомлення від логера SQLAlchemy (імітація логу SQL-запиту).")
    else:
        sqlalchemy_logger.warning("Це попередження від SQLAlchemy (наприклад, повільний запит), а не SQL-лог.")

    try:
        1 / 0
    except ZeroDivisionError:
        app_logger.exception("Стався виняток! Трасування буде залоговано.")

    print(f"\nНалаштування логування застосовано. Перевірте вивід консолі.")
    if settings.LOG_TO_FILE and LOG_DIR:
        print(f"Якщо логування у файл увімкнено, перевірте файли у: {LOG_DIR}")
        print(f"Лог програми: {LOG_DIR / settings.LOG_APP_FILE}")
        print(f"Лог помилок: {LOG_DIR / settings.LOG_ERROR_FILE}")
