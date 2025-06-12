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

# Абсолютний імпорт налаштувань
from backend.app.src.config.settings import settings

# --- Конфігурація логування ---

# Директорія для логів визначається та створюється в settings.py (якщо LOG_TO_FILE=True).
# Тут ми просто використовуємо шлях з settings.LOG_DIR, який вже є об'єктом Path.
LOG_DIR_PATH: Optional[Path] = settings.LOG_DIR if settings.LOG_TO_FILE else None

# Словник конфігурації логування для `logging.config.dictConfig`
LOGGING_CONFIG: dict = {
    "version": 1,
    "disable_existing_loggers": False, # Не вимикати існуючі логери (наприклад, логери встановлених бібліотек)
    "formatters": {
        "default": { # Стандартний детальний форматер
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(process)d - %(threadName)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": { # Спрощений форматер для консолі у не-DEBUG режимі
            "format": "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": { # JSON форматер для структурованого логування (потребує python-json-logger)
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(process)d %(threadName)s %(module)s %(funcName)s %(lineno)d %(message)s",
            # Додаткові поля можна додати через клас LogstashFormatter або кастомний клас.
        }
    },
    "handlers": {
        "console": { # Обробник для виводу в консоль (stdout)
            "class": "logging.StreamHandler",
            "formatter": "default" if settings.DEBUG else "simple", # Різні форматери для DEBUG та інших рівнів
            "level": settings.LOGGING_LEVEL.upper(),
            "stream": sys.stdout, # Явно вказати потік виводу (за замовчуванням sys.stderr)
        },
    },
    "loggers": { # Конфігурація для конкретних логерів
        # Логер для Uvicorn (помилки та доступ)
        "uvicorn.error": {
            "handlers": ["console"],
            "level": "INFO", # Або інший рівень за потребою
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["console"],
            "level": "INFO", # Логи доступу Uvicorn
            "propagate": False,
        },
        # Логер для FastAPI
        "fastapi": {
            "handlers": ["console"],
            "level": settings.LOGGING_LEVEL.upper(),
            "propagate": False,
        },
        # Логер для SQLAlchemy (корисний для перегляду SQL-запитів)
        "sqlalchemy.engine": {
            "handlers": ["console"],
            "level": "INFO" if settings.ECHO_SQL else "WARNING", # Використовуємо ECHO_SQL з налаштувань
            "propagate": False,
        },
        # Логер для поточної програми (назва береться з налаштувань)
        settings.PROJECT_NAME.lower(): {
            "handlers": ["console"],
            "level": settings.LOGGING_LEVEL.upper(),
            "propagate": False, # Не передавати батьківському, якщо тут є свої обробники
        },
    },
    "root": { # Конфігурація кореневого логера (ловить всі інші повідомлення, що не оброблені вище)
        "handlers": ["console"],
        "level": settings.LOGGING_LEVEL.upper(),
    },
}

# Динамічне додавання файлових обробників, якщо увімкнено логування у файл в налаштуваннях
if settings.LOG_TO_FILE and LOG_DIR_PATH:
    # Переконуємося, що директорія для логів існує (створюємо, якщо ні)
    LOG_DIR_PATH.mkdir(parents=True, exist_ok=True)

    # Файловий обробник для всіх логів програми (app_file)
    LOGGING_CONFIG["handlers"]["app_file"] = {
        "class": "logging.handlers.RotatingFileHandler", # Використання ротації файлів
        "formatter": "default", # Детальний форматер для файлів
        "level": settings.LOGGING_LEVEL.upper(),
        "filename": str(LOG_DIR_PATH / settings.LOG_APP_FILE), # Повний шлях до файлу
        "maxBytes": settings.LOG_MAX_BYTES, # Максимальний розмір файлу перед ротацією
        "backupCount": settings.LOG_BACKUP_COUNT, # Кількість збережених резервних копій
        "encoding": "utf-8",
    }
    # Файловий обробник спеціально для логів помилок (рівень ERROR та вище)
    LOGGING_CONFIG["handlers"]["error_file"] = {
        "class": "logging.handlers.RotatingFileHandler",
        "formatter": "default",
        "level": "ERROR", # Логувати тільки ERROR та CRITICAL
        "filename": str(LOG_DIR_PATH / settings.LOG_ERROR_FILE),
        "maxBytes": settings.LOG_MAX_BYTES,
        "backupCount": settings.LOG_BACKUP_COUNT,
        "encoding": "utf-8",
    }
    # Додавання файлових обробників до логера програми та кореневого логера
    # Це забезпечить, що логи програми та всі інші логи (через root) також пишуться у файли.
    project_logger_name = settings.PROJECT_NAME.lower()
    if project_logger_name in LOGGING_CONFIG["loggers"]:
        LOGGING_CONFIG["loggers"][project_logger_name]["handlers"].extend(["app_file", "error_file"])
    if "root" in LOGGING_CONFIG:
        LOGGING_CONFIG["root"]["handlers"].extend(["app_file", "error_file"])

    # Якщо потрібно, щоб логи FastAPI або SQLAlchemy також писалися у файли,
    # можна аналогічно додати "app_file" та "error_file" до їхніх обробників.
    # Наприклад:
    # if "fastapi" in LOGGING_CONFIG["loggers"]:
    #     LOGGING_CONFIG["loggers"]["fastapi"]["handlers"].extend(["app_file", "error_file"])
    # if "sqlalchemy.engine" in LOGGING_CONFIG["loggers"]:
    #     LOGGING_CONFIG["loggers"]["sqlalchemy.engine"]["handlers"].extend(["app_file"])


def setup_logging() -> logging.Logger:
    """Застосовує конфігурацію логування та повертає основний логер додатку.

    Цю функцію слід викликати один раз під час запуску програми
    (наприклад, у `config/__init__.py` або `main.py` на етапі `startup`),
    щоб налаштувати систему логування для всього додатку.

    Returns:
        logging.Logger: Налаштований основний логер додатку.
    """
    main_app_logger_name = settings.PROJECT_NAME.lower()
    try:
        logging.config.dictConfig(LOGGING_CONFIG)
        # Отримуємо основний логер програми для першого повідомлення про успішне налаштування
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
        # Якщо виникає помилка імпорту (наприклад, python-json-logger не встановлено, а форматер "json" використовується)
        logging.basicConfig(level=settings.LOGGING_LEVEL.upper(), format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
        logging.error(
            "Помилка імпорту при налаштуванні логування: %s. "
            "Можливо, відсутня бібліотека 'python-json-logger', якщо використовується JSON форматер. "
            "Перехід до базової конфігурації логування.", e
        )
        return logging.getLogger(main_app_logger_name) # Повертаємо логер з базовою конфігурацією
    except Exception as e: # pylint: disable=broad-except
        # Резервне базове логування, якщо будь-яка інша помилка конфігурації
        logging.basicConfig(level=settings.LOGGING_LEVEL.upper(), format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
        logging.error(
            "Не вдалося застосувати конфігурацію логування через помилку: %s. "
            "Перехід до базової конфігурації логування (basicConfig).", e, exc_info=True
        )
        return logging.getLogger(main_app_logger_name) # Повертаємо логер з базовою конфігурацією


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

    app_logger.info(f"\nНалаштування логування успішно застосовано. Перевірте вивід консолі.")
    if settings.LOG_TO_FILE and LOG_DIR_PATH:
        app_logger.info(f"Якщо логування у файл увімкнено, перевірте файли у директорії: {LOG_DIR_PATH.resolve()}")
        app_logger.info(f"  Лог програми: {LOG_DIR_PATH / settings.LOG_APP_FILE}")
        app_logger.info(f"  Лог помилок: {LOG_DIR_PATH / settings.LOG_ERROR_FILE}")
