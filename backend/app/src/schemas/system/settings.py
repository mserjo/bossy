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
from backend.app.src.core.dicts import SettingValueType
from backend.app.src.config.logging import get_logger
from backend.app.src.core.i18n import _
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
        description=_("system.settings.fields.key.description"),
        examples=["site_name", "maintenance_mode"]
    )
    name: str = Field(
        ...,
        max_length=SETTING_NAME_MAX_LENGTH,
        description=_("system.settings.fields.name.description"),
        examples=["Назва Сайту", "Режим Обслуговування"]
    )
    description: Optional[str] = Field(
        None,
        description=_("system.settings.fields.description.description")
    )
    value_type: SettingValueType = Field(
        default=SettingValueType.STRING,
        description=_("system.settings.fields.value_type.description")
    )
    is_editable: bool = Field(
        default=True,
        description=_("system.settings.fields.is_editable.description")
    )
    is_sensitive: bool = Field(
        default=False,
        description=_("system.settings.fields.is_sensitive.description")
    )
    # model_config успадковується з BaseSchema (from_attributes=True)


class SystemSettingCreateSchema(SystemSettingBaseSchema):
    """
    Схема для створення нового системного налаштування.
    """
    # Успадковує key, name, description, value_type, is_editable, is_sensitive.
    value: Optional[Any] = Field(None, description=_("system.settings.create.fields.value.description"))


class SystemSettingUpdateSchema(BaseSchema):
    """
    Схема для оновлення значення існуючого системного налаштування.
    Зазвичай оновлюється лише поле `value`. Інші поля (key, value_type) є системними.
    Можна дозволити оновлення `name`, `description`, `is_editable`, `is_sensitive` за потреби.
    """
    value: Optional[Any] = Field(None, description=_("system.settings.update.fields.value.description"))
    name: Optional[str] = Field(None, max_length=SETTING_NAME_MAX_LENGTH,
                                description=_("system.settings.update.fields.name.description"))
    description: Optional[str] = Field(None, description=_("system.settings.update.fields.description.description"))
    is_editable: Optional[bool] = Field(None, description=_("system.settings.update.fields.is_editable.description"))
    is_sensitive: Optional[bool] = Field(None, description=_("system.settings.update.fields.is_sensitive.description"))
    # value_type та key зазвичай не змінюються для існуючого налаштування.


class SystemSettingResponseSchema(SystemSettingBaseSchema, IDSchemaMixin, TimestampedSchemaMixin):
    """
    Схема для представлення даних про системне налаштування у відповідях API.
    Успадковує `id`, `created_at`, `updated_at` та поля з `SystemSettingBaseSchema`.
    """
    # id, created_at, updated_at - успадковані.
    # key, name, description, value_type, is_editable, is_sensitive - успадковані.
    value: Optional[Any] = Field(None, description=_("system.settings.response.fields.value.description"))
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
