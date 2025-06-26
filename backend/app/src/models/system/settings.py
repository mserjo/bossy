# backend/app/src/models/system/settings.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `SystemSettingsModel` для зберігання глобальних налаштувань системи.
Ці налаштування можуть керувати різними аспектами поведінки всієї системи,
наприклад, налаштування логування, параметри безпеки за замовчуванням, налаштування інтеграцій тощо.
Доступ до цих налаштувань зазвичай має лише супер-адміністратор.
"""

from sqlalchemy import Column, String, Text, JSON, Boolean # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
import uuid # Для роботи з UUID

from backend.app.src.models.base import BaseModel # Імпорт базової моделі

# TODO: Визначити, чи потрібен `BaseMainModel` чи достатньо `BaseModel`.
# Системні налаштування зазвичай не мають "назви" чи "опису" в тому ж сенсі,
# що й інші сутності. Вони скоріше є парами ключ-значення.
# Поки що використовуємо BaseModel, оскільки поля name, description, group_id, state_id з BaseMainModel
# тут можуть бути недоречними. Якщо кожне налаштування - окремий запис, то name/code можуть бути корисними.
# Якщо всі налаштування в одному JSON-об'єкті, то модель буде іншою.

# Варіант 1: Кожне налаштування - окремий запис в таблиці.
# Це більш гнучко для додавання нових налаштувань, валідації типів, аудиту.
class SystemSettingModel(BaseModel): # успадковуємо від BaseModel, а не BaseMainModel
    """
    Модель для зберігання окремих системних налаштувань у форматі ключ-значення.

    Кожен запис представляє одне конкретне налаштування системи.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор запису налаштування (успадковано).
        key (str): Унікальний ключ налаштування (наприклад, "log_level", "maintenance_mode").
        value (Text): Значення налаштування, збережене як текст. Може потребувати перетворення типу при читанні/записі.
                      Для складних значень (JSON, числа, булеві) потрібна логіка в сервісному шарі.
        value_type (str): Тип значення ('string', 'integer', 'boolean', 'json') для допомоги в інтерпретації.
        description (str | None): Опис призначення цього налаштування.
        is_editable (bool): Чи може це налаштування редагуватися через UI (деякі можуть бути лише системними).
        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення запису (успадковано).
    """
    __tablename__ = "system_settings"

    # Унікальний ключ для ідентифікації налаштування. Наприклад: "maintenance_mode", "default_language".
    # Повинен бути унікальним.
    key: Column[str] = Column(String(255), nullable=False, unique=True, index=True)

    # Значення налаштування. Зберігається як текстове поле.
    # Для складних типів (JSON, списки) сервісний шар відповідатиме за серіалізацію/десеріалізацію.
    value: Column[str] = Column(Text, nullable=True) # Може бути nullable, якщо значення за замовчуванням береться з коду

    # Тип значення, що зберігається в полі `value`.
    # Наприклад: 'string', 'integer', 'float', 'boolean', 'json', 'list_string'.
    # Допомагає правильно інтерпретувати та валідувати значення на сервісному рівні.
    value_type: Column[str] = Column(String(50), nullable=False, default='string')

    # Опис того, що це за налаштування та на що воно впливає.
    description: Column[str | None] = Column(Text, nullable=True)

    # Чи може це налаштування бути змінене користувачем (суперадміном) через інтерфейс.
    # Деякі налаштування можуть бути суто внутрішніми або керованими лише через конфігураційні файли.
    is_editable: Column[bool] = Column(Boolean, default=True, nullable=False)

    # TODO: Додати поле `category` або `group_key` для групування налаштувань в UI.
    # category: Column[str] = Column(String(100), nullable=True, index=True)

    # TODO: Подумати про механізм кешування цих налаштувань, оскільки вони можуть часто читатися.

    category: Column[str | None] = Column(String(100), nullable=True, index=True, comment="Категорія для групування налаштувань в UI")

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі SystemSettingModel.
        Наприклад: <SystemSettingModel(key='maintenance_mode', value='false')>
        """
        return f"<{self.__class__.__name__}(key='{self.key}', value='{self.value}')>"

# Варіант 2: Всі налаштування зберігаються в одному записі (наприклад, в JSON полі).
# Цей варіант менш гнучкий для аудиту окремих змін, але може бути простішим, якщо налаштувань небагато.
# З огляду на структуру інших частин системи (деталізовані моделі), Варіант 1 виглядає більш відповідним.
# Якщо все ж таки потрібен Варіант 2:
# class SystemSettingsObjectModel(BaseModel):
#     __tablename__ = "system_settings_object" # Інша назва таблиці
#
#     # Одне поле для зберігання всіх налаштувань у форматі JSON.
#     # `id` буде фіксованим (наприклад, завжди один запис).
#     settings_data: Column[dict] = Column(JSON, nullable=False, default=lambda: {})
#
#     def __repr__(self) -> str:
#         return f"<{self.__class__.__name__}(id='{self.id}')>"

# Зупиняємося на Варіанті 1 (SystemSettingModel) для більшої гнучкості та деталізації.

# Приклади системних налаштувань, які можуть зберігатися:
# - `site_name`: "Bossy" (string)
# - `default_language`: "uk" (string)
# - `maintenance_mode`: "false" (boolean)
# - `new_user_registration_open`: "true" (boolean)
# - `max_failed_login_attempts`: "5" (integer)
# - `jwt_token_lifetime_seconds`: "3600" (integer)
# - `email_notifications_enabled`: "true" (boolean)
# - `cron_last_run_monitoring`: "2023-01-01T10:00:00Z" (datetime string, хоча це краще в окремій таблиці моніторингу)

# TODO: Переконатися, що назва таблиці `system_settings` відповідає `structure-claude-v3.md`.
# У `structure-claude-v3.md` вказано `backend/app/src/models/system/settings.py` для моделі,
# що відповідає `SystemSettingsModel`. Назва таблиці `system_settings` є логічною.

# TODO: Розглянути, чи потрібні `state_id` або `group_id` для системних налаштувань.
# `group_id` точно не потрібен, оскільки це глобальні налаштування.
# `state_id` (активне/неактивне налаштування) може бути корисним, якщо деякі налаштування
# можна тимчасово вимикати, не видаляючи їх, але це можна контролювати і значенням `is_editable`
# або специфічним значенням самого налаштування (наприклад, `maintenance_mode` = true/false).
# Поки що `BaseModel` не має цих полів, що є доречним для цієї моделі.
# Якщо б успадковувались від `BaseMainModel`, ці поля були б зайвими.
# Поле `is_deleted` з `BaseMainModel` (якщо б використовували його) тут теж не дуже доречне,
# оскільки налаштування або існують, або ні (або мають значення за замовчуванням з коду).
# `BaseModel` (id, created_at, updated_at) є достатнім базисом.
# Додаткові поля `key`, `value`, `value_type`, `description`, `is_editable` специфічні для цієї моделі.
