# backend/app/src/services/bonuses/calculation.py
# -*- coding: utf-8 -*-
"""
Сервіс для розрахунку бонусів.

Відповідає за обчислення бонусних балів на основі визначених правил
та контексту подій, таких як виконання завдань.
"""
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from datetime import timedelta, datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.src.services.base import BaseService
from backend.app.src.models.bonuses.bonus import BonusRule # Model name was Bonus in previous version, now BonusRule
from backend.app.src.models.tasks.task import Task
from backend.app.src.models.tasks.completion import TaskCompletion
from backend.app.src.models.auth.user import User
# from backend.app.src.models.groups.group import Group # Не використовується прямо

from backend.app.src.schemas.bonuses.bonus_rule import BonusRuleResponse # Schema name was BonusRule in previous version, now BonusRuleResponse
from backend.app.src.services.bonuses.bonus_rule import BonusRuleService # Service name was BonusRule in previous version, now BonusRuleService
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)
# settings видалено, оскільки не використовується
# from backend.app.src.core.constants import TASK_COMPLETION_STATUS_APPROVED # Видалено, будемо використовувати Enum
from backend.app.src.core.dicts import TaskStatus # Імпорт TaskStatus Enum


# TODO: [Constants/Enums] Константа COMPLETION_STATUS_APPROVED замінена на TaskStatus.COMPLETED.value.
#       Перевірити, чи є в TaskStatus Enum більш відповідний член (наприклад, APPROVED).


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
    ) -> Tuple[Optional[Decimal], Optional[int]]:  # ID правила тепер int
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

        # Припускаємо, що TaskStatus.COMPLETED є еквівалентом ухваленого завдання для нарахування бонусу
        if task_completion.status != TaskStatus.COMPLETED:
            logger.info(
                f"Завдання ID '{task.id}' не має статусу '{TaskStatus.COMPLETED.value}'. Бонус не нараховується.")
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
                f"Оцінка правила ID '{rule_schema.id}' (Ім'я: '{rule_schema.name}', Бали: {rule_schema.amount})") # points_amount -> amount
            if rule_schema.amount == Decimal("0"):  # points_amount -> amount, is None видалено
                logger.debug(f"Правило ID '{rule_schema.id}' пропущено: бали нульові.")
                continue

            if await self._check_rule_conditions(rule_schema, task, user, task_completion):
                candidate_rules.append(rule_schema)
            else:
                logger.debug(f"Умови для правила ID '{rule_schema.id}' не виконані.")

        if not candidate_rules:
            logger.info(f"Жодне правило не пройшло перевірку умов для завдання ID '{task.id}'.")
            return None, None

        # Сортування кандидатів: 1. amount (desc), 2. created_at (desc)
        # Специфічність вже врахована порядком з get_applicable_bonus_rules.
        # Якщо два правила з однаковою специфічністю і балами, беремо новіше.
        candidate_rules.sort(key=lambda r: (r.amount, r.created_at), reverse=True) # points_amount -> amount

        best_rule = candidate_rules[0]
        final_bonus_amount = Decimal(str(best_rule.amount)) # points_amount -> amount

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
        # Припускаємо, що TaskStatus.COMPLETED є еквівалентом ухваленого завдання
        if task_completion.status != TaskStatus.COMPLETED:
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
                TaskCompletion.status == TaskStatus.COMPLETED, # Використання Enum
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
                TaskCompletion.status == TaskStatus.COMPLETED, # Використання Enum
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
