# backend/app/src/tasks/gamification/badges.py
# -*- coding: utf-8 -*-
"""
Модуль для завдання видачі бейджів користувачам.

Визначає `AwardBadgesTask`, відповідальний за перевірку умов
та видачу бейджів користувачам на основі їхніх досягнень,
виконаних завдань, участі в подіях тощо.
"""

import asyncio
from typing import Any, Dict, Optional, List

from app.src.tasks.base import BaseTask
# from app.src.services.user_service import UserService # Для отримання даних користувачів
# from app.src.services.gamification_service import GamificationService # Для логіки бейджів
# from app.src.tasks.notifications.messenger import SendMessengerNotificationTask # Для сповіщень

from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Приклад визначення бейджів та їх критеріїв (має бути в конфігурації або моделі даних GamificationService)
BADGE_DEFINITIONS_EXAMPLE = {
    "first_task_completed_stub": {
        "name": "Першопроходець Завдань (Заглушка)",
        "description": "Завершив своє перше завдання.",
        "criteria_type": "event",
        "event_trigger": "task_completed",
        "event_condition_description": "user_total_completed_tasks == 1"
        # "event_condition": lambda data: data.get("user_total_completed_tasks") == 1
    },
    "power_player_lvl5_stub": {
        "name": "Гравець 5-го Рівня (Заглушка)",
        "description": "Досягнув 5-го рівня.",
        "criteria_type": "event",
        "event_trigger": "level_up",
        "event_condition_description": "new_level == 5"
        # "event_condition": lambda data: data.get("new_level") == 5
    },
    "streak_5_days_stub": { # Цей бейдж перевірятиметься періодично
        "name": "Тижневий Стрік (Заглушка)",
        "description": "Виконував завдання 5 днів поспіль.",
        "criteria_type": "custom_check",
        "check_function_name": "_check_5_day_streak_stub"
    },
    "periodic_badge_stub": { # Ще один для періодичної перевірки
        "name": "Активний Учасник (Заглушка)",
        "description": "Проявив активність цього тижня.",
        "criteria_type": "custom_check",
        "check_function_name": "_check_weekly_activity_stub"
    }
}

