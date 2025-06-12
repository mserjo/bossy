# backend/app/src/services/bonuses/calculation.py
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import timedelta, datetime, timezone  # Додано datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from backend.app.src.services.base import BaseService
from backend.app.src.models.bonuses.bonus import BonusRule  # Повний шлях не потрібен, бо це той самий рівень
from backend.app.src.models.tasks.task import Task
from backend.app.src.models.tasks.completion import TaskCompletion
from backend.app.src.models.auth.user import User
# from backend.app.src.models.groups.group import Group # Не використовується прямо

from backend.app.src.schemas.bonuses.bonus_rule import BonusRuleResponse
from backend.app.src.services.bonuses.bonus_rule import BonusRuleService  # Імпорт сервісу правил
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings  # Для доступу до конфігурацій

# TODO: Винести COMPLETION_STATUS_APPROVED до спільного файлу констант/енумів, якщо він використовується в інших місцях.
COMPLETION_STATUS_APPROVED = "APPROVED"  # Статус для перевірки успішного виконання завдання


class BonusCalculationService(BaseService):
    """
    Сервіс, відповідальний за розрахунок бонусних балів на основі визначених правил та контексту подій.
    Може обробляти прості правила з фіксованими балами або складнішу, умовну логіку.
    Зазвичай викликається іншими сервісами (наприклад, TaskCompletionService), коли відбувається подія,
    що потенційно може активувати нарахування бонусу.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("BonusCalculationService ініціалізовано.")

    async def calculate_bonus_for_task_completion(
            self,
            task: Task,
            user: User,
            task_completion: TaskCompletion
    ) -> Tuple[Optional[Decimal], Optional[UUID]]:  # Повертає суму бонусу та ID застосованого правила
        """
        Розраховує бонус за виконання завдання.

        Згідно з `technical_task.txt`:
        - Оцінює всі застосовні правила, умови яких виконані.
        - Обирає найкраще правило:
            1. Найвища кількість балів (`points_amount`).
            2. Якщо бали однакові, обирається найбільш специфічне правило (Task > TaskType > Group > Global).
               (Сервіс `BonusRuleService.get_applicable_bonus_rules` вже повертає правила в порядку специфічності).
            3. Якщо все ще нічия, обирається правило, створене останнім (`created_at` desc).

        :param task: Об'єкт виконаного завдання.
        :param user: Об'єкт користувача, що виконав завдання.
        :param task_completion: Об'єкт завершення завдання.
        :return: Кортеж (сума бонусу, ID застосованого правила) або (None, None), якщо бонус не нараховано.
        """
        logger.info(f"Розрахунок бонусу за виконання завдання ID '{task.id}' користувачем ID '{user.id}'.")

        if task_completion.status != COMPLETION_STATUS_APPROVED:
            logger.info(
                f"Завдання ID '{task.id}' не має статусу '{COMPLETION_STATUS_APPROVED}'. Бонус не нараховується.")
            return None, None

        if not task.group_id:
            # TODO: Уточнити в technical_task.txt, як обробляти завдання без групи.
            # Поки що логуємо попередження, але дозволяємо застосування глобальних правил.
            logger.warning(
                f"Завдання ID '{task.id}' не має контексту групи. Можуть бути застосовані лише глобальні правила, не специфічні для групи.")

        bonus_rule_service = BonusRuleService(self.db_session)
        # get_applicable_bonus_rules вже сортує за специфічністю
        applicable_rules_schemas: List[BonusRuleResponse] = await bonus_rule_service.get_applicable_bonus_rules(
            group_id=task.group_id,  # Може бути None, якщо завдання не в групі
            task_id=task.id,
            task_type_id=task.task_type_id
        )

        if not applicable_rules_schemas:
            logger.info(f"Не знайдено застосовних правил для завдання ID '{task.id}'. Бонус не нараховано.")
            return None, None

        candidate_rules: List[BonusRuleResponse] = []
        for rule_schema in applicable_rules_schemas:
            logger.debug(
                f"Оцінка правила ID '{rule_schema.id}' (Ім'я: '{rule_schema.name}', Бали: {rule_schema.points_amount})")
            if rule_schema.points_amount is None or rule_schema.points_amount == Decimal(
                    "0"):  # Правила без балів або з нульовими балами не розглядаються
                logger.debug(f"Правило ID '{rule_schema.id}' пропущено: немає балів або бали нульові.")
                continue

            if await self._check_rule_conditions(rule_schema, task, user, task_completion):
                candidate_rules.append(rule_schema)
            else:
                logger.debug(f"Умови для правила ID '{rule_schema.id}' не виконані.")

        if not candidate_rules:
            logger.info(f"Жодне правило не пройшло перевірку умов для завдання ID '{task.id}'.")
            return None, None

        # Сортування кандидатів: 1. points_amount (desc), 2. created_at (desc)
        # Специфічність вже врахована порядком з get_applicable_bonus_rules.
        # Якщо два правила з однаковою специфічністю і балами, беремо новіше.
        candidate_rules.sort(key=lambda r: (r.points_amount, r.created_at), reverse=True)

        best_rule = candidate_rules[0]
        final_bonus_amount = Decimal(str(best_rule.points_amount))

        logger.info(f"Застосовано правило '{best_rule.name}' (ID: {best_rule.id}): {final_bonus_amount} балів.")
        return final_bonus_amount, best_rule.id

    async def _check_rule_conditions(
            self,
            rule: BonusRuleResponse,
            task: Task,
            user: User,
            task_completion: TaskCompletion
    ) -> bool:
        """
        Перевіряє виконання умов конкретного правила.

        :param rule: Pydantic схема правила для перевірки.
        :param task: Об'єкт завдання.
        :param user: Об'єкт користувача.
        :param task_completion: Об'єкт завершення завдання.
        :return: True, якщо умови виконані, інакше False.
        """
        logger.debug(f"Перевірка умов для правила '{rule.name}' (ID: {rule.id}), тип умови: {rule.condition_type}")

        # Базова перевірка: завдання має бути ухвалене
        if task_completion.status != COMPLETION_STATUS_APPROVED:
            return False  # Умова не виконана, якщо завдання не ухвалене

        condition_type = rule.condition_type
        config = rule.condition_config if rule.condition_config else {}  # Забезпечуємо наявність dict

        if condition_type == "DEFAULT":
            logger.debug(f"Умова 'DEFAULT' для правила '{rule.name}' завжди виконана.")
            return True

        elif condition_type == "TASK_COMPLETED_ON_TIME":
            if task.due_date and task_completion.completed_at:
                if task_completion.completed_at <= task.due_date:
                    logger.debug(f"Умова 'TASK_COMPLETED_ON_TIME' для правила '{rule.name}' виконана.")
                    return True
            logger.debug(
                f"Умова 'TASK_COMPLETED_ON_TIME' для правила '{rule.name}' не виконана (немає due_date, completed_at або виконано із запізненням).")
            return False

        elif condition_type == "TASK_COMPLETED_EARLY":
            min_hours_early = Decimal(str(config.get("min_hours_early", 0)))
            if task.due_date and task_completion.completed_at and min_hours_early > 0:
                required_completion_time = task.due_date - timedelta(hours=float(min_hours_early))
                if task_completion.completed_at <= required_completion_time:
                    logger.debug(
                        f"Умова 'TASK_COMPLETED_EARLY' (мін. {min_hours_early} год.) для правила '{rule.name}' виконана.")
                    return True
            logger.debug(
                f"Умова 'TASK_COMPLETED_EARLY' для '{rule.name}' не виконана (не відповідає критеріям дострокового виконання).")
            return False

        elif condition_type == "USER_FIRST_TASK_COMPLETION":
            stmt = select(func.count(TaskCompletion.id)).where(
                TaskCompletion.user_id == user.id,
                TaskCompletion.status == COMPLETION_STATUS_APPROVED,
                TaskCompletion.id != task_completion.id  # Не рахувати поточне виконання
            )
            prior_completions_count = (await self.db_session.execute(stmt)).scalar_one()
            if prior_completions_count == 0:
                logger.debug(f"Умова 'USER_FIRST_TASK_COMPLETION' для правила '{rule.name}' виконана.")
                return True
            logger.debug(
                f"Умова 'USER_FIRST_TASK_COMPLETION' для '{rule.name}' не виконана (є {prior_completions_count} попередніх виконань).")
            return False

        elif condition_type == "USER_FIRST_SPECIFIC_TASK_COMPLETION":
            stmt = select(func.count(TaskCompletion.id)).where(
                TaskCompletion.user_id == user.id,
                TaskCompletion.task_id == task.id,
                TaskCompletion.status == COMPLETION_STATUS_APPROVED,
                TaskCompletion.id != task_completion.id  # Не рахувати поточне виконання
            )
            prior_specific_completions_count = (await self.db_session.execute(stmt)).scalar_one()
            if prior_specific_completions_count == 0:
                logger.debug(f"Умова 'USER_FIRST_SPECIFIC_TASK_COMPLETION' для правила '{rule.name}' виконана.")
                return True
            logger.debug(
                f"Умова 'USER_FIRST_SPECIFIC_TASK_COMPLETION' для '{rule.name}' не виконана (є {prior_specific_completions_count} попередніх виконань цього завдання).")
            return False

        # TODO: Реалізувати інші типи умов з `technical_task.txt` (наприклад, `COMPLETION_STREAK`, якщо він обробляється тут).
        # elif condition_type == "COMPLETION_STREAK":
        #     # Потребує більш складної логіки, можливо, окремого сервісу або даних про історію активності.
        #     logger.warning(f"Умова 'COMPLETION_STREAK' для правила '{rule.name}' ще не реалізована.")
        #     return False

        else:
            logger.warning(
                f"Невідомий тип умови '{condition_type}' для правила '{rule.name}'. Умова вважається невиконаною.")
            return False


logger.debug("BonusCalculationService клас визначено та завантажено.")
