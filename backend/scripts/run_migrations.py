# backend/scripts/run_migrations.py
import os
import sys
import logging
from alembic.config import Config
from alembic import command

# Налаштування логування
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Переконуємося, що корінь проекту (backend) є в sys.path
# для правильного завантаження alembic.ini та env.py,
# які можуть імпортувати з `app`
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) # Це 'backend/'
if PROJECT_ROOT not in sys.path:
    logger.info(f"Додавання {PROJECT_ROOT} до sys.path для Alembic.")
    sys.path.append(PROJECT_ROOT)

ALEMBIC_INI_PATH = os.path.join(PROJECT_ROOT, 'alembic.ini')

def main():
    """
    Головна функція для запуску міграцій Alembic.
    Застосовує міграції до версії 'head'.
    """
    logger.info(f"Завантаження конфігурації Alembic з: {ALEMBIC_INI_PATH}")

    if not os.path.exists(ALEMBIC_INI_PATH):
        logger.error(f"Файл конфігурації alembic.ini не знайдено за шляхом: {ALEMBIC_INI_PATH}")
        logger.error("Переконайтеся, що скрипт запускається з правильної директорії або alembic.ini існує.")
        sys.exit(1)

    try:
        # Створення об'єкту конфігурації Alembic
        # Цей шлях має бути відносним до місця запуску alembic команди,
        # або абсолютним. Якщо запускаємо з `backend/scripts`, то `alembic.ini`
        # знаходиться на рівень вище.
        # Alembic сам намагається знайти alembic.ini у поточній директорії або вище.
        # Явно вказувати шлях до .ini є надійніше для скриптів.
        alembic_cfg = Config(ALEMBIC_INI_PATH)

        # Встановлюємо шлях до директорії з міграціями, якщо він не абсолютний в alembic.ini
        # Зазвичай alembic.ini має щось типу `script_location = app/src/migrations`
        # Якщо script_location відносний, Alembic розглядає його відносно поточного робочого каталогу.
        # Щоб це працювало надійно зі скриптом, можна встановити `prepend_sys_path`.
        # alembic_cfg.set_main_option('prepend_sys_path', '.') # Додає поточну директорію до sys.path

        logger.info("Застосування міграцій до версії 'head'...")
        command.upgrade(alembic_cfg, "head")
        logger.info("Міграції успішно застосовано.")

    except Exception as e:
        logger.error(f"Помилка під час виконання міграцій Alembic: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    # Для запуску: python backend/scripts/run_migrations.py
    # Переконайтеся, що DATABASE_URL правильно налаштований в .env
    # і доступний для `app.src.config.database` та `app.src.migrations.env.py`.
    main()