class AwardBadgesTask(BaseTask):
    """
    Завдання для перевірки та видачі бейджів користувачам.

    Може спрацьовувати на основі різних подій (наприклад, завершення завдання,
    підвищення рівня) або періодично перевіряти умови для всіх користувачів.
    Логіка визначення та видачі бейджів має бути реалізована
    в `GamificationService`, а визначення бейджів - у конфігурації або БД.
    """

    def __init__(self, name: str = "AwardBadgesTask"):
        """
        Ініціалізація завдання видачі бейджів.
        """
        super().__init__(name)
        # У реальній системі:
        # self.user_service = UserService()
        # self.gamification_service = GamificationService()
        # self.badge_definitions = self.gamification_service.get_badge_definitions()
        self.badge_definitions = BADGE_DEFINITIONS_EXAMPLE # Використовуємо приклад для заглушки
        # self.notify_user_task = SendMessengerNotificationTask()

    async def _get_applicable_badges_for_event(
        self, user_id: Any, event_type: str, event_data: Dict[str, Any]
    ) -> List[str]:
        """
        Заглушка: Визначає, які бейджі можуть бути видані користувачу на основі конкретної події.
        """
        self.logger.debug(
            f"Перевірка бейджів за подією для user_id '{user_id}', event_type='{event_type}', data={event_data} (заглушка)."
        )
        applicable_badge_ids: List[str] = []

        # --- Початок блоку реальної логіки ---
        # for badge_id, definition in self.badge_definitions.items():
        #     if definition.get("criteria_type") == "event" and definition.get("event_trigger") == event_type:
        #         condition_func = definition.get("event_condition") # Це має бути реальна функція
        #         if callable(condition_func):
        #             # Передача необхідних даних у функцію умови
        #             # Наприклад, if condition_func(event_data, user_profile_data):
        #             if condition_func(event_data): # Спрощено для прикладу
        #                 applicable_badge_ids.append(badge_id)
        #         elif "event_condition_description" in definition : # Якщо умова просто описана
        #              # Імітуємо перевірку на основі опису (дуже спрощено)
        #              if definition["event_condition_description"] == "new_level == 5" and event_data.get("new_level") == 5:
        #                  applicable_badge_ids.append(badge_id)
        #              elif definition["event_condition_description"] == "user_total_completed_tasks == 1" and event_data.get("user_total_completed_tasks") == 1:
        #                  applicable_badge_ids.append(badge_id)
        #         else: # Якщо умови немає, будь-яка подія цього типу підходить
        #             applicable_badge_ids.append(badge_id)
        # --- Кінець блоку реальної логіки ---

        await asyncio.sleep(0.01) # Імітація перевірки умов

        # Імітація логіки для заглушки на основі BADGE_DEFINITIONS_EXAMPLE:
        if event_type == "level_up" and event_data.get("new_level") == 5:
            applicable_badge_ids.append("power_player_lvl5_stub")
        if event_type == "task_completed" and event_data.get("user_total_completed_tasks") == 1:
             applicable_badge_ids.append("first_task_completed_stub")

        if applicable_badge_ids:
            self.logger.info(f"Знайдено {len(applicable_badge_ids)} потенційних бейджів ({applicable_badge_ids}) за подією для user_id '{user_id}'.")
        return applicable_badge_ids

    async def _check_and_award_badge(self, user_id: Any, badge_id: str) -> bool:
        """
        Заглушка: Перевіряє, чи користувач вже має бейдж, і якщо ні - видає його.
        Повертає True, якщо бейдж було щойно видано, False в іншому випадку.
        """
        self.logger.debug(f"Перевірка та видача бейджа '{badge_id}' для user_id '{user_id}' (заглушка).")

        # --- Початок блоку реальної логіки ---
        # try:
        #     has_badge = await self.gamification_service.user_has_badge(user_id, badge_id)
        #     if not has_badge:
        #         badge_info = self.badge_definitions.get(badge_id)
        #         if not badge_info:
        #             self.logger.warning(f"Визначення для бейджа '{badge_id}' не знайдено.")
        #             return False
        #
        #         await self.gamification_service.award_badge_to_user(user_id, badge_id, badge_info.get("name"))
        #         self.logger.info(f"Бейдж '{badge_info.get('name', badge_id)}' видано user_id '{user_id}'.")
        #
        #         # Ініціювати сповіщення користувача про новий бейдж
        #         # user_profile = await self.user_service.get_user_profile(user_id)
        #         # if user_profile and user_profile.telegram_chat_id: # Або інший канал
        #         #    message = f"Вітаємо! Ви отримали новий бейдж: {badge_info.get('name')} - {badge_info.get('description')}"
        #         #    await self.notify_user_task.execute(target_identifier=user_profile.telegram_chat_id, message_text=message, platform="telegram")
        #         return True # Бейдж видано
        #     else:
        #         # self.logger.debug(f"Користувач user_id '{user_id}' вже має бейдж '{badge_id}'.")
        #         return False # Бейдж вже є
        # except Exception as e:
        #     self.logger.error(f"Помилка при перевірці/видачі бейджа '{badge_id}' для user_id '{user_id}': {e}", exc_info=True)
        #     return False
        # --- Кінець блоку реальної логіки ---

        await asyncio.sleep(0.01) # Імітація запиту до БД

        # Імітація для заглушки: видаємо бейдж, якщо користувач не "user_has_all_badges"
        # і бейдж не "first_task_completed_stub" для користувача "test_user_1" (щоб імітувати, що він вже є)
        if user_id == "user_has_all_badges":
            self.logger.debug(f"Користувач '{user_id}' (заглушка) вже має бейдж '{badge_id}'.")
            return False
        if badge_id == "first_task_completed_stub" and user_id == "test_user_1": # Імітуємо, що він вже є
             self.logger.debug(f"Користувач '{user_id}' (заглушка) вже має бейдж '{badge_id}'.")
             return False

        badge_name = self.badge_definitions.get(badge_id, {}).get("name", badge_id)
        self.logger.info(f"Бейдж '{badge_name}' (заглушка) видано user_id '{user_id}'.")
        return True


    async def _run_for_specific_event(
        self, user_id: Any, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Обробляє видачу бейджів для конкретної події конкретного користувача."""
        self.logger.info(f"Обробка бейджів за подією для user_id='{user_id}', event='{event_type}'.")
        badges_to_check = await self._get_applicable_badges_for_event(user_id, event_type, event_data)

        awarded_count = 0
        awarded_badges_ids: List[str] = []

        if not badges_to_check:
            self.logger.info(f"Для user_id='{user_id}', event='{event_type}' немає застосовних бейджів за подією.")

        for badge_id in badges_to_check:
            try:
                was_awarded = await self._check_and_award_badge(user_id, badge_id)
                if was_awarded:
                    awarded_count += 1
                    awarded_badges_ids.append(badge_id)
            except Exception as e: # Захист від помилок в _check_and_award_badge
                 self.logger.error(f"Помилка під час спроби видачі бейджа '{badge_id}' для user_id '{user_id}' (подія '{event_type}'): {e}", exc_info=True)

        return {
            "user_id": user_id,
            "event_type": event_type,
            "event_data": event_data,
            "applicable_badges_ids_by_event": badges_to_check,
            "badges_awarded_now_count": awarded_count,
            "awarded_badges_ids_now": awarded_badges_ids
        }

    async def _run_for_all_users_periodic_check(self) -> Dict[str, Any]:
        """
        Заглушка: Періодично перевіряє умови для бейджів, які не залежать від миттєвих подій
        (наприклад, "тижневий стрік", "1000 балів досвіду", бейджі за "custom_check").
        """
        self.logger.info("Періодична перевірка 'custom_check' та 'milestone' бейджів для всіх користувачів (заглушка).")

        # --- Початок блоку реальної логіки ---
        # user_ids_to_check = await self.user_service.get_all_active_user_ids() # Або вибірка користувачів
        # total_badges_awarded_this_run = 0
        # users_processed_count = len(user_ids_to_check)
        # detailed_results = []
        #
        # for user_id in user_ids_to_check:
        #     user_badges_awarded_count = 0
        #     for badge_id, definition in self.badge_definitions.items():
        #         if definition.get("criteria_type") == "custom_check":
        #             check_func_name = definition.get("check_function_name")
        #             if hasattr(self.gamification_service, check_func_name): # Перевіряємо в сервісі
        #                 check_passed = await getattr(self.gamification_service, check_func_name)(user_id)
        #                 if check_passed:
        #                     if await self._check_and_award_badge(user_id, badge_id):
        #                         user_badges_awarded_count += 1
        #         elif definition.get("criteria_type") == "milestone":
        #             # Логіка перевірки досягнень (milestones), наприклад, по балах, кількості виконаних завдань тощо.
        #             # user_points = await self.gamification_service.get_user_points(user_id)
        #             # if user_points >= definition.get("milestone_points", float('inf')):
        #             #    if await self._check_and_award_badge(user_id, badge_id):
        #             #        user_badges_awarded_count += 1
        #             pass # Додати логіку для milestone
        #     if user_badges_awarded_count > 0:
        #         total_badges_awarded_this_run += user_badges_awarded_count
        #         detailed_results.append({"user_id": user_id, "awarded_count": user_badges_awarded_count})
        #
        # self.logger.info(f"Періодична перевірка бейджів завершена. Оброблено {users_processed_count} користувачів. "
        #                  f"Видано {total_badges_awarded_this_run} бейджів.")
        # return {"users_processed_count": users_processed_count, "total_badges_awarded_this_run": total_badges_awarded_this_run, "details": detailed_results}
        # --- Кінець блоку реальної логіки ---

        await asyncio.sleep(0.05) # Імітація обробки

        # Імітація: видаємо "periodic_badge_stub" та "streak_5_days_stub" користувачу "user_gets_periodic_badge"
        user_id_for_periodic = "user_gets_periodic_badge"
        awarded_this_run_count = 0
        awarded_ids_this_run = []

        # Імітуємо, що _check_5_day_streak_stub повернув True для цього користувача
        if await self._check_and_award_badge(user_id_for_periodic, "streak_5_days_stub"):
            awarded_this_run_count +=1
            awarded_ids_this_run.append("streak_5_days_stub")

        # Імітуємо, що _check_weekly_activity_stub повернув True
        if await self._check_and_award_badge(user_id_for_periodic, "periodic_badge_stub"):
            awarded_this_run_count += 1
            awarded_ids_this_run.append("periodic_badge_stub")

        return {
            "users_processed_count": 1, # Імітуємо обробку одного користувача
            "total_badges_awarded_this_run": awarded_this_run_count,
            "details": [{"user_id": user_id_for_periodic, "awarded_ids": awarded_ids_this_run}] if awarded_this_run_count > 0 else []
        }


    async def run(
        self,
        user_id: Optional[Any] = None,
        event_type: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any # Додаткові аргументи, наприклад, specific_badge_id_to_check
    ) -> Dict[str, Any]:
        """
        Виконує перевірку та видачу бейджів.

        - Якщо `event_type` та `user_id` надані: обробляє бейджі для цієї події користувача.
        - Якщо `user_id` надано, а `event_type` ні: (Потенційно) перевіряє всі умови для цього користувача.
          У поточній заглушці цей випадок не реалізовано детально і видасть попередження.
        - Якщо `user_id` та `event_type` не надані: виконує періодичну перевірку для всіх користувачів.
        - Якщо `specific_badge_id_to_check` надано в kwargs разом з `user_id`: перевіряє конкретний бейдж.

        Args:
            user_id (Optional[Any]): ID користувача.
            event_type (Optional[str]): Тип події (наприклад, "task_completed", "level_up").
            event_data (Optional[Dict[str, Any]]): Дані, пов'язані з подією.
            **kwargs: `specific_badge_id_to_check` (str) - ID конкретного бейджа для перевірки.

        Returns:
            Dict[str, Any]: Результат операції.
        """
        self.logger.info(f"Завдання '{self.name}' розпочало процес видачі бейджів (user_id='{user_id}', event_type='{event_type}').")

        specific_badge_id_to_check = kwargs.get("specific_badge_id_to_check")

        if specific_badge_id_to_check and user_id:
            self.logger.info(f"Перевірка конкретного бейджа '{specific_badge_id_to_check}' для user_id '{user_id}'.")
            # Потрібна логіка для перевірки умов саме цього бейджа.
            # Це може включати виклик check_function або перевірку даних користувача.
            # Для заглушки просто спробуємо його видати:
            was_awarded = await self._check_and_award_badge(user_id, specific_badge_id_to_check)
            return {
                "status": "completed_specific_badge_check",
                "user_id": user_id,
                "badge_id_checked": specific_badge_id_to_check,
                "was_awarded_now": was_awarded
            }
        elif event_type and user_id is not None: # user_id може бути 0, тому is not None
            self.logger.debug(f"Обробка на основі події: user_id='{user_id}', event_type='{event_type}'.")
            result_data = await self._run_for_specific_event(user_id, event_type, event_data or {})
            return { "status": "completed_event_driven_check", **result_data }
        elif user_id is not None and not event_type:
            # Цей випадок може бути використаний для перевірки всіх "milestone" або "custom_check"
            # бейджів для одного користувача, наприклад, після зміни його даних.
            self.logger.warning(f"Перевірка всіх бейджів для user_id '{user_id}' (без конкретної події) "
                                f"ще не повністю реалізована в цій заглушці (буде викликано періодичну).")
            # У заглушці можна тимчасово викликати логіку, схожу на періодичну, але для одного користувача.
            # Або просто повернути повідомлення. Для даної заглушки, це буде оброблено як періодична,
            # що не зовсім коректно, але для прикладу.
            # Краще було б мати окремий метод _run_user_specific_milestone_checks(user_id)
            # Поки що, для заглушки, цей випадок не буде оброблятися окремо від загальної періодичної.
            # Повернемо інформативне повідомлення, щоб не викликати повну періодичну перевірку.
            return {"status": "skipped_user_specific_no_event_stub", "user_id": user_id,
                    "info": "This mode (user-specific check without event) needs specific implementation beyond current stub."}
        elif not user_id and not event_type: # Періодична перевірка для всіх
            self.logger.info("Запуск періодичної перевірки бейджів для всіх користувачів.")
            result_data = await self._run_for_all_users_periodic_check()
            return { "status": "completed_periodic_all_users_check", **result_data }
        else: # event_type є, а user_id немає - нелогічний випадок для більшості подій
             error_msg = f"Некоректний виклик AwardBadgesTask: event_type='{event_type}' надано без user_id."
             self.logger.warning(error_msg)
             return {"status": "error_invalid_parameters", "error": error_msg}


# # Приклад використання (можна видалити або закоментувати):
# # async def main():
# #     logging.basicConfig(
# #         level=logging.DEBUG, # DEBUG для детального логування
# #         format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# #     )
# #     badge_task = AwardBadgesTask()
# #
# #     logger.info("--- Тест 1: Видача бейджа за подією 'level_up' (користувач test_user_lvl_up) ---")
# #     result_levelup = await badge_task.execute(
# #         user_id="test_user_lvl_up",
# #         event_type="level_up",
# #         event_data={"new_level": 5, "old_level": 4} # new_level=5 має видати power_player_lvl5_stub
# #     )
# #     logger.info(f"Результат (level_up): {result_levelup}")
# #
# #     logger.info("\n--- Тест 2: Видача бейджа за подією 'task_completed' (перше завдання для test_user_first_task) ---")
# #     result_task_first = await badge_task.execute(
# #         user_id="test_user_first_task",
# #         event_type="task_completed",
# #         event_data={"task_id": "task_abc", "user_total_completed_tasks": 1} # має видати first_task_completed_stub
# #     )
# #     logger.info(f"Результат (task_completed, first): {result_task_first}")
# #
# #     logger.info("\n--- Тест 3: Подія 'task_completed' (не перше завдання для test_user_lvl_up) ---")
# #     result_task_not_first = await badge_task.execute(
# #         user_id="test_user_lvl_up", # Цей користувач вже отримав power_player_lvl5_stub
# #         event_type="task_completed",
# #         event_data={"task_id": "task_def", "user_total_completed_tasks": 10} # не має видати first_task_completed_stub
# #     )
# #     logger.info(f"Результат (task_completed, not first): {result_task_not_first}")
# #
# #     logger.info("\n--- Тест 4: Періодична перевірка для всіх (заглушка) ---")
# #     result_periodic = await badge_task.execute()
# #     logger.info(f"Результат (періодична перевірка): {result_periodic}")
# #
# #     logger.info("\n--- Тест 5: Користувач 'user_has_all_badges' (імітація, що він вже має бейджі) ---")
# #     result_has_all = await badge_task.execute(
# #         user_id="user_has_all_badges",
# #         event_type="level_up",
# #         event_data={"new_level": 5} # Навіть якщо підходить під умову, бейдж не має видатися
# #     )
# #     logger.info(f"Результат (user_has_all_badges): {result_has_all}")
# #
# #     logger.info("\n--- Тест 6: Перевірка конкретного бейджа (якого ще немає) ---")
# #     result_specific_new = await badge_task.execute(
# #         user_id="test_user_specific_badge",
# #         specific_badge_id_to_check="streak_5_days_stub" # Цей бейдж видається тільки в періодичній заглушці іншому юзеру
# #     ) # Очікуємо, що він буде виданий, бо _check_and_award_badge не має складної логіки перевірки умов для заглушки
# #     logger.info(f"Результат (specific_badge_new): {result_specific_new}")
# #
# #     logger.info("\n--- Тест 7: Перевірка конкретного бейджа (який вже 'є' у user_has_all_badges) ---")
# #     result_specific_exists = await badge_task.execute(
# #         user_id="user_has_all_badges",
# #         specific_badge_id_to_check="power_player_lvl5_stub"
# #     )
# #     logger.info(f"Результат (specific_badge_exists): {result_specific_exists}")
# #
# #     logger.info("\n--- Тест 8: Виклик з user_id, але без event_type (має пропуститися згідно логіки заглушки) ---")
# #     result_user_no_event = await badge_task.execute(user_id="test_user_no_event")
# #     logger.info(f"Результат (user_id, no event_type): {result_user_no_event}")
# #
# #
# # if __name__ == "__main__":
# #     # Для Windows може знадобитися: asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# #     asyncio.run(main())
