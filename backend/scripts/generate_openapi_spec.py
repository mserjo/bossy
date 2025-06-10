# backend/scripts/generate_openapi_spec.py
import json
import os
import sys
import logging

# Налаштування базового логування для скрипта
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Додавання шляху до батьківської директорії (backend) для імпорту модулів додатку
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) # 'backend/'
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
    logger.info(f"Додано {PROJECT_ROOT} до sys.path")

# Імпорт FastAPI додатку
# Це має бути після додавання PROJECT_ROOT до sys.path
try:
    from app.main import app # Припускаємо, що FastAPI app інстанс знаходиться в app.main
except ImportError as e:
    logger.error(f"Не вдалося імпортувати FastAPI додаток 'app' з 'app.main'. Переконайтеся, що PYTHONPATH налаштовано правильно. Помилка: {e}")
    sys.exit(1)

# Визначення шляху для збереження специфікації OpenAPI
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "docs", "api")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "openapi.json")

def generate_and_save_openapi_spec():
    """
    Генерує OpenAPI специфікацію з FastAPI додатку та зберігає її у файл.
    """
    logger.info("Генерація OpenAPI специфікації...")
    try:
        # Отримання OpenAPI схеми від FastAPI додатку
        openapi_schema = app.openapi()
        logger.info("OpenAPI специфікацію успішно згенеровано.")
    except Exception as e:
        logger.error(f"Помилка під час генерації OpenAPI схеми: {e}", exc_info=True)
        sys.exit(1)

    # Створення директорії для виводу, якщо вона не існує
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        logger.info(f"Директорію для виводу '{OUTPUT_DIR}' перевірено/створено.")
    except OSError as e:
        logger.error(f"Не вдалося створити директорію '{OUTPUT_DIR}': {e}", exc_info=True)
        sys.exit(1)

    # Збереження схеми у файл JSON
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(openapi_schema, f, ensure_ascii=False, indent=4)
        logger.info(f"OpenAPI специфікацію успішно збережено у файл: {OUTPUT_FILE}")
    except IOError as e:
        logger.error(f"Не вдалося записати OpenAPI специфікацію у файл '{OUTPUT_FILE}': {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Неочікувана помилка під час збереження файлу: {e}", exc_info=True)
        sys.exit(1)

def main():
    """
    Головна функція скрипта.
    """
    logger.info("Запуск скрипта генерації OpenAPI специфікації...")
    generate_and_save_openapi_spec()
    logger.info("Скрипт генерації OpenAPI специфікації завершив роботу.")

if __name__ == "__main__":
    # Для запуску: python backend/scripts/generate_openapi_spec.py
    # Переконайтеся, що всі залежності додатку встановлені, оскільки FastAPI app буде імпортовано.
    main()
