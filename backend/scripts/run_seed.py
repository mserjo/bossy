# backend/scripts/run_seed.py
# -*- coding: utf-8 -*-
"""
Скрипт для заповнення бази даних початковими даними (seed).

Цей скрипт викликає `InitialDataService` для заповнення довідників
та створення інших необхідних початкових записів у базі даних.
Скрипт є ідемпотентним, тобто його можна безпечно запускати кілька разів.
"""
import asyncio
import os
import sys
import logging  # Стандартний модуль логування

# --- Налаштування шляхів для імпорту модулів додатку ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)  # Директорія 'backend'
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# --- Налаштування логування ---
try:
    from backend.app.src.config.logging import logger

    logger.info("Використовується логер додатку для скрипта run_seed.")  # i18n
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.info("Логер додатку не знайдено, використовується базовий логер для run_seed.")  # i18n

if BACKEND_DIR not in sys.path:  # Логуємо, якщо шлях було додано раніше
    logger.info(f"Додано '{BACKEND_DIR}' до sys.path для run_seed.")  # i18n

# --- Імпорт компонентів додатку ---
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from backend.app.src.config.database import get_db_session  # Для отримання сесії БД
# Головний сервіс для ініціалізації даних
from backend.app.src.services.system.initial_data_service import InitialDataService


# Базова функція-заглушка для інтернаціоналізації рядків
def _(text: str) -> str:
    return text


async def run_seeding_logic(db_session: AsyncSession):
    """
    Асинхронна логіка для запуску сервісу заповнення початкових даних.

    Args:
        db_session: Асинхронна сесія бази даних.
    """
    try:
        initial_data_service = InitialDataService(db_session=db_session)

        # i18n: Log message - Calling service to populate dictionaries
        logger.info(_("Виклик InitialDataService для заповнення довідників..."))
        # Припускаємо, що InitialDataService має метод populate_dictionaries()
        # або run_full_initialization() також обробляє довідники ідемпотентно.
        # Якщо InitialDataService.run_full_initialization() створює і користувачів,
        # то це може бути те, що нам потрібно.
        # Згідно з попереднім оглядом InitialDataService, він має метод run_full_initialization,
        # який включає initialize_base_dictionaries, create_system_users, setup_default_settings.
        # Це саме те, що потрібно для "заповнення початковими даними".

        result = await initial_data_service.run_full_initialization()

        if result.get("status") == "success" or result.get("status") == "skipped_already_done":
            logger.info(
                _("Заповнення початкових даних через InitialDataService пройшло успішно (або дані вже існували)."))  # i18n
            logger.info(_("Деталі: {details}").format(details=result.get("details")))  # i18n
        elif result.get("status") == "partial_success":
            logger.warning(
                _("InitialDataService завершив роботу з частковим успіхом. Деякі кроки могли не виконатись."))  # i18n
            logger.warning(_("Деталі: {details}").format(details=result.get("details")))  # i18n
        else:  # error, critical_error, conflict
            logger.error(_("Помилка під час виконання InitialDataService: {message}").format(
                message=result.get("message")))  # i18n
            logger.error(_("Деталі: {details}").format(details=result.get("details")))  # i18n

    except Exception as e:
        # i18n: Error message - Error during seeding process
        logger.error(_("Помилка під час процесу заповнення початкових даних: {error}").format(error=e), exc_info=True)


async def run_script_async_logic():
    """
    Асинхронна функція для запуску логіки скрипта з отриманням сесії БД.
    """
    # i18n: Log message - Starting data seeding script
    logger.info(_("Запуск скрипта заповнення початкових даних (seed)..."))

    session_generator = get_db_session()
    db_session: Optional[AsyncSession] = None
    try:
        db_session = await anext(session_generator)
        if db_session is None:
            raise StopAsyncIteration  # Якщо сесія None

        await run_seeding_logic(db_session)

    except StopAsyncIteration:
        # i18n: Error message - Failed to get DB session
        logger.error(_("Не вдалося отримати сесію бази даних для заповнення початкових даних."))
    except Exception as e:
        # i18n: Error message - Unexpected error during script execution
        logger.error(_("Виникла непередбачена помилка під час виконання скрипта run_seed: {error}").format(error=e),
                     exc_info=True)
    finally:
        if db_session is not None:
            try:
                await session_generator.aclose()  # Закриваємо генератор (і сесію)
            except Exception as e:
                # i18n: Error message - Error closing DB session
                logger.error(_("Помилка при закритті сесії БД: {error}").format(error=e), exc_info=True)

    # i18n: Log message - Data seeding script finished
    logger.info(_("Роботу скрипта заповнення початкових даних завершено."))


def main():
    """
    Головна функція для запуску скрипта.
    """
    if sys.version_info >= (3, 7):
        asyncio.run(run_script_async_logic())
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_script_async_logic())


if __name__ == "__main__":
    # Для запуску цього скрипта:
    # python backend/scripts/run_seed.py
    #
    # Передумови:
    # 1. Змінна середовища DATABASE_URL має бути правильно налаштована.
    # 2. База даних має бути доступна, міграції Alembic застосовані.
    # 3. `InitialDataService` має бути правильно налаштований та містити логіку
    #    для створення всіх необхідних початкових даних (довідники, системні користувачі тощо).
    #
    # Цей скрипт тепер покладається на `InitialDataService` для виконання фактичної роботи,
    # забезпечуючи централізовану та узгоджену логіку заповнення даних.
    logger.info(_("Ініціалізація скрипта run_seed.py..."))  # i18n
    main()
