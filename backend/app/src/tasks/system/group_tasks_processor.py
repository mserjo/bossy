# backend/app/src/tasks/system/group_tasks_processor.py
# -*- coding: utf-8 -*-
"""
Фонове завдання для обробки специфічних для груп повторюваних завдань.
"""
from backend.app.src.config.logging import get_logger
# TODO: Імпортувати екземпляр Celery app
# from backend.app.src.workers import celery_app as app # Приклад
# TODO: Імпортувати сервіси для роботи з групами, користувачами, налаштуваннями груп, бонусами
# from backend.app.src.services.group.group_service import GroupService
# from backend.app.src.services.auth.user_service import UserService
# from backend.app.src.services.group.group_settings_service import GroupSettingsService
# from backend.app.src.services.bonus.transaction_service import TransactionService
# from backend.app.src.config.database import SessionLocal
# from datetime import date, datetime

logger = get_logger(__name__)

# @app.task(name="tasks.system.group_tasks_processor.process_all_group_recurring_tasks") # Приклад для Celery
def process_all_group_recurring_tasks():
    """
    Періодичне завдання, що ітерує по всіх активних групах та їх учасниках
    для виконання специфічних групових повторюваних дій, таких як:
    - Привітання з Днем Народження та нарахування бонусів (якщо налаштовано в групі).
    - Нарахування бонусів за річницю перебування в групі (якщо налаштовано).
    - Інші подібні завдання, що визначаються налаштуваннями групи.
    """
    logger.info("Запуск завдання обробки групових повторюваних завдань...")
    # db = None
    # try:
    #     db = SessionLocal()
    #     group_service = GroupService(db)
    #     user_service = UserService(db) # Для отримання деталей користувачів (дата народження, дата приєднання до групи)
    #     settings_service = GroupSettingsService(db) # Для отримання налаштувань групи (чи активовані такі бонуси, їх розмір)
    #     transaction_service = TransactionService(db) # Для нарахування бонусів
    #
    #     active_groups = await group_service.get_all_active_groups() # Потрібен такий метод
    #
    #     today = date.today()
    #
    #     for group in active_groups:
    #         logger.debug(f"Обробка групи: {group.name} (ID: {group.id})")
    #         group_settings = await settings_service.get_settings_for_group(group.id) # Або кешовані налаштування
    #
    #         if not group_settings:
    #             logger.warning(f"Не знайдено налаштувань для групи {group.id}, пропуск.")
    #             continue
    #
    #         group_members = await group_service.get_group_members_details(group.id) # Метод, що повертає UserModels з датою вступу в групу
    #
    #         for member_info in group_members: # member_info може бути об'єктом з user_model та joined_date_in_group
    #             user = member_info.user # UserModel
    #
    #             # 1. Перевірка Дня Народження
    #             if group_settings.birthday_bonus_enabled and user.date_of_birth:
    #                 if user.date_of_birth.month == today.month and user.date_of_birth.day == today.day:
    #                     logger.info(f"Сьогодні День Народження у користувача {user.email} (ID: {user.id}) з групи {group.name}!")
    #                     # TODO: Перевірити, чи вже нараховано бонус сьогодні (щоб уникнути дублів при частих запусках)
    #                     # await transaction_service.create_birthday_bonus(
    #                     #     user_id=user.id,
    #                     #     group_id=group.id,
    #                     #     amount=group_settings.birthday_bonus_amount,
    #                     #     actor_id=SYSTEM_SHADOW_USER_ID # ID системного користувача
    #                     # )
    #                     logger.info(f"Нараховано бонус за ДН (ЗАГЛУШКА) для {user.email} в групі {group.name}.")
    #
    #             # 2. Перевірка річниці в групі
    #             if group_settings.anniversary_bonus_enabled and member_info.joined_at_group: # joined_at_group - дата вступу в конкретну групу
    #                 # Перевіряємо, чи сьогодні річниця (без урахування року, якщо бонус щорічний)
    #                 if member_info.joined_at_group.month == today.month and member_info.joined_at_group.day == today.day:
    #                     years_in_group = today.year - member_info.joined_at_group.year
    #                     if years_in_group > 0: # Не нараховувати в день вступу, а тільки на річниці
    #                         logger.info(f"Сьогодні {years_in_group}-а річниця в групі {group.name} для користувача {user.email}!")
    #                         # TODO: Перевірити, чи вже нараховано
    #                         # await transaction_service.create_anniversary_bonus(
    #                         #     user_id=user.id,
    #                         #     group_id=group.id,
    #                         #     amount=group_settings.anniversary_bonus_amount, # Може залежати від кількості років
    #                         #     years=years_in_group,
    #                         #     actor_id=SYSTEM_SHADOW_USER_ID
    #                         # )
    #                         logger.info(f"Нараховано бонус за річницю (ЗАГЛУШКА) для {user.email} в групі {group.name}.")
    #
    #             # TODO: Інші можливі групові періодичні завдання
    #
    # except Exception as e:
    #     logger.error(f"Помилка в завданні обробки групових повторюваних завдань: {e}", exc_info=True)
    # finally:
    #     if db:
    #         db.close()

    logger.info("Завдання обробки групових повторюваних завдань завершено (ЗАГЛУШКА).")
    return {"status": "completed", "message": "Group recurring tasks processing finished (stub)."}

# Потрібно визначити SYSTEM_SHADOW_USER_ID в константах або налаштуваннях.
