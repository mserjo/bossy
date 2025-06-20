# backend/app/src/config/logging_config.py
# -*- coding: utf-8 -*-
"""Конфігурація системи логування для додатку.

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
- `setup_logging()`: Функція для застосування конфігурації логування та повернення основного логера додатку.
- `get_logger()`: Допоміжна функція для отримання екземпляра логера з певним ім'ям.

Використання:
Функція `setup_logging()` викликається в `config/__init__.py` для налаштування
та отримання основного логера `config.logger`.
Інші модулі повинні імпортувати `logger` з `backend.app.src.config`.
"""
import logging
import logging.config
import sys
from pathlib import Path
from typing import Optional

# Імпорт settings буде зроблено всередині функцій setup_logging та get_logger

# Глобальна змінна для LOG_DIR_PATH, яка буде ініціалізована в setup_logging
LOG_DIR_PATH: Optional[Path] = None

def setup_logging() -> logging.Logger:
    """Застосовує конфігурацію логування та повертає основний логер додатку.

    Цю функцію слід викликати один раз під час запуску програми
    (наприклад, у `config/__init__.py` або `main.py` на етапі `startup`),
    щоб налаштувати систему логування для всього додатку.

    Returns:
        logging.Logger: Налаштований основний логер додатку.
    """
    from backend.app.src.config.settings import settings # Імпорт settings всередині функції
    global LOG_DIR_PATH # Оголошуємо, що будемо змінювати глобальну змінну
    LOG_DIR_PATH = settings.LOG_DIR if settings.LOG_TO_FILE else None

    # Словник конфігурації логування для `logging.config.dictConfig`
    # Визначення LOGGING_CONFIG перенесено всередину setup_logging, щоб мати доступ до settings
    LOGGING_CONFIG: dict = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(process)d - %(threadName)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "simple": {
                "format": "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(levelname)s %(name)s %(process)d %(threadName)s %(module)s %(funcName)s %(lineno)d %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default" if settings.DEBUG else "simple",
                "level": settings.LOGGING_LEVEL.upper(),
                "stream": sys.stdout,
            },
        },
        "loggers": {
            "uvicorn.error": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "fastapi": {
                "handlers": ["console"],
                "level": settings.LOGGING_LEVEL.upper(),
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": ["console"],
                "level": "INFO" if settings.ECHO_SQL else "WARNING",
                "propagate": False,
            },
            settings.PROJECT_NAME.lower(): {
                "handlers": ["console"],
                "level": settings.LOGGING_LEVEL.upper(),
                "propagate": False,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": settings.LOGGING_LEVEL.upper(),
        },
    }

    if settings.LOG_TO_FILE and LOG_DIR_PATH:
        LOG_DIR_PATH.mkdir(parents=True, exist_ok=True)
        LOGGING_CONFIG["handlers"]["app_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "level": settings.LOGGING_LEVEL.upper(),
            "filename": str(LOG_DIR_PATH / settings.LOG_APP_FILE),
            "maxBytes": settings.LOG_MAX_BYTES,
            "backupCount": settings.LOG_BACKUP_COUNT,
            "encoding": "utf-8",
        }
        LOGGING_CONFIG["handlers"]["error_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "level": "ERROR",
            "filename": str(LOG_DIR_PATH / settings.LOG_ERROR_FILE),
            "maxBytes": settings.LOG_MAX_BYTES,
            "backupCount": settings.LOG_BACKUP_COUNT,
            "encoding": "utf-8",
        }
        project_logger_name = settings.PROJECT_NAME.lower()
        if project_logger_name in LOGGING_CONFIG["loggers"]:
            LOGGING_CONFIG["loggers"][project_logger_name]["handlers"].extend(["app_file", "error_file"])
        if "root" in LOGGING_CONFIG:
            LOGGING_CONFIG["root"]["handlers"].extend(["app_file", "error_file"])

    main_app_logger_name = settings.PROJECT_NAME.lower()
    try:
        logging.config.dictConfig(LOGGING_CONFIG)
        configured_logger = logging.getLogger(main_app_logger_name)
        configured_logger.info(
            "Систему логування успішно налаштовано. Рівень: %s, Логування у файл: %s.",
            settings.LOGGING_LEVEL.upper(),
            settings.LOG_TO_FILE
        )
        if settings.LOG_TO_FILE and LOG_DIR_PATH:
            configured_logger.info("Логи програми зберігатимуться у: %s", LOG_DIR_PATH / settings.LOG_APP_FILE)
            configured_logger.info("Логи помилок програми зберігатимуться у: %s", LOG_DIR_PATH / settings.LOG_ERROR_FILE)
        return configured_logger
    except ImportError as e:
        logging.basicConfig(level=settings.LOGGING_LEVEL.upper(), format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
        logging.error(
            "Помилка імпорту при налаштуванні логування: %s. "
            "Можливо, відсутня бібліотека 'python-json-logger', якщо використовується JSON форматер. "
            "Перехід до базової конфігурації логування.", e
        )
        return logging.getLogger(main_app_logger_name)
    except Exception as e:
        logging.basicConfig(level=settings.LOGGING_LEVEL.upper(), format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
        logging.error(
            "Не вдалося застосувати конфігурацію логування через помилку: %s. "
            "Перехід до базової конфігурації логування (basicConfig).", e, exc_info=True
        )
        return logging.getLogger(main_app_logger_name)


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
    from backend.app.src.config.settings import settings # Імпорт settings всередині функції
    if name is None:
        name = settings.PROJECT_NAME.lower()
    return logging.getLogger(name)

# Приклад використання та тестування налаштувань логування
if __name__ == "__main__":
    # Потрібно імпортувати settings для тестового блоку, якщо він буде використовуватися
    # from backend.app.src.config.settings import settings # Розкоментуйте, якщо будете запускати цей файл напряму
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

    # app_logger.info(f"Це INFO повідомлення від логера програми '{settings.PROJECT_NAME.lower()}'.")
    app_logger.error(
        "Це ERROR повідомлення від логера програми. "
        "Воно повинно потрапити до error.log, якщо логування у файл увімкнено."
    )

    fastapi_logger.info("Це INFO повідомлення від логера FastAPI.")

    # # Логування SQLAlchemy залежить від DEBUG режиму
    # if settings.DEBUG:
    #     sqlalchemy_logger.info("Це INFO повідомлення від SQLAlchemy (імітація SQL-запиту в DEBUG режимі).")
    # else:
    #     sqlalchemy_logger.warning("Це WARNING від SQLAlchemy (наприклад, повільний запит, НЕ SQL-запит).")

    # Демонстрація логування винятків
    try:
        x = 1 / 0
    except ZeroDivisionError:
        # app_logger.error("Виникла помилка ділення на нуль!", exc_info=True) # Альтернативний спосіб логування трасування
        app_logger.exception("Виник виняток ZeroDivisionError! Трасування стеку буде автоматично додано.")

    app_logger.info(f"\nНалаштування логування успішно застосовано. Перевірте вивід консолі.")
    # if settings.LOG_TO_FILE and LOG_DIR_PATH:
    #     app_logger.info(f"Якщо логування у файл увімкнено, перевірте файли у директорії: {LOG_DIR_PATH.resolve()}")
    #     app_logger.info(f"  Лог програми: {LOG_DIR_PATH / settings.LOG_APP_FILE}")
    #     app_logger.info(f"  Лог помилок: {LOG_DIR_PATH / settings.LOG_ERROR_FILE}")
