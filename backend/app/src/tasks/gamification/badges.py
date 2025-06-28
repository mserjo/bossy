# backend/app/src/tasks/gamification/badges.py
# -*- coding: utf-8 -*-
"""
Фонові завдання, пов'язані з бейджами та досягненнями.
"""
from backend.app.src.config.logging import get_logger
# TODO: Імпортувати екземпляр Celery app
# from backend.app.src.workers import celery_app as app # Приклад
# TODO: Імпортувати сервіси
# from backend.app.src.services.gamification.achievement_service import AchievementService # Для видачі бейджів
# from backend.app.src.services.gamification.badge_service import BadgeService # Для отримання умов бейджів
# from backend.app.src.services.group.group_service import GroupService # Для ітерації по групах/користувачах
# from backend.app.src.config.database import SessionLocal

logger = get_logger(__name__)

# @app.task(name="tasks.gamification.badges.award_periodic_activity_badges_task") # Приклад для Celery
def award_periodic_activity_badges_task():
    """
    Періодичне завдання для перевірки та видачі бейджів користувачам,
    які виконали певні умови (наприклад, за активність за період,
    досягнення певного числа виконаних завдань певного типу тощо).
    """
    logger.info("Запуск завдання видачі періодичних/активностних бейджів...")
    # db = None
    # try:
    #     db = SessionLocal()
    #     achievement_service = AchievementService(db)
    #     badge_service = BadgeService(db) # Для отримання визначень бейджів та їх умов
    #     group_service = GroupService(db)
    #
    #     # 1. Отримати список всіх "автоматичних" бейджів, які можуть видаватися періодично або за умовою
    #     # automatable_badges = await badge_service.get_automatable_badges()
    #
    #     # for badge_definition in automatable_badges:
    #     #     logger.debug(f"Перевірка умов для бейджа: {badge_definition.name} (ID: {badge_definition.id})")
    #     #     # 2. Для кожного такого бейджа отримати користувачів, які потенційно можуть його отримати
    #     #     # (наприклад, всі активні користувачі в групі, до якої належить бейдж).
    #     #     # users_in_scope = await group_service.get_users_for_badge_check(badge_definition.group_id)
    #     #
    #     #     # for user in users_in_scope:
    #     #     #     # 3. Перевірити, чи виконав користувач умови для цього бейджа
    #     #     #     # (ця логіка може бути в AchievementService або BadgeService)
    #     #     #     # has_already_achieved = await achievement_service.has_user_achieved_badge(user.id, badge_definition.id)
    #     #     #     # if not has_already_achieved:
    #     #     #     #     conditions_met = await achievement_service.check_badge_conditions_for_user(
    #     #     #     #         user_id=user.id,
    #     #     #     #         badge_id=badge_definition.id,
    #     #     #     #         # badge_criteria=badge_definition.criteria # Якщо умови зберігаються з бейджем
    #     #     #     #     )
    #     #     #     #     if conditions_met:
    #     #     #     #         await achievement_service.award_badge_to_user(
    #     #     #     #             user_id=user.id,
    #     #     #     #             badge_id=badge_definition.id,
    #     #     #     #             group_id=badge_definition.group_id,
    #     #     #     #             awarded_by_system=True
    #     #     #     #         )
    #     #     #     #         logger.info(f"Бейдж '{badge_definition.name}' видано користувачу {user.email} (ЗАГЛУШКА).")
    #
    #     # logger.info(f"Видача періодичних бейджів завершена.")
    #     # return {"status": "completed", "badges_checked": len(automatable_badges)}
    #
    # except Exception as e:
    #     logger.error(f"Помилка в завданні видачі періодичних бейджів: {e}", exc_info=True)
    #     # return {"status": "error", "message": str(e)}
    # finally:
    #     if db:
    #         db.close()

    logger.info("Завдання видачі періодичних/активностних бейджів завершено (ЗАГЛУШКА).")
    return {"status": "completed", "message": "Periodic badges awarding task finished (stub)."}

# Примітка: Видача бейджів може також відбуватися миттєво при виконанні певних дій
# (наприклад, завершення завдання, досягнення рівня) всередині відповідних сервісів.
# Це завдання призначене для бейджів, умови яких перевіряються періодично.
