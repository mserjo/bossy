# backend/app/src/config/logging.py
# -*- coding: utf-8 -*-
# # Модуль конфігурації системи логування для FastAPI програми Kudos (Virtus).
# #
# # Відповідає за налаштування логування на основі параметрів, визначених у
# # `backend.app.src.config.settings.settings`. Підтримує різні рівні логування,
# # форматування повідомлень, виведення в консоль, збереження у файли з ротацією,
# # а також опціональний JSON-формат. Налаштовує логери для Uvicorn, FastAPI,
# # SQLAlchemy та основного логера програми.
# #
# # Основні компоненти:
# # - `LOGGING_CONFIG`: Словник конфігурації для `logging.config.dictConfig`.
# # - `setup_logging()`: Функція для застосування конфігурації логування.
# # - `get_logger()`: Допоміжна функція для отримання екземпляра логера.

import logging
import logging.config # Необхідно для dictConfig
import sys # Для sys.stdout
from pathlib import Path # Використовується для роботи зі шляхами
from typing import Optional # Для типізації аргументу name в get_logger

# Абсолютний імпорт налаштувань програми
from backend.app.src.config.settings import settings

# --- Конфігурація логування ---

# Директорія для логів визначається та створюється в settings.py, якщо LOG_TO_FILE=True.
# Тут ми просто використовуємо шлях з settings.LOG_DIR, який вже є об'єктом Path.
LOG_DIR_PATH: Optional[Path] = settings.LOG_DIR if settings.LOG_TO_FILE else None

# Словник конфігурації логування для `logging.config.dictConfig`.
# Ця структура дозволяє гнучко налаштувати всі аспекти системи логування.
LOGGING_CONFIG: dict = {
    "version": 1, # Версія схеми конфігурації (на даний момент завжди 1)
    "disable_existing_loggers": False, # False - не вимикати існуючі логери, які могли бути налаштовані бібліотеками.
                                       # True - вимкнути всі існуючі логери перед застосуванням цієї конфігурації.
                                       # Зазвичай False є безпечнішим вибором.
    "formatters": { # Визначення форматерів для повідомлень логів
        "default": { # Стандартний детальний форматер
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(process)d - %(threadName)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S", # Формат дати та часу
        },
        "simple": { # Спрощений форматер для менш детального виводу (наприклад, для продакшен консолі)
            "format": "%(asctime)s - %(levelname)s - [%(name)s] - %(message)s", # Додано %(name)s для кращої ідентифікації джерела
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": { # JSON форматер для структурованого логування.
                  # ПОТРЕБУЄ ВСТАНОВЛЕНОЇ БІБЛІОТЕКИ: `pip install python-json-logger`
                  # Якщо бібліотека не встановлена, цей форматер не буде працювати
                  # і може викликати помилку при спробі його використання.
                  # Для використання JSON логування, змініть форматер для обробників (напр., 'console') на 'json'.
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter", # Вказує клас форматера
            "format": "%(asctime)s %(levelname)s %(name)s %(process)d %(threadName)s %(module)s %(funcName)s %(lineno)d %(message)s"
            # Можна додати інші поля або налаштувати `rename_fields` для відповідності Logstash тощо.
        }
    },
    "handlers": { # Обробники логів (визначають, куди направляти повідомлення логів)
        "console": { # Обробник для виводу в консоль (stdout)
            "class": "logging.StreamHandler", # Стандартний обробник для потоків
            # Використовувати детальний форматер ("default"), якщо DEBUG=True в налаштуваннях,
            # інакше використовувати спрощений форматер ("simple").
            "formatter": "default" if settings.DEBUG else "simple",
            "level": settings.LOGGING_LEVEL.upper(), # Рівень логування з налаштувань (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            "stream": sys.stdout, # Явно вказати потік виводу (можна також sys.stderr для помилок)
        },
    },
    "loggers": { # Конфігурація для конкретних логерів (за назвою)
        # Логери для Uvicorn. Важливо налаштувати їх, щоб логи Uvicorn відповідали загальному стилю.
        "uvicorn.error": { # Логер помилок Uvicorn (наприклад, помилки при старті сервера)
            "handlers": ["console"], # Направляти в консоль (та у файли, якщо увімкнено нижче)
            "level": "INFO", # Рівень для логера Uvicorn (можна змінити на WARNING для менш детального виводу)
            "propagate": False, # Не передавати повідомлення батьківському логеру (root), оскільки ми їх обробляємо тут.
        },
        "uvicorn.access": { # Логер доступів Uvicorn (HTTP запитів)
            "handlers": ["console"], # Направляти в консоль
            "level": "INFO", # Зазвичай INFO, можна WARNING для зменшення об'єму логів
            "propagate": False,
        },
        "fastapi": { # Логер для повідомлень від самої бібліотеки FastAPI
            "handlers": ["console"],
            "level": settings.LOGGING_LEVEL.upper(), # Використовувати загальний рівень логування
            "propagate": False,
        },
        "sqlalchemy.engine": { # Логер SQLAlchemy (корисний для перегляду SQL-запитів у режимі DEBUG)
            "handlers": ["console"],
            # В режимі DEBUG логувати SQL-запити (рівень INFO), інакше тільки WARNING та вище.
            "level": "INFO" if settings.DEBUG else "WARNING",
            "propagate": False,
        },
        # Логер для поточної програми. Назва логера береться з `settings.PROJECT_NAME`
        # (переведена в нижній регістр), щоб забезпечити консистентність.
        settings.PROJECT_NAME.lower(): {
            "handlers": ["console"], # За замовчуванням виводити в консоль
            "level": settings.LOGGING_LEVEL.upper(), # Використовувати загальний рівень логування
            "propagate": False, # Якщо тут є обробники, не передавати повідомлення батьківському (root) логеру.
        },
    },
    "root": { # Конфігурація кореневого логера (ловить всі інші повідомлення, для яких не налаштовано окремий логер)
        "handlers": ["console"], # За замовчуванням направляти в консоль
        "level": settings.LOGGING_LEVEL.upper(), # Використовувати загальний рівень логування
    },
}

