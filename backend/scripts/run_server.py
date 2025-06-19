# backend/scripts/run_server.py
# -*- coding: utf-8 -*-
"""
Скрипт для запуску FastAPI додатку за допомогою Uvicorn.

Цей скрипт надає зручний спосіб запуску Uvicorn сервера з різними
конфігураціями через аргументи командного рядка або змінні середовища.
Він дозволяє налаштовувати хост, порт, кількість робочих процесів,
режим автоматичного перезавантаження та рівень логування.
"""
import uvicorn
import argparse
import os
import logging  # Стандартний модуль логування
import sys
from typing import List  # Для типізації

# --- Налаштування шляхів ---
# Додаємо директорію 'backend' до sys.path, щоб uvicorn.run міг знайти модуль додатку.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)  # Директорія 'backend/'
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# --- Налаштування логування ---
try:
    from backend.app.src.config.logging import get_logger # Змінено імпорт
    logger = get_logger(__name__) # Отримуємо логер для цього скрипта
    logger.info("Використовується логер додатку для скрипта run_server.")  # i18n
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.info("Логер додатку не знайдено (ImportError), використовується базовий логер для run_server.")  # i18n

# Перевірка та логування додавання шляху (використовує вже ініціалізований logger)
# Цей блок був тут, але логічніше, щоб він виконувався після спроби налаштування логера.
# if BACKEND_DIR not in sys.path: # Закоментовано, бо sys.path вже модифіковано вище.
#     # Якщо шлях вже додано, ця умова не виконається.
#     # Якщо ж він додається вперше, логер вже має бути налаштований.
#     pass # Логування про додавання шляху вже було вище, якщо це був перший раз.
# Це повідомлення тепер буде виведено через налаштований логер, якщо він успішно імпортувався.
# Якщо ні, то через базовий.
# Повідомлення про додавання шляху вже було вище, тому цей блок можна спростити або видалити,
# якщо припускати, що логування налаштовується коректно.
# Для чистоти, логування про додавання до sys.path краще робити одразу після дії.
# Оскільки logger вже визначено, можна просто використовувати його.
# Залишимо як є, але звернемо увагу, що інформація про sys.path може дублюватися або бути не зовсім точною
# щодо того, який саме логер її виводить, якщо перший logger.info після sys.path.insert не спрацював.
# Однак, основне виправлення - це get_logger.

# Насправді, логування про sys.path краще розмістити після блоку try-except,
# щоб бути впевненим, що logger точно ініціалізований або як кастомний, або як базовий.
# Але, оскільки логіка додавання шляху вище, і там є logger.info, то залишимо як є,
# основна задача - виправити get_logger.


# Базова функція-заглушка для інтернаціоналізації рядків
def _(text: str) -> str:
    return text


