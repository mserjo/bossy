# backend/app/src/models/system/settings.py
"""
Модель SQLAlchemy для сутності "Системне Налаштування" (SystemSetting).

Цей модуль визначає модель `SystemSetting`, яка використовується для зберігання
різноманітних налаштувань програми, що керуються на рівні системи
(зазвичай суперкористувачем).
"""
from typing import Optional, Dict, Any

from sqlalchemy import String, Text, Boolean, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

# Абсолютний імпорт базових класів та міксинів
from backend.app.src.models.base import Base  # Системні налаштування можуть не мати всіх полів BaseMainModel
from backend.app.src.models.mixins import TimestampedMixin, NameDescriptionMixin  # Name/Description можуть бути корисні
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)


# TODO: Визначити Enum SettingValueType в core.dicts.py, наприклад:
# class SettingValueType(str, Enum):
#     STRING = "string"
#     INTEGER = "integer"
#     FLOAT = "float"
#     BOOLEAN = "boolean"
#     JSON = "json"
#     LIST_STR = "list_str" # Список рядків, може зберігатися як JSON або розділений рядок
# Потім імпортувати: from backend.app.src.core.dicts import SettingValueType

class SystemSetting(Base, TimestampedMixin, NameDescriptionMixin):
    """
    Модель Системного Налаштування.

    Зберігає пари ключ-значення для системних налаштувань.
    Поля `name` та `description` з `NameDescriptionMixin` можуть використовуватися
    для людиночитаної назви та опису налаштування. `name` тут буде унікальним ключем.

    Атрибути:
        id (Mapped[int]): Унікальний ідентифікатор запису налаштування.
        key (Mapped[str]): Унікальний ключ налаштування (програмний ідентифікатор).
                           Успадковане поле `name` з NameDescriptionMixin може бути використане як `key`,
                           або можна визначити окреме поле `key` і використовувати `name` для UI.
                           Поточна реалізація використовує `key`.
        value (Mapped[Optional[str]]): Значення налаштування, збережене як текст.
                                        Може потребувати перетворення залежно від `value_type`.
        description (Mapped[Optional[str]]): Опис налаштування (успадковано).
        value_type (Mapped[str]): Тип значення ('string', 'integer', 'boolean', 'json', 'list_str').
                                  TODO: Використовувати Enum `SettingValueType`.
        is_editable (Mapped[bool]): Чи може суперкористувач редагувати це налаштування через UI/API.
        is_sensitive (Mapped[bool]): Чи є значення налаштування чутливим (наприклад, API ключ),
                                     що вимагає маскування у UI/логах.
        created_at, updated_at: Успадковано.
    """
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True, comment="Унікальний ідентифікатор налаштування"
    )

    # Використовуємо окреме поле 'key' для програмного доступу,
    # 'name' з NameDescriptionMixin - для UI.
    key: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False, comment="Унікальний програмний ключ налаштування"
    )

    # Значення зберігається як текст; value_type визначає, як його інтерпретувати.
    # Для JSON або складних типів може знадобитися тип JSON в БД.
    value: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Значення налаштування (як текст або JSON-рядок)"
    )

    # value_type: Mapped[SettingValueType] = mapped_column(SQLEnum(SettingValueType), default=SettingValueType.STRING, nullable=False)
    value_type: Mapped[str] = mapped_column(
        String(50), default='string', nullable=False, comment="Тип значення (string, integer, boolean, json)"
    )  # TODO: Замінити на Enum SettingValueType

    is_editable: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Чи можна редагувати через UI/API суперкористувачем"
    )
    is_sensitive: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Чи є значення чутливим (маскувати у UI/логах)"
    )

    # `name` та `description` успадковані з NameDescriptionMixin.
    # `name` буде використовуватися як людиночитана назва налаштування.
    # `description` - для детального опису призначення налаштування.

    # Поля для __repr__
    # `created_at`, `updated_at`, `name` успадковуються.
    _repr_fields = ["id", "key", "value_type", "is_editable"]


if __name__ == "__main__":
    # Демонстраційний блок для моделі SystemSetting.
    logger.info("--- Модель Системного Налаштування (SystemSetting) ---")
    logger.info(f"Назва таблиці: {SystemSetting.__tablename__}")

    logger.info("\nОчікувані поля:")
    expected_fields = [
        'id', 'name', 'description',  # З NameDescriptionMixin (name тут буде ключем)
        'created_at', 'updated_at',  # З TimestampedMixin
        'key', 'value', 'value_type', 'is_editable', 'is_sensitive'
    ]
    # BaseMainModel не успадковується, тому state, group_id, notes, deleted_at тут не буде.
    for field in expected_fields:
        logger.info(f"  - {field}")

    # Приклад створення екземпляра (без взаємодії з БД)
    from datetime import datetime, timezone

    example_setting = SystemSetting(
        id=1,
        key="site_maintenance_mode",
        name="Режим обслуговування сайту",  # TODO i18n
        description="Вмикає або вимикає режим обслуговування для всього сайту.",  # TODO i18n
        value="false",
        value_type="boolean",  # TODO: Замінити на SettingValueType.BOOLEAN.value
        is_editable=True,
        is_sensitive=False
    )
    example_setting.created_at = datetime.now(tz=timezone.utc)

    logger.info(f"\nПриклад екземпляра SystemSetting (без сесії):\n  {example_setting}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <SystemSetting(id=1, name='Режим обслуговування сайту', key='site_maintenance_mode', value_type='boolean', is_editable=True, created_at=...)>

    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
    logger.info("TODO: Не забудьте визначити Enum 'SettingValueType' в core.dicts.py та оновити поле 'value_type'.")