# Динамічне додавання файлових обробників, якщо увімкнено логування у файл (`settings.LOG_TO_FILE` == True)
if settings.LOG_TO_FILE and LOG_DIR_PATH:
    # Файловий обробник для всіх логів програми (з ротацією)
    LOGGING_CONFIG["handlers"]["app_file_rotating"] = { # Змінено назву для уникнення конфлікту, якщо б був інший "app_file"
        "class": "logging.handlers.RotatingFileHandler", # Використовує ротацію файлів за розміром
        "formatter": "default", # Використовувати детальний форматер для файлів
        "level": settings.LOGGING_LEVEL.upper(),
        "filename": str(LOG_DIR_PATH / settings.LOG_APP_FILE), # Повний шлях до файлу логів програми
        "maxBytes": settings.LOG_MAX_BYTES, # Максимальний розмір файлу перед ротацією
        "backupCount": settings.LOG_BACKUP_COUNT, # Кількість резервних копій файлів логів
        "encoding": "utf-8", # Кодування файлу логів
    }
    # Файловий обробник спеціально для логів помилок (рівень ERROR та вище, з ротацією)
    LOGGING_CONFIG["handlers"]["error_file_rotating"] = { # Змінено назву
        "class": "logging.handlers.RotatingFileHandler",
        "formatter": "default",
        "level": "ERROR", # Логувати тільки повідомлення рівня ERROR та CRITICAL
        "filename": str(LOG_DIR_PATH / settings.LOG_ERROR_FILE), # Повний шлях до файлу логів помилок
        "maxBytes": settings.LOG_MAX_BYTES,
        "backupCount": settings.LOG_BACKUP_COUNT,
        "encoding": "utf-8",
    }
    # Додавання файлових обробників до логера програми та кореневого логера
    # Це гарантує, що повідомлення від програми та будь-які інші неперехоплені повідомлення
    # також потраплять у відповідні файли.
    app_logger_name = settings.PROJECT_NAME.lower()
    if app_logger_name in LOGGING_CONFIG["loggers"]:
        LOGGING_CONFIG["loggers"][app_logger_name]["handlers"].extend(["app_file_rotating", "error_file_rotating"])
    if "root" in LOGGING_CONFIG:
        LOGGING_CONFIG["root"]["handlers"].extend(["app_file_rotating", "error_file_rotating"])

    # Приклад: якщо потрібно, щоб логи Uvicorn або FastAPI також писалися у файли:
    # if "uvicorn.error" in LOGGING_CONFIG["loggers"]:
    #     LOGGING_CONFIG["loggers"]["uvicorn.error"]["handlers"].extend(["app_file_rotating", "error_file_rotating"])
    # if "fastapi" in LOGGING_CONFIG["loggers"]:
    #     LOGGING_CONFIG["loggers"]["fastapi"]["handlers"].extend(["app_file_rotating", "error_file_rotating"])


def setup_logging():
    """
    Застосовує конфігурацію логування, визначену в `LOGGING_CONFIG`.

    Цю функцію слід викликати один раз під час запуску програми (наприклад, у `main.py`
    або в обробнику події `startup` FastAPI), щоб налаштувати систему логування для всього додатку.
    """
    try:
        logging.config.dictConfig(LOGGING_CONFIG)
        # Отримуємо логер програми для першого повідомлення про успішне налаштування
        # Використовуємо logging.getLogger напряму, оскільки наш get_logger може залежати від вже налаштованої системи.
        logger = logging.getLogger(settings.PROJECT_NAME.lower())
        logger.info(
            f"Систему логування успішно налаштовано. Рівень: {settings.LOGGING_LEVEL.upper()}, "
            f"Логування у файл: {settings.LOG_TO_FILE}."
        )
        if settings.LOG_TO_FILE and LOG_DIR_PATH:
            logger.info(f"Логи програми зберігатимуться у: {LOG_DIR_PATH / settings.LOG_APP_FILE}")
            logger.info(f"Логи помилок програми зберігатимуться у: {LOG_DIR_PATH / settings.LOG_ERROR_FILE}")
    except ImportError as e:
        # Якщо виникає помилка імпорту (наприклад, python-json-logger не встановлено, а форматер 'json' використовується)
        logging.basicConfig(level=settings.LOGGING_LEVEL.upper(), format="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s")
        logging.error(f"Помилка імпорту при налаштуванні логування: {e}. Можливо, відсутня необхідна бібліотека (наприклад, 'python-json-logger' для JSON форматера). Перехід до базової конфігурації логування.")
    except Exception as e:
        # Резервне базове логування, якщо виникає будь-яка інша помилка під час конфігурації dictConfig.
        logging.basicConfig(level=settings.LOGGING_LEVEL.upper(), format="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s")
        logging.error(f"Не вдалося налаштувати конфігурацію логування через dictConfig: {e}. Перехід до базової конфігурації (basicConfig).")

