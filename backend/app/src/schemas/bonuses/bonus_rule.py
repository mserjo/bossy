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

# Оскільки BonusRule модель успадковує NameDescriptionMixin, StateMixin, їх поля теж мають бути тут.

# TODO: Замінити Any на конкретні схеми, коли вони будуть доступні/рефакторені.
# from backend.app.src.schemas.dictionaries.bonus_types import BonusTypeSchema
# from backend.app.src.schemas.tasks.task import TaskSchema # Або TaskBriefSchema
BonusTypeSchema = Any  # Тимчасовий заповнювач
TaskSchema = Any  # Тимчасовий заповнювач


class BonusRuleBaseSchema(BaseSchema):
    """
    Базова схема для полів правила нарахування бонусів.
    Включає поля, спільні для створення та оновлення правил.
    """
    name: str = Field(
        ...,
        max_length=255,  # Відповідає типовій довжині для назв
        description="Назва правила нарахування бонусів.",
        examples=["Бонус за щоденний вхід", "Штраф за прострочене завдання"]
    )
    description: Optional[str] = Field(
        None,
        description="Детальний опис правила та умов його спрацювання."
    )
    # TODO: Уточнити зв'язок event_id, якщо події є типом завдань.
    #       Можливо, буде лише task_id, а тип завдання визначить, чи це подія.
    task_id: Optional[int] = Field(None, description="ID завдання, до якого прив'язане правило (якщо є).")
    event_id: Optional[int] = Field(None,
                                    description="ID події (завдання типу 'event'), до якої прив'язане правило (якщо є).")

    # TODO: Валідувати bonus_type_code на основі існуючих кодів в довіднику dict_bonus_types
    bonus_type_code: str = Field(
        description="Код типу бонусу з довідника (наприклад, 'REWARD', 'PENALTY')."
    )
    amount: Decimal = Field(
        # ge=0, # Дозволяємо від'ємні значення, якщо bonus_type_code не завжди однозначно визначає напрямок (наприклад, "ADJUSTMENT")
        # Або ж amount завжди позитивний, а bonus_type_code ('REWARD'/'PENALTY') визначає операцію.
        # Для прикладу, припускаємо, що amount може бути від'ємним для штрафів, якщо bonus_type_code це дозволяє.
        description="Сума бонусу або штрафу. Позитивна для нарахування, від'ємна для списання (або залежить від bonus_type_code)."
    )
    condition_description: Optional[str] = Field(
        None,
        description="Текстовий опис додаткових умов спрацювання правила."
    )
    # TODO: Розглянути використання Enum RuleState з core.dicts, якщо стани правил фіксовані.
    state: Optional[str] = Field(
        None,  # Або default="active"
        max_length=50,
        description="Стан правила (наприклад, 'active', 'inactive', 'draft').",
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


class BonusRuleSchema(BonusRuleBaseSchema, IDSchemaMixin, TimestampedSchemaMixin):
    """
    Схема для представлення даних про правило нарахування бонусів у відповідях API.
    Включає `id`, часові мітки та розширену інформацію про пов'язані об'єкти.
    """
    # id, created_at, updated_at успадковані з міксинів.
    # name, description, task_id, event_id, bonus_type_code, amount, condition_description, state
    # успадковані з BonusRuleBaseSchema.

    # TODO: Замінити Any на відповідні схеми.
    bonus_type: Optional[BonusTypeSchema] = Field(None, description="Об'єкт типу бонусу.")
    task: Optional[TaskSchema] = Field(None, description="Об'єкт пов'язаного завдання (коротка інформація).")
    event_task: Optional[TaskSchema] = Field(None,
                                             description="Об'єкт пов'язаної події (якщо event_id використовується окремо).")

    # Можна додати обчислювані або додатково завантажені поля, наприклад:
    # task_name: Optional[str] = Field(None, description="Назва пов'язаного завдання (якщо є).")


if __name__ == "__main__":
    # Демонстраційний блок для схем правил нарахування бонусів.
    print("--- Pydantic Схеми для Правил Нарахування Бонусів (BonusRule) ---")

    print("\nBonusRuleBaseSchema (приклад):")
    base_rule_data = {
        "name": "Щоденний бонус за вхід",  # TODO i18n
        "bonus_type_code": "DAILY_LOGIN_REWARD",
        "amount": Decimal("5.00"),
        "state": "active"
    }
    base_rule_instance = BonusRuleBaseSchema(**base_rule_data)
    print(base_rule_instance.model_dump_json(indent=2))

    print("\nBonusRuleCreateSchema (приклад для створення):")
    create_rule_data = {
        "name": "Бонус за реєстрацію друга",  # TODO i18n
        "description": "Нараховується користувачу, який запросив друга, після реєстрації друга.",  # TODO i18n
        "bonus_type_code": "REFERRAL_BONUS",
        "amount": Decimal("50.00"),
        "state": "active"
    }
    create_rule_instance = BonusRuleCreateSchema(**create_rule_data)
    print(create_rule_instance.model_dump_json(indent=2))

    print("\nBonusRuleUpdateSchema (приклад для оновлення):")
    update_rule_data = {"amount": Decimal("60.00"), "description": "Збільшений бонус за реєстрацію друга."}  # TODO i18n
    update_rule_instance = BonusRuleUpdateSchema(**update_rule_data)
    print(update_rule_instance.model_dump_json(indent=2, exclude_none=True))

    print("\nBonusRuleSchema (приклад відповіді API):")
    rule_response_data = {
        "id": 1,
        "name": "Бонус за виконання завдання 'Титан'",  # TODO i18n
        "bonus_type_code": "TASK_COMPLETION_BONUS",
        "amount": Decimal("100.00"),
        "task_id": 123,
        "state": "active",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        # "bonus_type": {"id": 1, "name": "Нагорода", "code": "REWARD"}, # Приклад BonusTypeSchema
        # "task": {"id": 123, "name": "Завдання 'Титан'"} # Приклад TaskSchema (коротка версія)
    }
    rule_response_instance = BonusRuleSchema(**rule_response_data)
    print(rule_response_instance.model_dump_json(indent=2, exclude_none=True))

    print("\nПримітка: Схеми для пов'язаних об'єктів (BonusTypeSchema, TaskSchema) наразі є заповнювачами (Any).")
    print("Їх потрібно буде імпортувати після їх рефакторингу/визначення.")
    print("Також, `bonus_type_code` потребує валідації на рівні сервісу або схеми.")
    print("Уточнення щодо `event_id` та його зв'язку з `task_id` залишається актуальним (TODO).")
