# backend/app/src/tasks/gamification/levels.py
# -*- coding: utf-8 -*-
"""
Модуль для завдання перерахунку рівнів користувачів.

Визначає `RecalculateUserLevelsTask`, відповідальний за періодичний
перерахунок рівнів користувачів на основі їх активності,
накопичених балів або інших критеріїв гейміфікації.
"""

import asyncio
import logging
from typing import Any, Dict, Optional, List

from app.src.tasks.base import BaseTask
# from app.src.services.user_service import UserService # Для отримання даних користувачів
# from app.src.services.gamification_service import GamificationService # Для логіки рівнів
# from app.src.tasks.notifications.messenger import SendMessengerNotificationTask # Для сповіщень
# from app.src.tasks.gamification.badges import AwardBadgesTask # Для видачі бейджів за рівень

# Налаштування логера для цього модуля
logger = logging.getLogger(__name__)

# Приклад визначення рівнів (має бути в конфігурації або моделі даних GamificationService)
LEVEL_THRESHOLDS_EXAMPLE = {
    1: 0,    # Рівень 1: 0-99 балів
    2: 100,  # Рівень 2: 100-249 балів
    3: 250,  # Рівень 3: 250-499 балів
    4: 500,  # Рівень 4: 500-999 балів
    5: 1000, # Рівень 5: 1000+ балів
}