def main():
    """
    Головна функція для запуску Uvicorn сервера.
    Розбирає аргументи командного рядка для налаштування хоста, порту,
    кількості робітників, режиму перезавантаження та рівня логування.
    """
    # i18n: Argparse description for the script
    parser = argparse.ArgumentParser(description=_("Скрипт для запуску FastAPI додатку за допомогою Uvicorn."))

    # Визначення значень за замовчуванням з змінних середовища
    default_host = os.getenv("UVICORN_HOST", "127.0.0.1")
    default_port = int(os.getenv("UVICORN_PORT", "8000"))
    # Визначаємо значення reload з UVICORN_RELOAD, але дозволяємо --reload/--no-reload його перекрити
    env_reload_str = os.getenv("UVICORN_RELOAD", "False").lower()
    initial_reload_default = env_reload_str in ('true', '1', 't', 'yes', 'on')

    default_workers = int(os.getenv("UVICORN_WORKERS", "1"))
    default_log_level = os.getenv("UVICORN_LOG_LEVEL", "info").lower()
    # Шлях до головного файлу додатка FastAPI відносно директорії `backend/`
    default_app_module = os.getenv("APP_MODULE", "app.main:app")

    parser.add_argument(
        "--host", type=str, default=default_host,
        # i18n: Argparse help for --host
        help=_("Хост, на якому буде запущено сервер (за замовчуванням: {default} або з UVICORN_HOST).").format(
            default=default_host)
    )
    parser.add_argument(
        "--port", type=int, default=default_port,
        # i18n: Argparse help for --port
        help=_("Порт, на якому буде запущено сервер (за замовчуванням: {default} або з UVICORN_PORT).").format(
            default=default_port)
    )

    # Група для керування --reload, щоб --reload та --no-reload були взаємовиключними
    reload_group = parser.add_mutually_exclusive_group()
    reload_group.add_argument(
        "--reload", action="store_true", dest="reload_explicitly_set", default=None,
        # i18n: Argparse help for --reload
        help=_("Увімкнути режим автоматичного перезавантаження Uvicorn (для розробки). Перевизначає UVICORN_RELOAD.")
    )
    reload_group.add_argument(
        "--no-reload", action="store_false", dest="reload_explicitly_set",
        # i18n: Argparse help for --no-reload
        help=_(
            "Явно вимкнути режим автоматичного перезавантаження. Має вищий пріоритет ніж --reload або UVICORN_RELOAD.")
    )

    parser.add_argument(
        "--workers", type=int, default=default_workers,
        # i18n: Argparse help for --workers
        help=_("Кількість робочих процесів Uvicorn (за замовчуванням: {default} або з UVICORN_WORKERS).").format(
            default=default_workers)
    )
    parser.add_argument(
        "--log-level", type=str, default=default_log_level,
        choices=['critical', 'error', 'warning', 'info', 'debug', 'trace'],
        # i18n: Argparse help for --log-level
        help=_("Рівень логування Uvicorn (за замовчуванням: {default} або з UVICORN_LOG_LEVEL).").format(
            default=default_log_level)
    )
    parser.add_argument(
        "--app", type=str, default=default_app_module,
        # i18n: Argparse help for --app
        help=_(
            "Рядок для імпорту FastAPI додатку (наприклад, 'app.main:app', відносно директорії 'backend/'). За замовчуванням: APP_MODULE або '{default}'.").format(
            default=default_app_module)
    )

    args = parser.parse_args()

    # Визначення фінального значення для reload
    if args.reload_explicitly_set is not None:  # Якщо --reload або --no-reload було вказано
        final_reload_enabled = args.reload_explicitly_set
    else:  # Інакше беремо з env (або False, якщо env не було)
        final_reload_enabled = initial_reload_default

    # i18n: Log message - Starting Uvicorn server for app
    logger.info(_("Запуск Uvicorn сервера для додатку: {app_module}").format(app_module=args.app))
    logger.info(_("Хост: {host}").format(host=args.host))  # i18n
    logger.info(_("Порт: {port}").format(port=args.port))  # i18n
    logger.info(_("Режим перезавантаження: {status}").format(
        status=_("Увімкнено") if final_reload_enabled else _("Вимкнено")))  # i18n
    logger.info(_("Кількість робітників: {workers}").format(workers=args.workers))  # i18n
    logger.info(_("Рівень логування Uvicorn: {log_level}").format(log_level=args.log_level))  # i18n

    if not args.app:
        # i18n: Error message - FastAPI app module not specified
        logger.error(
            _("Не вказано FastAPI додаток для запуску. Використайте --app або встановіть змінну середовища APP_MODULE."))
        sys.exit(1)  # Вихід з помилкою

    workers_to_run = args.workers
    if final_reload_enabled and args.workers > 1:
        # i18n: Warning message - Reload mode incompatible with multiple workers
        logger.warning(
            _("Режим перезавантаження (--reload) несумісний з кількістю робітників > 1. Кількість робітників буде встановлено в 1."))
        workers_to_run = 1

    # Uvicorn використовує поточну робочу директорію для пошуку модуля додатку,
    # якщо шлях до модуля не є абсолютним.
    # Оскільки ми додали BACKEND_DIR до sys.path, uvicorn.run повинен знайти 'app.main:app'.
    # Якщо запускати скрипт з директорії `backend/` (наприклад, `python scripts/run_server.py`),
    # то `app.main:app` буде знайдено відносно `backend/`.
    # Якщо запускати з кореня проекту (на один рівень вище `backend/`),
    # то для uvicorn командного рядка потрібно було б вказати `backend.app.main:app`.
    # Але оскільки `backend` додано в sys.path, `app.main:app` має працювати.

    try:
        uvicorn.run(
            args.app,  # Наприклад, "app.main:app"
            host=args.host,
            port=args.port,
            reload=final_reload_enabled,
            workers=workers_to_run,
            log_level=args.log_level.lower()
            # reload_dirs можна вказати, якщо стандартний механізм не відстежує всі потрібні зміни,
            # наприклад, якщо конфігураційні файли поза стандартними шляхами Python.
            # reload_dirs=[os.path.join(BACKEND_DIR, "app")]
        )
    except ImportError as e:
        logger.error(
            _("Помилка імпорту модуля додатку '{app_module}': {error}. Переконайтеся, що шлях правильний і всі залежності встановлено.").format(
                app_module=args.app, error=e))  # i18n
        logger.error(_("Поточний sys.path: {sys_path}").format(sys_path=sys.path))  # i18n
        logger.error(_("Поточна робоча директорія: {cwd}").format(cwd=os.getcwd()))  # i18n
        sys.exit(1)
    except Exception as e:
        logger.error(_("Неочікувана помилка при запуску Uvicorn: {error}").format(error=e), exc_info=True)  # i18n
        sys.exit(1)


if __name__ == "__main__":
    # Приклади запуску:
    # # Запуск з налаштуваннями за замовчуванням (з директорії backend/):
    # python scripts/run_server.py
    #
    # # Запуск на іншому порту з увімкненим перезавантаженням (з директорії backend/):
    # python scripts/run_server.py --port 8080 --reload
    #
    # # Запуск з іншим модулем додатку (якщо потрібно, з директорії backend/):
    # python scripts/run_server.py --app custom_app.api:my_fastapi_instance
    #
    # # Запуск з кореня проекту (на один рівень вище backend/):
    # # python backend/scripts/run_server.py --app backend.app.main:app (якщо APP_MODULE не налаштовано)
    # # Або, якщо APP_MODULE="app.main:app", то `python backend/scripts/run_server.py` має працювати
    # # завдяки додаванню `backend` до sys.path.
    main()