# --- Допоміжна функція для отримання екземпляра логера ---
def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Отримує екземпляр логера `logging.Logger`.

    Якщо `name` не вказано (або `None`), повертає основний логер програми,
    назва якого визначається `settings.PROJECT_NAME` (в нижньому регістрі).
    Це дозволяє централізовано керувати назвою основного логера програми.

    Args:
        name (Optional[str]): Назва логера. Якщо `None`, використовується
                              назва проекту з `settings.PROJECT_NAME`.

    Returns:
        logging.Logger: Екземпляр логера `logging.Logger`.
    """
    if name is None:
        # Використовувати назву проекту з налаштувань, переведену в нижній регістр, як назву основного логера.
        name = settings.PROJECT_NAME.lower()
    return logging.getLogger(name)

# Приклад використання та тестування налаштувань логування
# Цей блок виконується, якщо файл запускається напряму (наприклад, `python logging.py`).
if __name__ == "__main__":
    # Для тестування, спочатку застосовуємо конфігурацію логування.
    # У реальному додатку це робиться один раз при старті.
    setup_logging()

    # Отримання різних логерів для демонстрації
    # Кореневий логер (якщо потрібно логувати щось, що не має специфічного логера)
    root_logger = get_logger("root_test") # Даємо унікальне ім'я, щоб не конфліктувати з налаштуваннями root
    # Логер поточної програми (назва береться з settings.PROJECT_NAME)
    app_logger = get_logger() # Еквівалентно get_logger(settings.PROJECT_NAME.lower())
    # Логер для FastAPI (якщо потрібно логувати щось специфічне для FastAPI з цього місця)
    fastapi_logger = get_logger("fastapi_test") # Унікальне ім'я для тесту
    # Логер для SQLAlchemy (для імітації логування SQL-запитів)
    sqlalchemy_logger = get_logger("sqlalchemy.engine_test") # Унікальне ім'я для тесту

    # Демонстрація логування повідомлень різного рівня
    root_logger.debug("Це DEBUG повідомлення від тестового 'root_test' логера.")
    root_logger.info("Це INFO повідомлення від тестового 'root_test' логера.")
    root_logger.warning("Це WARNING повідомлення від тестового 'root_test' логера.")
    root_logger.error("Це ERROR повідомлення від тестового 'root_test' логера.")
    root_logger.critical("Це CRITICAL повідомлення від тестового 'root_test' логера.")

    app_logger.info(f"Це INFO повідомлення від логера програми '{app_logger.name}'.")
    app_logger.error(
        f"Це ERROR повідомлення від логера програми '{app_logger.name}'. "
        "Воно повинно потрапити до error_file_rotating (якщо логування у файл увімкнено)."
    )

    fastapi_logger.info(f"Це INFO повідомлення від тестового логера '{fastapi_logger.name}'.")

    # Логування SQLAlchemy залежить від DEBUG режиму в налаштуваннях `LOGGING_CONFIG`
    if settings.DEBUG:
        sqlalchemy_logger.info(f"Це INFO від SQLAlchemy ('{sqlalchemy_logger.name}') (імітація SQL в DEBUG).")
    else:
        sqlalchemy_logger.warning(f"Це WARNING від SQLAlchemy ('{sqlalchemy_logger.name}') (приклад, НЕ SQL).")

    # Демонстрація логування винятків
    try:
        x = 1 / 0
    except ZeroDivisionError:
        # app_logger.error("Виникла помилка ділення на нуль!", exc_info=True) # Альтернативний спосіб логування трасування
        # `exc_info=True` автоматично додає інформацію про виняток до логу.
        app_logger.exception("Виник виняток ZeroDivisionError! Трасування стеку буде автоматично додано до цього повідомлення.")

    app_logger.info(f"\nНалаштування логування успішно застосовано та протестовано. Перевірте вивід консолі.")
    if settings.LOG_TO_FILE and LOG_DIR_PATH:
        app_logger.info(f"Якщо логування у файл увімкнено (`LOG_TO_FILE=True`), перевірте файли у директорії: {LOG_DIR_PATH.resolve()}")
        app_logger.info(f"  Лог програми: {LOG_DIR_PATH / settings.LOG_APP_FILE}")
        app_logger.info(f"  Лог помилок: {LOG_DIR_PATH / settings.LOG_ERROR_FILE}")
    else:
        app_logger.info("Логування у файл вимкнено (`LOG_TO_FILE=False`). Всі логи направлено в консоль.")
