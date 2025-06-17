# backend/app/src/schemas/groups/settings.py
"""
Pydantic схеми для сутності "Налаштування Групи" (GroupSetting).

Цей модуль визначає схеми для:
- Базового представлення налаштувань групи (`GroupSettingBaseSchema`).
- Оновлення налаштувань групи (`GroupSettingUpdateSchema`).
- Представлення налаштувань групи у відповідях API (`GroupSettingSchema`).
"""
from datetime import datetime
from typing import Optional
from decimal import Decimal

from pydantic import Field

# Абсолютний імпорт базових схем та міксинів
from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin, TimestampedSchemaMixin
from backend.app.src.config.logging import get_logger 
logger = get_logger(__name__)


class GroupSettingBaseSchema(BaseSchema):
    """
    Базова схема для полів налаштувань групи.
    Визначає налаштування, які можуть бути застосовані до групи.
    """
    # TODO i18n: default value 'бали' for currency_name
    currency_name: str = Field(
        default='бали',
        max_length=50,
        description="Назва внутрішньої валюти/бонусів групи (наприклад, 'бали', 'очки', 'зірочки')."
    )
    allow_decimal_bonuses: bool = Field(
        default=False,
        description="Чи дозволені дробові значення для бонусів у групі."
    )
    max_debt_amount: Optional[Decimal] = Field(
        None,
        # ge=0, # TODO: Вирішити, чи борг має бути >=0, чи може бути від'ємним числом (що представляє ліміт боргу)
        # Якщо це ліміт боргу, то він має бути від'ємним або нульовим, або додатнім для максимального боргу.
        # Краще уточнити логіку. Поки що без обмеження ge=0.
        description="Максимально допустима сума 'боргу' (від'ємного балансу) для учасника. NULL означає відсутність ліміту."
    )
    task_completion_requires_review: bool = Field(
        default=True,
        description="Чи потребує виконання завдання перевірки адміністратором перед нарахуванням бонусів."
    )
    allow_task_reviews: bool = Field(
        default=True,
        description="Чи дозволено користувачам залишати відгуки/рейтинги до завдань у групі."
    )
    allow_gamification_levels: bool = Field(
        default=True,
        description="Чи активна система рівнів гейміфікації в групі."
    )
    allow_gamification_badges: bool = Field(
        default=True,
        description="Чи активна система бейджів/досягнень гейміфікації в групі."
    )
    allow_gamification_ratings: bool = Field(
        default=True,
        description="Чи активна система рейтингів користувачів гейміфікації в групі."
    )
    # model_config успадковується з BaseSchema (from_attributes=True)


class GroupSettingCreateSchema(GroupSettingBaseSchema):
    """
    Схема для створення налаштувань групи.
    `group_id` є обов'язковим при створенні.
    """
    group_id: int = Field(description="Ідентифікатор групи, для якої створюються ці налаштування.")


class GroupSettingUpdateSchema(GroupSettingBaseSchema):
    """
    Схема для оновлення налаштувань групи.
    Всі поля є опціональними, оскільки оновлення може бути частковим.
    """
    currency_name: Optional[str] = Field(None, max_length=50, description="Нова назва валюти бонусів.")
    allow_decimal_bonuses: Optional[bool] = Field(None, description="Нове значення дозволу дробових бонусів.")
    max_debt_amount: Optional[Decimal] = Field(None, description="Нове значення максимального боргу.")
    task_completion_requires_review: Optional[bool] = Field(None, description="Нове значення вимоги перевірки завдань.")
    allow_task_reviews: Optional[bool] = Field(None, description="Нове значення дозволу відгуків на завдання.")
    allow_gamification_levels: Optional[bool] = Field(None, description="Новий статус системи рівнів.")
    allow_gamification_badges: Optional[bool] = Field(None, description="Новий статус системи бейджів.")
    allow_gamification_ratings: Optional[bool] = Field(None, description="Новий статус системи рейтингів.")


class GroupSettingSchema(GroupSettingBaseSchema, IDSchemaMixin, TimestampedSchemaMixin):
    """
    Схема для представлення налаштувань групи у відповідях API.
    Включає `id` групи, до якої належать налаштування, та часові мітки.
    """
    # id, created_at, updated_at успадковані з міксинів.
    # Інші поля успадковані з GroupSettingBaseSchema.
    group_id: int = Field(description="Ідентифікатор групи, до якої належать ці налаштування.")


if __name__ == "__main__":
    # Демонстраційний блок для схем налаштувань групи.
    logger.info("--- Pydantic Схеми для Налаштувань Групи (GroupSetting) ---")

    logger.info("\nGroupSettingBaseSchema (приклад):")
    base_settings_data = {
        "currency_name": "кристали",  # TODO i18n
        "allow_decimal_bonuses": True,
        "max_debt_amount": Decimal("50.00")
    }
    base_settings_instance = GroupSettingBaseSchema(**base_settings_data)
    logger.info(base_settings_instance.model_dump_json(indent=2))

    logger.info("\nGroupSettingUpdateSchema (приклад для оновлення):")
    update_settings_data = {
        "currency_name": "золоті монети",  # TODO i18n
        "allow_task_reviews": False
    }
    update_settings_instance = GroupSettingUpdateSchema(**update_settings_data)
    logger.info(update_settings_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nGroupSettingSchema (приклад відповіді API):")
    setting_response_data = {
        "id": 1,  # ID самого запису налаштувань
        "group_id": 101,  # ID групи
        "currency_name": "бали",  # TODO i18n
        "allow_decimal_bonuses": False,
        "max_debt_amount": None,
        "task_completion_requires_review": True,
        "allow_task_reviews": True,
        "allow_gamification_levels": True,
        "allow_gamification_badges": True,
        "allow_gamification_ratings": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    setting_response_instance = GroupSettingSchema(**setting_response_data)
    logger.info(setting_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Ці схеми використовуються для валідації та серіалізації даних налаштувань групи.")
    logger.info("Поле 'max_debt_amount' може потребувати уточнення логіки (чи може бути від'ємним для позначення ліміту).")
