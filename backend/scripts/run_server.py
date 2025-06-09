# backend/scripts/run_server.py
import uvicorn
import argparse
import os
import logging
import sys

# Налаштування базового логування для скрипта
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Головна функція для запуску Uvicorn сервера.
    Розбирає аргументи командного рядка для налаштування хоста, порту та режиму перезавантаження.
    """
    parser = argparse.ArgumentParser(description="Скрипт для запуску FastAPI додатку за допомогою Uvicorn.")

    default_host = os.getenv("UVICORN_HOST", "127.0.0.1")
    default_port = int(os.getenv("UVICORN_PORT", "8000"))
    env_reload = os.getenv("UVICORN_RELOAD", "False").lower() in ('true', '1', 't')
    default_workers = int(os.getenv("UVICORN_WORKERS", "1"))
    default_log_level = os.getenv("UVICORN_LOG_LEVEL", "info").lower()

    parser.add_argument(
        "--host",
        type=str,
        default=default_host,
        help=f"Хост, на якому буде запущено сервер (за замовчуванням: {default_host} або UVICORN_HOST)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=default_port,
        help=f"Порт, на якому буде запущено сервер (за замовчуванням: {default_port} або UVICORN_PORT)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help=f"Увімкнути режим автоматичного перезавантаження Uvicorn (для розробки). Перевизначає UVICORN_RELOAD. За замовчуванням активовано, якщо UVICORN_RELOAD встановлено в true."
    )
    parser.add_argument(
        "--no-reload",
        action="store_false",
        dest="reload",
        help="Явно вимкнути режим автоматичного перезавантаження. Має вищий пріоритет ніж --reload або UVICORN_RELOAD."
    )
    parser.set_defaults(reload=env_reload)

    parser.add_argument(
        "--workers",
        type=int,
        default=default_workers,
        help=f"Кількість робочих процесів Uvicorn (за замовчуванням: {default_workers} або UVICORN_WORKERS)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=default_log_level,
        choices=['critical', 'error', 'warning', 'info', 'debug', 'trace'],
        help=f"Рівень логування Uvicorn (за замовчуванням: {default_log_level} або UVICORN_LOG_LEVEL)"
    )
    parser.add_argument(
        "--app",
        type=str,
        default=os.getenv("APP_MODULE", "app.main:app"),
        help="Рядок для імпорту FastAPI додатку (наприклад, 'app.main:app'). За замовчуванням: APP_MODULE або 'app.main:app'"
    )

    args = parser.parse_args()

    logger.info(f"Запуск Uvicorn сервера для додатку: {args.app}")
    logger.info(f"Хост: {args.host}")
    logger.info(f"Порт: {args.port}")
    logger.info(f"Режим перезавантаження: {'Увімкнено' if args.reload else 'Вимкнено'}")
    logger.info(f"Кількість робітників: {args.workers}")
    logger.info(f"Рівень логування: {args.log_level}")

    if not args.app:
        logger.error("Не вказано FastAPI додаток для запуску. Використайте --app або встановіть APP_MODULE.")
        return

    workers_to_run = args.workers
    if args.reload and args.workers > 1:
        logger.warning("Режим перезавантаження (--reload) несумісний з кількістю робітників > 1. Встановлено кількість робітників = 1.")
        workers_to_run = 1

    # Щоб uvicorn.run знайшов 'app.main:app', зазвичай цей скрипт має запускатися
    # з директорії `backend/` (тобто `python scripts/run_server.py`),
    # або директорія `backend/` має бути в PYTHONPATH.
    # Uvicorn CLI робить це автоматично, додаючи поточну директорію до sys.path.
    # Для програмного виклику uvicorn.run, це може потребувати уваги.
    # Однак, стандартна практика - запускати uvicorn з командного рядка з кореня проекту,
    # де він може знайти `app`.
    # Якщо PYTHONPATH налаштований правильно (наприклад, через poetry або venv активацію,
    # що додає корінь проекту до шляху), то прямий виклик uvicorn.run також спрацює.

    # Додамо корінь проекту (директорію backend) до sys.path, якщо скрипт запускається з backend/scripts
    # Це допоможе uvicorn знайти модуль app.main:app
    # Визначаємо шлях до директорії backend
    current_script_path = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.abspath(os.path.join(current_script_path, os.pardir))

    if backend_dir not in sys.path:
        logger.info(f"Додавання {backend_dir} до sys.path для знаходження модуля додатку.")
        sys.path.insert(0, backend_dir)

    uvicorn.run(
        args.app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=workers_to_run,
        log_level=args.log_level.lower()
    )

if __name__ == "__main__":
    main()
