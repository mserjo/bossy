# backend/scripts/generate_openapi_spec.py
# -*- coding: utf-8 -*-
"""
Скрипт для генерації специфікації OpenAPI (JSON) для FastAPI додатку.

Цей скрипт імпортує екземпляр FastAPI додатку, викликає його метод .openapi()
для отримання схеми API, та зберігає цю схему у файл JSON у визначеній директорії.
Це корисно для CI/CD процесів, генерації клієнтських бібліотек або публікації документації API.
"""
import json
import os
import sys
import logging # Стандартний модуль логування

# --- Налаштування шляхів для імпорту модулів додатку ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR) # Директорія 'backend'
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

# --- Імпорт компонентів додатку ---
# Намагаємося імпортувати логер та FastAPI додаток.
try:
    from backend.app.src.config.logging import get_logger # Змінено імпорт
    logger = get_logger(__name__) # Отримуємо логер для цього скрипта
    logger.info("Використовується логер додатку для скрипта generate_openapi_spec.") # i18n
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.info("Логер додатку не знайдено (ImportError), використовується базовий логер для generate_openapi_spec.") # i18n

try:
    from backend.app.main import app # Імпорт FastAPI app інстансу
    logger.debug("FastAPI додаток 'app' успішно імпортовано.") # i18n
except ImportError as e:
    # i18n: Error message - Failed to import FastAPI app
    logger.error(
        _("Не вдалося імпортувати FastAPI додаток 'app' з 'backend.app.main'. "
          "Переконайтеся, що PYTHONPATH налаштовано правильно та всі залежності встановлено. Помилка: {error}").format(error=e),
        exc_info=True
    )
    sys.exit(1)

# --- Конфігурація шляхів виводу ---
# TODO: Розглянути можливість зробити OUTPUT_DIR та OUTPUT_FILE конфігурованими через аргументи командного рядка або змінні середовища.
# Директорія 'docs/api/' в корені проекту (на рівні з 'backend', 'frontend')
PROJECT_ROOT_DIR = os.path.dirname(BACKEND_DIR)
OUTPUT_DIR = os.path.join(PROJECT_ROOT_DIR, "docs", "api")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "openapi.json")

# Базова функція-заглушка для інтернаціоналізації рядків
def _(text: str) -> str:
    return text

def generate_and_save_openapi_spec():
    """
    Генерує OpenAPI специфікацію з FastAPI додатку та зберігає її у JSON файл.
    """
    # i18n: Log message - Starting OpenAPI specification generation
    logger.info(_("Генерація OpenAPI специфікації..."))
    try:
        # Отримання OpenAPI схеми від FastAPI додатку
        # Метод .openapi() повертає словник, що представляє схему OpenAPI.
        openapi_schema = app.openapi()
        # i18n: Log message - OpenAPI specification generated successfully
        logger.info(_("OpenAPI специфікацію успішно згенеровано."))
    except Exception as e:
        # i18n: Error message - Error during OpenAPI schema generation
        logger.error(_("Помилка під час генерації OpenAPI схеми: {error}").format(error=e), exc_info=True)
        sys.exit(1)

    # Створення директорії для виводу, якщо вона не існує
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        # i18n: Log message - Output directory checked/created
        logger.info(_("Директорію для виводу '{output_dir}' перевірено/створено.").format(output_dir=OUTPUT_DIR))
    except OSError as e:
        # i18n: Error message - Failed to create output directory
        logger.error(_("Не вдалося створити директорію '{output_dir}': {error}").format(output_dir=OUTPUT_DIR, error=e), exc_info=True)
        sys.exit(1)

    # Збереження схеми у файл JSON
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            # json.dump для запису словника у файл JSON.
            # ensure_ascii=False для коректного відображення не-ASCII символів (наприклад, кирилиці).
            # indent=4 для форматування файлу з відступами для кращої читабельності.
            json.dump(openapi_schema, f, ensure_ascii=False, indent=4)
        # i18n: Log message - OpenAPI specification saved successfully
        logger.info(_("OpenAPI специфікацію успішно збережено у файл: {output_file}").format(output_file=OUTPUT_FILE))
    except IOError as e:
        # i18n: Error message - Failed to write OpenAPI spec to file
        logger.error(_("Не вдалося записати OpenAPI специфікацію у файл '{output_file}': {error}").format(output_file=OUTPUT_FILE, error=e), exc_info=True)
        sys.exit(1)
    except Exception as e:
        # i18n: Error message - Unexpected error during file save
        logger.error(_("Неочікувана помилка під час збереження файлу OpenAPI: {error}").format(error=e), exc_info=True)
        sys.exit(1)

def main():
    """
    Головна функція скрипта.
    """
    # i18n: Log message - Starting OpenAPI specification generation script
    logger.info(_("Запуск скрипта генерації OpenAPI специфікації..."))
    generate_and_save_openapi_spec()
    # i18n: Log message - OpenAPI specification generation script finished
    logger.info(_("Скрипт генерації OpenAPI специфікації завершив роботу."))

if __name__ == "__main__":
    # Для запуску цього скрипта:
    # python backend/scripts/generate_openapi_spec.py
    #
    # Передумови:
    # 1. Всі залежності FastAPI додатку мають бути встановлені, оскільки скрипт імпортує
    #    та ініціалізує екземпляр додатку для генерації схеми.
    # 2. Шлях до директорії 'backend' має бути доступний для імпорту (sys.path налаштовується на початку скрипта).
    # 3. Файл backend/app/main.py має містити екземпляр FastAPI додатку з назвою `app`.
    main()