class RecalculateUserLevelsTask(BaseTask):
    """
    Завдання для періодичного перерахунку рівнів користувачів.

    Це завдання може обробляти всіх користувачів або конкретного користувача.
    Логіка визначення рівня (наприклад, за кількістю балів досвіду)
    має бути реалізована в відповідному сервісі (`GamificationService`).
    Після зміни рівня може ініціювати завдання для сповіщення користувача
    та видачі відповідних бейджів.
    """

    def __init__(self, name: str = "RecalculateUserLevelsTask"):
        """
        Ініціалізація завдання перерахунку рівнів.
        """
        super().__init__(name)
        # У реальній системі:
        # self.user_service = UserService()
        # self.gamification_service = GamificationService()
        # self.level_thresholds = self.gamification_service.get_level_definitions()
        self.level_thresholds = LEVEL_THRESHOLDS_EXAMPLE # Використовуємо приклад для заглушки

        # Можна ініціалізувати інші таски, якщо цей таск буде їх викликати напряму
        # self.award_badges_task = AwardBadgesTask()
        # self.notify_user_task = SendMessengerNotificationTask() # Або інший таск сповіщень

    async def _get_users_for_recalculation(self, user_id: Optional[Any] = None) -> List[Any]:
        """
        Отримує список ID користувачів для перерахунку рівнів.
        Якщо user_id надано, повертає список з одним цим ID.
        Якщо user_id не надано, концептуально повертає всіх активних користувачів.
        У реалізації це може бути вибірка користувачів, чия активність змінилася,
        або тих, хто ще не має розрахованого рівня.
        """
        if user_id is not None: # Дозволяє user_id=0, якщо це валідний ID
            self.logger.info(f"Підготовка до перерахунку рівня для конкретного user_id: {user_id}")
            # user = await self.user_service.get_user_by_id(user_id)
            # return [user.id] if user else []
            return [user_id] # Заглушка
        else:
            self.logger.info("Підготовка до перерахунку рівнів для всіх активних користувачів (заглушка).")
            # У реальній системі:
            # user_ids = await self.user_service.get_all_active_user_ids_for_level_recalc()
            # return user_ids
            await asyncio.sleep(0.02) # Імітація запиту до БД
            # Приклади ID для демонстрації різних сценаріїв
            return ["user_1_newbie", "user_2_mid", "user_3_leveled_up", "user_4_max_level", "user_5_no_change"]

    async def _calculate_and_update_level(self, user_id: Any) -> Dict[str, Any]:
        """
        Заглушка для розрахунку та оновлення рівня конкретного користувача.
        Включає імітацію отримання даних, розрахунок нового рівня, оновлення в БД
        та потенційний виклик завдань для видачі бейджа та сповіщення.
        """
        self.logger.debug(f"Перерахунок рівня для user_id: {user_id} (заглушка).")

        # --- Початок блоку реальної логіки (концептуально) ---
        # try:
        #     # 1. Отримати поточні дані користувача (бали, поточний рівень)
        #     # user_gamification_data = await self.gamification_service.get_user_gamification_profile(user_id)
        #     # if not user_gamification_data:
        #     #     self.logger.warning(f"Не знайдено профіль гейміфікації для user_id '{user_id}'.")
        #     #     return {"user_id": user_id, "error": "Gamification profile not found", "changed": False}
        #     # user_points = user_gamification_data.experience_points
        #     # current_level = user_gamification_data.current_level
        #     # current_level_name = user_gamification_data.current_level_name

        # Імітація даних для заглушки:
        user_points_map = {
            "user_1_newbie": 50, "user_2_mid": 150, "user_3_leveled_up": 550,
            "user_4_max_level": 1200, "user_5_no_change": 300
        }
        current_level_map = {
            "user_1_newbie": 1, "user_2_mid": 2, "user_3_leveled_up": 3, # Цей користувач підніме рівень
            "user_4_max_level": 5, "user_5_no_change": 3
        }
        user_points = user_points_map.get(user_id, 0)
        current_level = current_level_map.get(user_id, 0)

        #     # 2. Визначити новий рівень на основі балів та порогів
        #     # new_level_info = self.gamification_service.determine_level_from_points(user_points)
        #     # new_level = new_level_info.level_number
        #     # new_level_name = new_level_info.level_name

        # Імітація розрахунку нового рівня на основі self.level_thresholds
        new_level = 0
        # sorted_thresholds = sorted(self.level_thresholds.items(), key=lambda item: item[1], reverse=True)
        # for level, threshold in sorted_thresholds:
        #     if user_points >= threshold:
        #         new_level = level
        #         break
        # if new_level == 0: new_level = 1 # Мінімальний рівень
        # new_level_name = f"Рівень {new_level}" # Зазвичай назва рівня береться з конфігурації

        # Простіша імітація для прикладу:
        if user_points >= self.level_thresholds[5]: new_level = 5
        elif user_points >= self.level_thresholds[4]: new_level = 4
        elif user_points >= self.level_thresholds[3]: new_level = 3
        elif user_points >= self.level_thresholds[2]: new_level = 2
        else: new_level = 1
        new_level_name = f"Рівень {new_level}"


        #     # 3. Якщо рівень змінився, оновити його в БД
        #     if new_level != current_level:
        #         # await self.gamification_service.update_user_level(user_id, new_level, new_level_name, user_points)
        #         self.logger.info(f"Рівень користувача user_id '{user_id}' змінено з {current_level} на {new_level} ('{new_level_name}'). Бали: {user_points}.")
        #
        #         # 4. Ініціювати завдання для видачі бейджа за досягнення рівня (якщо є)
        #         # badge_for_level = await self.gamification_service.get_badge_for_level_achievement(new_level)
        #         # if badge_for_level:
        #         #     await self.award_badges_task.execute(user_id=user_id, badge_id=badge_for_level.id, reason="level_up")
        #
        #         # 5. Ініціювати завдання для сповіщення користувача про новий рівень
        #         # user_profile = await self.user_service.get_user_profile(user_id) # Для отримання chat_id, email тощо
        #         # if user_profile and user_profile.telegram_chat_id:
        #         #    notification_message = f"Вітаємо! Ви досягли нового рівня: {new_level_name}!"
        #         #    await self.notify_user_task.execute(
        #         #        target_identifier=user_profile.telegram_chat_id,
        #         #        message_text=notification_message,
        #         #        platform="telegram"
        #         #    )
        #         return {"user_id": user_id, "old_level": current_level, "new_level": new_level, "changed": True, "points": user_points, "level_name": new_level_name}
        #     else:
        #         # self.logger.debug(f"Рівень користувача user_id '{user_id}' не змінився (Рівень: {current_level}, Бали: {user_points}).")
        #         # Можливо, оновити тільки час останньої перевірки рівня
        #         # await self.gamification_service.update_last_level_check_timestamp(user_id)
        #         return {"user_id": user_id, "old_level": current_level, "new_level": new_level, "changed": False, "points": user_points, "level_name": current_level_name}
        #
        # except Exception as e:
        #     self.logger.error(f"Помилка перерахунку рівня для user_id '{user_id}': {e}", exc_info=True)
        #     return {"user_id": user_id, "error": str(e), "changed": False}
        # --- Кінець блоку реальної логіки ---

        await asyncio.sleep(0.01) # Імітація обробки та запитів до БД

        changed = new_level != current_level
        if changed:
            self.logger.info(f"Рівень user_id '{user_id}' змінено: {current_level} -> {new_level} ('{new_level_name}'). Бали: {user_points}.")
        else:
            self.logger.debug(f"Рівень user_id '{user_id}' не змінився: {current_level}. Бали: {user_points}.")

        return {"user_id": user_id, "old_level": current_level, "new_level": new_level, "changed": changed, "points": user_points, "level_name": new_level_name if changed else f"Рівень {current_level}"}


    async def run(self, user_id: Optional[Any] = None, **kwargs: Any) -> Dict[str, Any]:
        """
        Виконує перерахунок рівнів для вказаного користувача або для всіх.

        Args:
            user_id (Optional[Any]): ID конкретного користувача для перерахунку.
                                     Якщо None, перераховуються рівні для всіх релевантних користувачів.
            **kwargs: Додаткові аргументи (наразі не використовуються, але можуть бути
                      використані для фільтрації користувачів або зміни логіки).

        Returns:
            Dict[str, Any]: Результат операції, що містить статистику по змінених рівнях.
        """
        self.logger.info(f"Завдання '{self.name}' розпочало перерахунок рівнів користувачів.")
        if user_id is not None:
            self.logger.info(f"Цільовий user_id: {user_id}.")
        else:
            self.logger.info("Перерахунок для всіх релевантних користувачів (заглушка).")

        users_to_process = await self._get_users_for_recalculation(user_id)

        if not users_to_process:
            self.logger.info("Немає користувачів для перерахунку рівнів.")
            return {"status": "no_users_found", "users_processed_count": 0, "levels_changed_count": 0}

        results_summary: List[Dict[str, Any]] = []
        levels_changed_count = 0

        # Обробка користувачів може бути паралелізована, якщо _calculate_and_update_level є незалежною
        # і сервіси, які вона використовує, підтримують асинхронні/паралельні запити.
        # tasks_to_run = [self._calculate_and_update_level(uid) for uid in users_to_process]
        # processing_outcomes = await asyncio.gather(*tasks_to_run, return_exceptions=True)
        #
        # for outcome in processing_outcomes:
        #     if isinstance(outcome, Exception):
        #         self.logger.error(f"Помилка під час паралельної обробки рівня: {outcome}", exc_info=outcome)
        #         # Тут можна додати логіку для обробки помилки, наприклад, записати ID користувача, для якого сталася помилка
        #     elif outcome and isinstance(outcome, dict):
        #         results_summary.append(outcome) # Додаємо успішний результат
        #         if outcome.get("changed"):
        #             levels_changed_count +=1
        #     else:
        #         self.logger.warning(f"Несподіваний результат від _calculate_and_update_level: {outcome}")

        # Послідовна обробка для простоти заглушки та контролю логування:
        for uid_to_process in users_to_process:
            try:
                result = await self._calculate_and_update_level(uid_to_process)
                results_summary.append(result)
                if result.get("changed"): # Перевіряємо, чи ключ "changed" існує і чи він True
                    levels_changed_count += 1
            except Exception as e:
                self.logger.error(f"Не вдалося обробити рівень для user_id '{uid_to_process}': {e}", exc_info=True)
                results_summary.append({"user_id": uid_to_process, "error": str(e), "changed": False}) # Додаємо інформацію про помилку

        final_summary_message = (
            f"Перерахунок рівнів завершено. Оброблено користувачів: {len(users_to_process)}. "
            f"Змінено рівнів: {levels_changed_count}."
        )
        self.logger.info(final_summary_message)

        return {
            "status": "completed",
            "summary": final_summary_message,
            "users_processed_count": len(users_to_process),
            "levels_changed_count": levels_changed_count,
            # "details": results_summary # Може бути дуже великим, тому зазвичай не повертається повністю.
                                       # Краще логувати деталі або зберігати їх окремо.
                                       # Для заглушки можна повернути, щоб бачити результат.
            "details_sample": results_summary[:5] # Приклад повернення лише частини деталей
        }

