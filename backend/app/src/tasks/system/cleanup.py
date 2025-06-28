# backend/app/src/tasks/system/cleanup.py
# -*- coding: utf-8 -*-
"""
Фонові завдання для очищення системи.
"""
from backend.app.src.config.logging import get_logger
# TODO: Імпортувати екземпляр Celery app, коли він буде визначений (наприклад, з `backend.app.src.workers.celery_app`)
# from backend.app.src.workers import celery_app as app # Приклад
# TODO: Імпортувати налаштування, якщо потрібно (наприклад, для шляхів до логів, термінів зберігання)
# from backend.app.src.core.config import settings
# TODO: Імпортувати DBSession або інший спосіб доступу до БД, якщо завдання взаємодіють з нею
# from backend.app.src.config.database import SessionLocal

logger = get_logger(__name__)

# @app.task(name="tasks.system.cleanup.cleanup_old_logs_task") # Приклад для Celery
def cleanup_old_logs_task(days_to_keep: int = 90):
    """
    Періодичне завдання для видалення старих лог-файлів.

    Args:
        days_to_keep (int): Кількість днів, протягом яких зберігати логи.
                            Логи, старші за цю кількість днів, будуть видалені.
    """
    logger.info(f"Запуск завдання очищення старих логів (зберігати {days_to_keep} днів)...")
    # TODO: Реалізувати логіку пошуку та видалення старих лог-файлів.
    # - Визначити директорію з логами (з settings).
    # - Пройтися по файлах, перевірити дату модифікації.
    # - Видалити файли, що старші за `days_to_keep`.
    # - Обережно обробляти можливі помилки доступу до файлів.
    # Приклад:
    # log_dir = settings.LOG_DIR
    # current_time = time.time()
    # for filename in os.listdir(log_dir):
    #     file_path = os.path.join(log_dir, filename)
    #     if os.path.isfile(file_path):
    #         file_mod_time = os.path.getmtime(file_path)
    #         if (current_time - file_mod_time) // (24 * 3600) > days_to_keep:
    #             try:
    #                 os.remove(file_path)
    #                 logger.info(f"Видалено старий лог-файл: {file_path}")
    #             except OSError as e:
    #                 logger.error(f"Помилка видалення лог-файлу {file_path}: {e}")
    logger.info("Завдання очищення старих логів завершено (ЗАГЛУШКА).")
    return {"status": "completed", "message": f"Log cleanup task finished (stub). Kept logs for {days_to_keep} days."}

# @app.task(name="tasks.system.cleanup.cleanup_temp_files_task") # Приклад для Celery
def cleanup_temp_files_task():
    """
    Періодичне завдання для видалення тимчасових файлів.
    """
    logger.info("Запуск завдання очищення тимчасових файлів...")
    # TODO: Реалізувати логіку пошуку та видалення тимчасових файлів
    # (наприклад, з директорії `static/temp/` або іншої визначеної в settings).
    logger.info("Завдання очищення тимчасових файлів завершено (ЗАГЛУШКА).")
    return {"status": "completed", "message": "Temporary files cleanup task finished (stub)."}

# @app.task(name="tasks.system.cleanup.cleanup_stale_sessions_task") # Приклад для Celery
def cleanup_stale_sessions_task(max_age_days: int = 30):
    """
    Періодичне завдання для видалення застарілих сесій користувачів з бази даних.
    (Актуально, якщо сесії зберігаються в БД і не мають механізму авто-видалення).
    """
    logger.info(f"Запуск завдання очищення застарілих сесій (старші за {max_age_days} днів)...")
    # TODO: Реалізувати логіку видалення сесій з БД.
    # db = SessionLocal()
    # try:
    #     # cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
    #     # result = db.query(UserSessionModel).filter(UserSessionModel.last_activity < cutoff_date).delete()
    #     # db.commit()
    #     # logger.info(f"Видалено {result} застарілих сесій.")
    # except Exception as e:
    #     # logger.error(f"Помилка очищення застарілих сесій: {e}", exc_info=True)
    #     # db.rollback()
    # finally:
    #     # db.close()
    #     pass
    logger.info("Завдання очищення застарілих сесій завершено (ЗАГЛУШКА).")
    return {"status": "completed", "message": f"Stale sessions cleanup task finished (stub). Max age {max_age_days} days."}

# TODO: Додати інші завдання очищення, якщо потрібно.
