# backend/app/src/tasks/gamification/levels.py
# -*- coding: utf-8 -*-
"""
Фонові завдання, пов'язані з рівнями користувачів.
"""
from backend.app.src.config.logging import get_logger
# TODO: Імпортувати екземпляр Celery app
# from backend.app.src.workers import celery_app as app # Приклад
# TODO: Імпортувати сервіси
# from backend.app.src.services.gamification.user_level_service import UserLevelService
# from backend.app.src.services.group.group_service import GroupService # Щоб отримати всі групи/користувачів
# from backend.app.src.config.database import SessionLocal

logger = get_logger(__name__)

# @app.task(name="tasks.gamification.levels.recalculate_all_user_levels_task") # Приклад для Celery
def recalculate_all_user_levels_task():
    """
    Періодичне завдання для перерахунку рівнів всіх користувачів у всіх групах.
    Це може бути необхідно, якщо рівні залежать від накопичених очок або інших
    показників, які можуть змінюватися, а оновлення рівня в реальному часі
    є надто ресурсоємним або не потрібним.
    """
    logger.info("Запуск завдання перерахунку рівнів користувачів...")
    # db = None
    # try:
    #     db = SessionLocal()
    #     user_level_service = UserLevelService(db)
    #     group_service = GroupService(db) # Або сервіс, що надає всіх користувачів з їх активністю в групах
    #
    #     # Отримати всіх активних користувачів у всіх активних групах
    #     # або ітерувати по групах, потім по користувачах в них.
    #     # all_group_memberships = await group_service.get_all_active_group_memberships() # Приклад
    #
    #     # processed_users_count = 0
    #     # for membership in all_group_memberships:
    #     #     try:
    #     #         await user_level_service.update_user_level_based_on_score(
    #     #             user_id=membership.user_id,
    #     #             group_id=membership.group_id
    #     #         )
    #     #         processed_users_count +=1
    #     #     except Exception as e_user:
    #     #         logger.error(f"Помилка перерахунку рівня для user_id={membership.user_id} в group_id={membership.group_id}: {e_user}", exc_info=True)
    #
    #     # logger.info(f"Перерахунок рівнів завершено. Оброблено {processed_users_count} записів членства.")
    #     # return {"status": "completed", "processed_memberships": processed_users_count}
    #
    # except Exception as e:
    #     logger.error(f"Загальна помилка в завданні перерахунку рівнів: {e}", exc_info=True)
    #     # return {"status": "error", "message": str(e)}
    # finally:
    #     if db:
    #         db.close()

    logger.info("Завдання перерахунку рівнів користувачів завершено (ЗАГЛУШКА).")
    return {"status": "completed", "message": "User levels recalculation task finished (stub)."}

# Примітка: Якщо оновлення рівня відбувається миттєво при зміні очок/бонусів
# (наприклад, в сервісі транзакцій або виконання завдань),
# то окреме періодичне завдання для перерахунку може бути не потрібне,
# або воно може виконувати лише коригуючі функції.