# Приклад використання (можна видалити або закоментувати):
# async def main():
#     logging.basicConfig(
#         level=logging.DEBUG, # DEBUG, щоб бачити логування з _calculate_and_update_level
#         format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
#     )
#     level_task = RecalculateUserLevelsTask()
#
#     logger.info("--- Перерахунок для всіх користувачів (заглушка) ---")
#     result_all = await level_task.execute()
#     logger.info(f"Результат (всі): {result_all['summary']}. Перші 5 деталей: {result_all['details_sample']}")
#
#     logger.info("\n--- Перерахунок для конкретного користувача (user_3_leveled_up) ---")
#     result_specific_level_up = await level_task.execute(user_id="user_3_leveled_up")
#     logger.info(f"Результат (user_3_leveled_up): {result_specific_level_up}")
#
#     logger.info("\n--- Перерахунок для іншого конкретного користувача (user_1_newbie) ---")
#     result_user1 = await level_task.execute(user_id="user_1_newbie")
#     logger.info(f"Результат (user_1_newbie): {result_user1}")
#
#     logger.info("\n--- Перерахунок для неіснуючого користувача (заглушка) ---")
#     result_non_existent = await level_task.execute(user_id="non_existent_user_id")
#     logger.info(f"Результат (неіснуючий): {result_non_existent}")


# if __name__ == "__main__":
#     # Для Windows може знадобитися: asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
#     asyncio.run(main())
