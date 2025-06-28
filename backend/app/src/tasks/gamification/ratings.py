# backend/app/src/tasks/gamification/ratings.py
# -*- coding: utf-8 -*-
"""
Фонові завдання, пов'язані з розрахунком рейтингів.
"""
from backend.app.src.config.logging import get_logger
# TODO: Імпортувати екземпляр Celery app
# from backend.app.src.workers import celery_app as app # Приклад
# TODO: Імпортувати сервіси
# from backend.app.src.services.gamification.rating_service import RatingService
# from backend.app.src.services.group.group_service import GroupService # Для отримання всіх активних груп
# from backend.app.src.config.database import SessionLocal

logger = get_logger(__name__)

# @app.task(name="tasks.gamification.ratings.recalculate_all_group_ratings_task") # Приклад для Celery
def recalculate_all_group_ratings_task():
    """
    Періодичне завдання для перерахунку всіх рейтингів користувачів у всіх групах.
    Рейтинги можуть базуватися на різних показниках (загальний бал, кількість
    виконаних завдань за період тощо).
    """
    logger.info("Запуск завдання перерахунку рейтингів користувачів...")
    # db = None
    # try:
    #     db = SessionLocal()
    #     rating_service = RatingService(db)
    #     group_service = GroupService(db)
    #
    #     active_groups = await group_service.get_all_active_groups()
    #
    #     if not active_groups:
    #         logger.info("Немає активних груп для перерахунку рейтингів.")
    #         return {"status": "completed", "message": "No active groups for rating recalculation."}
    #
    #     processed_groups_count = 0
    #     for group in active_groups:
    #         logger.debug(f"Перерахунок рейтингів для групи: {group.name} (ID: {group.id})")
    #         try:
    #             # RatingService має визначити, які типи рейтингів потрібно перерахувати для цієї групи
    #             # (наприклад, за загальним балом, за активністю за тиждень/місяць)
    #             # та оновити збережені дані рейтингів (наприклад, в окремій таблиці UserGroupRating).
    #             # await rating_service.recalculate_ratings_for_group(group_id=group.id)
    #             logger.info(f"Рейтинги для групи {group.id} перераховано (ЗАГЛУШКА).")
    #             processed_groups_count += 1
    #         except Exception as e_group:
    #             logger.error(f"Помилка перерахунку рейтингів для групи {group.id}: {e_group}", exc_info=True)
    #
    #     logger.info(f"Перерахунок рейтингів завершено. Оброблено груп: {processed_groups_count}.")
    #     return {"status": "completed", "processed_groups": processed_groups_count}
    #
    # except Exception as e:
    #     logger.error(f"Загальна помилка в завданні перерахунку рейтингів: {e}", exc_info=True)
    #     return {"status": "error", "message": str(e)}
    # finally:
    #     if db:
    #         db.close()

    logger.info("Завдання перерахунку рейтингів користувачів завершено (ЗАГЛУШКА).")
    return {"status": "completed", "message": "User ratings recalculation task finished (stub)."}

# Примітка: Якщо рейтинги оновлюються в реальному часі або не потребують
# складних періодичних розрахунків, це завдання може бути спрощеним або непотрібним.
# Однак, для зведених рейтингів за період або ресурсоємних розрахунків
# періодичне завдання є доцільним.
