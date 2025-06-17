# backend/app/src/schemas/system/settings.py
"""
Pydantic схеми для сутності "Системне Налаштування" (SystemSetting).

Цей модуль визначає схеми для:
- Базового представлення системного налаштування (`SystemSettingBaseSchema`).
- Створення нового системного налаштування (`SystemSettingCreateSchema`).
- Оновлення значення існуючого системного налаштування (`SystemSettingUpdateSchema`).
- Представлення даних про системне налаштування у відповідях API (`SystemSettingSchema`).
"""
from datetime import datetime  # Для TimestampedSchemaMixin
from typing import Optional, Any, Dict

from pydantic import Field

# Абсолютний імпорт базових схем та міксинів
from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin, TimestampedSchemaMixin
from backend.app.src.core.dicts import SettingValueType # Імпортовано Enum
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# SettingValueType Enum імпортовано вище.


SETTING_KEY_MAX_LENGTH = 255
SETTING_NAME_MAX_LENGTH = 255
# SETTING_VALUE_TYPE_MAX_LENGTH = 50 # Не потрібен для Enum


class SystemSettingBaseSchema(BaseSchema):
    """
    Базова схема для полів системного налаштування, спільних для створення та оновлення.
    """
    key: str = Field(
        ...,
        max_length=SETTING_KEY_MAX_LENGTH,
        description="Унікальний програмний ключ налаштування.",
        examples=["site_name", "maintenance_mode"]
    )
    name: str = Field(  # Людиночитана назва, з моделі NameDescriptionMixin (non-nullable)
        ...,
        max_length=SETTING_NAME_MAX_LENGTH,
        description="Людиночитана назва налаштування (для відображення в UI).",
        examples=["Назва Сайту", "Режим Обслуговування"]
    )
    description: Optional[str] = Field(
        None,
        description="Детальний опис призначення та використання налаштування."
    )
    # `value` тут не визначаємо, бо в Create воно обов'язкове, а в Update - опціональне.
    # `value_type` також може відрізнятися.

    value_type: SettingValueType = Field(
        default=SettingValueType.STRING,
        description="Тип значення налаштування."
    )
    is_editable: bool = Field(
        default=True,
        description="Чи може суперкористувач редагувати це налаштування через UI/API."
    )
    is_sensitive: bool = Field(
        default=False,
        description="Чи є значення налаштування чутливим (наприклад, API ключ) і потребує маскування."
    )
    # model_config успадковується з BaseSchema (from_attributes=True)


class SystemSettingCreateSchema(SystemSettingBaseSchema):
    """
    Схема для створення нового системного налаштування.
    """
    # Успадковує key, name, description, value_type, is_editable, is_sensitive.
    value: Optional[Any] = Field(None,
                                 description="Значення налаштування. Тип залежить від `value_type` (наприклад, str, int, bool, dict).")


class SystemSettingUpdateSchema(BaseSchema):  # Не успадковує SystemSettingBaseSchema, щоб оновлювати лише value
    """
    Схема для оновлення значення існуючого системного налаштування.
    Зазвичай оновлюється лише поле `value`. Інші поля (key, value_type) є системними.
    Можна дозволити оновлення `name`, `description`, `is_editable`, `is_sensitive` за потреби.
    """
    value: Optional[Any] = Field(None, description="Нове значення налаштування. Тип має відповідати `value_type`.")
    name: Optional[str] = Field(None, max_length=SETTING_NAME_MAX_LENGTH,
                                description="Нова людиночитана назва налаштування.")
    description: Optional[str] = Field(None, description="Новий опис налаштування.")
    is_editable: Optional[bool] = Field(None, description="Новий статус можливості редагування.")
    is_sensitive: Optional[bool] = Field(None, description="Новий статус чутливості значення.")
    # value_type та key зазвичай не змінюються для існуючого налаштування.


class SystemSettingSchema(SystemSettingBaseSchema, IDSchemaMixin, TimestampedSchemaMixin):
    """
    Схема для представлення даних про системне налаштування у відповідях API.
    Успадковує `id`, `created_at`, `updated_at` та поля з `SystemSettingBaseSchema`.
    """
    # id, created_at, updated_at - успадковані.
    # key, name, description, value_type, is_editable, is_sensitive - успадковані.
    value: Optional[Any] = Field(None,
                                 description="Значення налаштування. Увага: чутливі значення можуть бути замасковані або відсутні.")
    # Примітка: Фактичне маскування чутливих значень (`is_sensitive` = True)
    # має відбуватися на рівні сервісу або при формуванні відповіді API,
    # а не в самій схемі Pydantic (схема описує структуру даних).


if __name__ == "__main__":
    # Демонстраційний блок для схем системних налаштувань.
    logger.info("--- Pydantic Схеми для Системних Налаштувань (SystemSetting) ---")

    logger.info("\nSystemSettingCreateSchema (приклад для створення):")
    create_setting_data = {
        "key": "max_users_per_group",
        "name": "Макс. користувачів у групі",  # TODO i18n
        "description": "Максимальна кількість користувачів, яку можна додати до однієї групи.",  # TODO i18n
        "value": "100",  # Значення може бути рядком, потім конвертується відповідно до value_type
        "value_type": SettingValueType.INTEGER, # Використовуємо Enum
        "is_editable": True,
        "is_sensitive": False
    }
    create_setting_instance = SystemSettingCreateSchema(**create_setting_data)
    logger.info(create_setting_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nSystemSettingUpdateSchema (приклад для оновлення значення):")
    update_setting_data = {"value": "150"}
    update_setting_instance = SystemSettingUpdateSchema(**update_setting_data)
    logger.info(update_setting_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nSystemSettingSchema (приклад відповіді API):")
    setting_response_data = {
        "id": 1,
        "key": "api_key_external_service",
        "name": "API Ключ для Зовнішнього Сервісу X",  # TODO i18n
        "value": "********",  # Приклад маскованого значення, якщо is_sensitive=True
        "value_type": SettingValueType.STRING, # Використовуємо Enum
        "is_editable": False,
        "is_sensitive": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    setting_response_instance = SystemSettingSchema(**setting_response_data)
    logger.info(setting_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Ці схеми використовуються для валідації та серіалізації даних системних налаштувань.")
    # logger.info("TODO: Інтегрувати Enum 'SettingValueType' з core.dicts для поля 'value_type' та додати валідацію.") # Вирішено
    logger.info("Маскування чутливих значень (`is_sensitive`) має оброблятися на рівні сервісу/API.")
