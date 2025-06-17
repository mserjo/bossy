# backend/app/src/schemas/bonuses/bonus_rule.py
"""
Pydantic схеми для сутності "Правило Нарахування Бонусів" (BonusRule).

Цей модуль визначає схеми для:
- Базового представлення правила нарахування бонусів (`BonusRuleBaseSchema`).
- Створення нового правила (`BonusRuleCreateSchema`).
- Оновлення існуючого правила (`BonusRuleUpdateSchema`).
- Представлення даних про правило у відповідях API (`BonusRuleSchema`).
"""
from datetime import datetime
from typing import Optional, Any  # Any для тимчасових полів
from decimal import Decimal

from pydantic import Field

# Абсолютний імпорт базових схем та міксинів
from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin, TimestampedSchemaMixin
from backend.app.src.config.logging import get_logger # Новий імпорт логера
from backend.app.src.core.i18n import _ # Added import
logger = get_logger(__name__)

# Оскільки BonusRule модель успадковує NameDescriptionMixin, StateMixin, їх поля теж мають бути тут.

# Імпорти для конкретних схем
from backend.app.src.schemas.dictionaries.bonus_types import BonusTypeResponseSchema
from backend.app.src.schemas.tasks.task import TaskSchema # Використовуємо TaskSchema як є
from backend.app.src.schemas.tasks.event import EventResponseSchema


# Placeholder assignments removed (BonusTypeSchema = Any, TaskSchema = Any)


class BonusRuleBaseSchema(BaseSchema):
    """
    Базова схема для полів правила нарахування бонусів.
    Включає поля, спільні для створення та оновлення правил.
    """
    name: str = Field(
        ...,
        max_length=255,
        description=_("bonus_rule.fields.name.description"),
        examples=["Бонус за щоденний вхід", "Штраф за прострочене завдання"]
    )
    description: Optional[str] = Field(
        None,
        description=_("bonus_rule.fields.description.description")
    )
    task_id: Optional[int] = Field(None, description=_("bonus_rule.fields.task_id.description"))
    event_id: Optional[int] = Field(None, description=_("bonus_rule.fields.event_id.description"))
    bonus_type_code: str = Field(
        description=_("bonus_rule.fields.bonus_type_code.description")
    )
    amount: Decimal = Field(
        description=_("bonus_rule.fields.amount.description")
    )
    condition_description: Optional[str] = Field(
        None,
        description=_("bonus_rule.fields.condition_description.description")
    )
    state: Optional[str] = Field(
        None,
        max_length=50,
        description=_("bonus_rule.fields.state.description"),
        examples=["active"]
    )
    # model_config успадковується з BaseSchema (from_attributes=True)


class BonusRuleCreateSchema(BonusRuleBaseSchema):
    """
    Схема для створення нового правила нарахування бонусів.
    Успадковує всі поля від `BonusRuleBaseSchema`.
    """
    # Можна додати поля, специфічні лише для створення, якщо такі є.
    pass


class BonusRuleUpdateSchema(BonusRuleBaseSchema):
    """
    Схема для оновлення існуючого правила нарахування бонусів.
    Всі поля, успадковані з `BonusRuleBaseSchema`, стають опціональними.
    """
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    task_id: Optional[int] = None
    event_id: Optional[int] = None
    bonus_type_code: Optional[str] = None
    amount: Optional[Decimal] = None
    condition_description: Optional[str] = None
    state: Optional[str] = Field(None, max_length=50)


class BonusRuleResponseSchema(BonusRuleBaseSchema, IDSchemaMixin, TimestampedSchemaMixin): # Renamed
    """
    Схема для представлення даних про правило нарахування бонусів у відповідях API.
    Включає `id`, часові мітки та розширену інформацію про пов'язані об'єкти.
    """
    # id, created_at, updated_at успадковані з міксинів.
    # name, description, task_id, event_id, bonus_type_code, amount, condition_description, state
    # успадковані з BonusRuleBaseSchema.

    bonus_type: Optional[BonusTypeResponseSchema] = Field(None, description=_("bonus_rule.response.fields.bonus_type.description"))
    task: Optional[TaskSchema] = Field(None, description=_("bonus_rule.response.fields.task.description"))
    event: Optional[EventResponseSchema] = Field(None, description=_("bonus_rule.response.fields.event.description"))

    # Можна додати обчислювані або додатково завантажені поля, наприклад:
    # task_name: Optional[str] = Field(None, description="Назва пов'язаного завдання (якщо є).")


if __name__ == "__main__":
    # Демонстраційний блок для схем правил нарахування бонусів.
    logger.info("--- Pydantic Схеми для Правил Нарахування Бонусів (BonusRule) ---")

    logger.info("\nBonusRuleBaseSchema (приклад):")
    base_rule_data = {
        "name": "Щоденний бонус за вхід",  # TODO i18n
        "bonus_type_code": "DAILY_LOGIN_REWARD",
        "amount": Decimal("5.00"),
        "state": "active"
    }
    base_rule_instance = BonusRuleBaseSchema(**base_rule_data)
    logger.info(base_rule_instance.model_dump_json(indent=2))

    logger.info("\nBonusRuleCreateSchema (приклад для створення):")
    create_rule_data = {
        "name": "Бонус за реєстрацію друга",  # TODO i18n
        "description": "Нараховується користувачу, який запросив друга, після реєстрації друга.",  # TODO i18n
        "bonus_type_code": "REFERRAL_BONUS",
        "amount": Decimal("50.00"),
        "state": "active"
    }
    create_rule_instance = BonusRuleCreateSchema(**create_rule_data)
    logger.info(create_rule_instance.model_dump_json(indent=2))

    logger.info("\nBonusRuleUpdateSchema (приклад для оновлення):")
    update_rule_data = {"amount": Decimal("60.00"), "description": "Збільшений бонус за реєстрацію друга."}  # TODO i18n
    update_rule_instance = BonusRuleUpdateSchema(**update_rule_data)
    logger.info(update_rule_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nBonusRuleSchema (приклад відповіді API):")
    rule_response_data = {
        "id": 1,
        "name": "Бонус за виконання завдання 'Титан'",  # TODO i18n
        "bonus_type_code": "TASK_COMPLETION_BONUS",
        "amount": Decimal("100.00"),
        "task_id": 123,
        "state": "active",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        # Приклади для пов'язаних об'єктів (закоментовано, бо потребують повних даних схем)
        # "bonus_type": {"id": 1, "name": "Нагорода", "code": "REWARD",
        #                "description": "Базовий тип нагороди", "created_at": str(datetime.now()), "updated_at": str(datetime.now())},
        # "task": {"id": 123, "name": "Завдання 'Титан'", "task_type_code": "GENERAL",
        #          "status_code": "ACTIVE", "created_at": str(datetime.now()), "updated_at": str(datetime.now())},
        # "event": {"id": 789, "name": "Подія 'Весняний Збір'", "event_type_code": "SEASONAL",
        #           "status_code": "UPCOMING", "start_time": str(datetime.now()), "end_time": str(datetime.now() + timedelta(days=1))}
    }
    rule_response_instance = BonusRuleResponseSchema(**rule_response_data)
    logger.info(rule_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Схеми для пов'язаних об'єктів тепер імпортовані (BonusTypeResponseSchema, TaskSchema, EventResponseSchema).")
    logger.info("Приклади даних для цих полів у `rule_response_data` закоментовані, оскільки потребують повної структури відповідних схем.")
    logger.info("Також, `bonus_type_code` потребує валідації на рівні сервісу або схеми.")
    logger.info("Уточнення щодо `event_id` та його зв'язку з `task_id` залишається актуальним (TODO).")
